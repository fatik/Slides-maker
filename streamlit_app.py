import streamlit as st
import re
import numpy as np
from sklearn.cluster import KMeans
from transformers import AutoTokenizer, AutoModel, pipeline
import torch

# Load models
@st.cache_resource
def load_models():
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    model = AutoModel.from_pretrained("bert-base-uncased")
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    return tokenizer, model, summarizer

tokenizer, model, summarizer = load_models()

# Define slide layouts
SLIDE_LAYOUTS = {
    "Title": {"elements": ["title"]},
    "Bullet Points": {"elements": ["title", "bullets"]},
    "Big Fact": {"elements": ["fact", "explanation"]},
    "Quote": {"elements": ["quote", "attribution"]},
    "Image Idea": {"elements": ["image_description", "caption"]},
    "Two Columns": {"elements": ["left_column", "right_column"]},
    "Statistic": {"elements": ["number", "context"]}
}

def get_bert_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

def cluster_sentences(sentences, n_clusters=10):
    embeddings = np.array([get_bert_embedding(sent) for sent in sentences])
    kmeans = KMeans(n_clusters=min(n_clusters, len(sentences)), random_state=42)
    return kmeans.fit_predict(embeddings)

def summarize_text(text, max_length=30):
    summary = summarizer(text, max_length=max_length, min_length=10, do_sample=False)[0]['summary_text']
    return summary

def select_layout(content):
    if '"' in content:
        return "Quote"
    elif re.search(r'\d+%|\d+\s*(?:kg|lbs?|tons?)', content):
        return "Statistic"
    elif len(content.split()) > 20:
        return "Bullet Points"
    elif "looks like" in content.lower() or "appears" in content.lower():
        return "Image Idea"
    elif "versus" in content.lower() or "compared to" in content.lower():
        return "Two Columns"
    else:
        return "Big Fact"

def create_slide_content(content, layout):
    if layout == "Title":
        return {"title": summarize_text(content, max_length=10)}
    elif layout == "Bullet Points":
        title = summarize_text(content, max_length=10)
        bullets = [s.strip() for s in content.split('.') if s.strip()]
        return {"title": title, "bullets": bullets[:3]}  # Limit to 3 bullets
    elif layout == "Big Fact":
        parts = content.split(',', 1)
        return {"fact": summarize_text(parts[0], max_length=15), 
                "explanation": summarize_text(parts[1], max_length=20) if len(parts) > 1 else ""}
    elif layout == "Quote":
        match = re.search(r'"([^"]*)"', content)
        quote = match.group(1) if match else content
        attribution = content.split('"')[-1].strip() if match else "Anonymous"
        return {"quote": summarize_text(quote, max_length=20), "attribution": attribution}
    elif layout == "Image Idea":
        parts = content.split(',', 1)
        return {"image_description": summarize_text(parts[0], max_length=15), 
                "caption": summarize_text(parts[1], max_length=20) if len(parts) > 1 else ""}
    elif layout == "Two Columns":
        parts = re.split(r'\sversus\s|\scompared to\s', content, flags=re.IGNORECASE)
        return {"left_column": summarize_text(parts[0], max_length=15), 
                "right_column": summarize_text(parts[1], max_length=15) if len(parts) > 1 else ""}
    elif layout == "Statistic":
        match = re.search(r'(\d+(?:%|\s*(?:kg|lbs?|tons?)))', content)
        if match:
            number = match.group(1)
            context = summarize_text(content.replace(number, '___'), max_length=20)
            return {"number": number, "context": context}
        else:
            return {"number": "N/A", "context": summarize_text(content, max_length=20)}

def render_slide(layout, content):
    slide = f"[Slide: {layout}]\n"
    for key, value in content.items():
        if isinstance(value, list):
            slide += f"{key.capitalize()}:\n"
            for item in value:
                slide += f"- {item}\n"
        else:
            slide += f"{key.capitalize()}: {value}\n"
    return slide

st.title("Advanced NLP-based Slide Generator")

input_text = st.text_area("Enter your script here:", height=200)

if st.button("Generate Slides"):
    if input_text:
        with st.spinner("Analyzing content and generating slides..."):
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', input_text) if s.strip()]
            clusters = cluster_sentences(sentences)
            
            slides = []
            for cluster_id in range(max(clusters) + 1):
                cluster_sentences = [sent for i, sent in enumerate(sentences) if clusters[i] == cluster_id]
                cluster_text = ' '.join(cluster_sentences)
                layout = select_layout(cluster_text)
                content = create_slide_content(cluster_text, layout)
                slides.append((layout, content))
            
            for i, (layout, content) in enumerate(slides, 1):
                st.subheader(f"Slide {i}: {layout}")
                st.code(render_slide(layout, content))
    else:
        st.warning("Please enter some text to generate slides.")

st.markdown("""
---
This app uses advanced NLP techniques to analyze your input and generate appropriate slides.
It uses BERT for text embedding, clustering for coherent slide grouping, and extractive summarization for content.
""")