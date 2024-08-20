import streamlit as st
import re
from transformers import pipeline
import random

# Define slide layouts
SLIDE_LAYOUTS = {
    "BH": {
        "name": "Big Heading",
        "elements": [
            {"type": "heading", "max_words": 4, "style": "large, centered"}
        ]
    },
    "HCS": {
        "name": "Heading with Caption and Subheading",
        "elements": [
            {"type": "heading", "max_words": 5, "style": "large"},
            {"type": "caption", "max_words": 10, "style": "medium"},
            {"type": "subheading", "max_words": 15, "style": "small"}
        ]
    },
    "TB": {
        "name": "Title with Bullets",
        "elements": [
            {"type": "title", "max_words": 7, "style": "large"},
            {"type": "bullets", "max_bullets": 4, "max_words_per_bullet": 8, "style": "medium"}
        ]
    },
    "QS": {
        "name": "Quote Spotlight",
        "elements": [
            {"type": "quote", "max_words": 20, "style": "large, italics"},
            {"type": "attribution", "max_words": 5, "style": "small"}
        ]
    },
    "IC": {
        "name": "Image with Caption",
        "elements": [
            {"type": "image_placeholder", "style": "centered"},
            {"type": "caption", "max_words": 15, "style": "small"}
        ]
    },
    "2C": {
        "name": "Two Columns",
        "elements": [
            {"type": "column", "max_words": 30, "style": "left"},
            {"type": "column", "max_words": 30, "style": "right"}
        ]
    },
    "NS": {
        "name": "Number Spotlight",
        "elements": [
            {"type": "number", "style": "very large, centered"},
            {"type": "description", "max_words": 10, "style": "medium"}
        ]
    },
    "TM": {
        "name": "Timeline",
        "elements": [
            {"type": "title", "max_words": 5, "style": "large"},
            {"type": "timeline_points", "max_points": 5, "max_words_per_point": 6, "style": "small"}
        ]
    },
    "CTA": {
        "name": "Call to Action",
        "elements": [
            {"type": "heading", "max_words": 6, "style": "large"},
            {"type": "subheading", "max_words": 10, "style": "medium"},
            {"type": "button", "max_words": 3, "style": "prominent"}
        ]
    },
    "CM": {
        "name": "Comparison",
        "elements": [
            {"type": "title", "max_words": 5, "style": "large"},
            {"type": "comparison", "items": 2, "max_words_per_item": 20, "style": "side-by-side"}
        ]
    }
}

@st.cache_resource
def load_nlp_pipeline():
    return pipeline("summarization", model="facebook/bart-large-cnn")

nlp = load_nlp_pipeline()

def extract_key_info(text):
    summary = nlp(text, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
    sentences = re.split(r'(?<=[.!?])\s+', summary)
    return sentences

def fit_content_to_layout(content, layout):
    fitted_content = {}
    for element in layout['elements']:
        if element['type'] == 'heading' or element['type'] == 'title':
            words = content[0].split()
            fitted_content[element['type']] = ' '.join(words[:element['max_words']])
            content = content[1:]
        elif element['type'] == 'bullets':
            bullets = []
            for _ in range(min(element['max_bullets'], len(content))):
                words = content[0].split()
                bullets.append(' '.join(words[:element['max_words_per_bullet']]))
                content = content[1:]
            fitted_content[element['type']] = bullets
        elif element['type'] == 'quote':
            words = content[0].split()
            fitted_content[element['type']] = ' '.join(words[:element['max_words']])
            content = content[1:]
        elif element['type'] == 'attribution':
            words = content[-1].split()
            fitted_content[element['type']] = ' '.join(words[:element['max_words']])
        elif element['type'] == 'caption' or element['type'] == 'subheading' or element['type'] == 'description':
            words = ' '.join(content).split()
            fitted_content[element['type']] = ' '.join(words[:element['max_words']])
        elif element['type'] == 'number':
            numbers = re.findall(r'\d+', ' '.join(content))
            fitted_content[element['type']] = numbers[0] if numbers else "N/A"
        elif element['type'] == 'timeline_points':
            points = []
            for _ in range(min(element['max_points'], len(content))):
                words = content[0].split()
                points.append(' '.join(words[:element['max_words_per_point']]))
                content = content[1:]
            fitted_content[element['type']] = points
        elif element['type'] == 'button':
            words = content[-1].split()
            fitted_content[element['type']] = ' '.join(words[:element['max_words']])
        elif element['type'] == 'comparison':
            items = []
            for _ in range(element['items']):
                if content:
                    words = content[0].split()
                    items.append(' '.join(words[:element['max_words_per_item']]))
                    content = content[1:]
            fitted_content[element['type']] = items
        elif element['type'] == 'column':
            words = ' '.join(content[:2]).split()
            fitted_content[element['type']] = fitted_content.get(element['type'], []) + [' '.join(words[:element['max_words']])]
            content = content[2:]
    return fitted_content

def select_layout(content):
    if any('?' in sentence for sentence in content):
        return "BH"
    elif any(re.search(r'\d+', sentence) for sentence in content):
        return "NS"
    elif len(content) >= 4:
        return "TB"
    elif any('"' in sentence for sentence in content):
        return "QS"
    elif any('image' in sentence.lower() for sentence in content):
        return "IC"
    elif len(content) == 2:
        return "2C"
    elif any('timeline' in sentence.lower() for sentence in content):
        return "TM"
    elif any('action' in sentence.lower() for sentence in content):
        return "CTA"
    elif any('compare' in sentence.lower() or 'versus' in sentence.lower() for sentence in content):
        return "CM"
    else:
        return "HCS"

def render_slide(layout_key, content):
    layout = SLIDE_LAYOUTS[layout_key]
    slide = f"[Slide: {layout['name']}]\n"
    for element in layout['elements']:
        if element['type'] in content:
            if isinstance(content[element['type']], list):
                for item in content[element['type']]:
                    slide += f"<{element['type']} style='{element['style']}'>{item}</{element['type']}>\n"
            else:
                slide += f"<{element['type']} style='{element['style']}'>{content[element['type']]}</{element['type']}>\n"
    return slide

st.title("Intelligent Layout-Based Slide Generator")

input_text = st.text_area("Enter your script here:", height=200)

if st.button("Generate Slides"):
    if input_text:
        with st.spinner("Analyzing content and generating slides..."):
            key_info = extract_key_info(input_text)
            slides = []
            
            while key_info:
                layout_key = select_layout(key_info[:3])  # Look at next 3 sentences max
                layout = SLIDE_LAYOUTS[layout_key]
                content = fit_content_to_layout(key_info, layout)
                slides.append((layout_key, content))
                key_info = key_info[len(layout['elements']):]  # Move to next chunk of content
            
            for i, (layout_key, content) in enumerate(slides, 1):
                st.subheader(f"Slide {i}: {SLIDE_LAYOUTS[layout_key]['name']}")
                st.code(render_slide(layout_key, content))
    else:
        st.warning("Please enter some text to generate slides.")

st.markdown("""
---
This app uses a pre-trained NLP model to analyze your input and generate appropriate slides.
The slide layouts are predefined, but the content is dynamically fitted to each layout.
""")