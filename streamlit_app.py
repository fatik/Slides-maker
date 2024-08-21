import streamlit as st
import re
from transformers import pipeline

# Define slide layouts
SLIDE_LAYOUTS = {
    "single_text_box": {"name": "Single Text Box", "elements": [{"type": "text", "max_words": 30, "style": "centered"}]},
    "bullet_points": {"name": "Bullet Points", "elements": [{"type": "title", "max_words": 5, "style": "left-aligned"}, {"type": "bullets", "max_bullets": 5, "max_words_per_bullet": 8, "style": "left-aligned"}]},
    "title_subtitle": {"name": "Title with Subtitle", "elements": [{"type": "title", "max_words": 5, "style": "large"}, {"type": "subtitle", "max_words": 15, "style": "medium"}]},
    "large_number": {"name": "Large Number/Percentage", "elements": [{"type": "number", "style": "very-large"}, {"type": "caption", "max_words": 20, "style": "small"}]},
    "three_column": {"name": "Three-Column Layout", "elements": [{"type": "column", "max_words": 20, "style": "left"}, {"type": "column", "max_words": 20, "style": "center"}, {"type": "column", "max_words": 20, "style": "right"}]},
    "image_caption": {"name": "Image with Caption", "elements": [{"type": "image_placeholder", "style": "centered"}, {"type": "caption", "max_words": 15, "style": "centered"}]},
    "two_column_text": {"name": "Two-Column Text", "elements": [{"type": "column", "max_words": 30, "style": "left"}, {"type": "column", "max_words": 30, "style": "right"}]},
    "four_square": {"name": "Four-Square Grid", "elements": [{"type": "title", "max_words": 5, "style": "top-centered"}, {"type": "square", "max_words": 20, "style": "top-left"}, {"type": "square", "max_words": 20, "style": "top-right"}, {"type": "square", "max_words": 20, "style": "bottom-left"}, {"type": "square", "max_words": 20, "style": "bottom-right"}]},
    "centered_square": {"name": "Centered Square", "elements": [{"type": "square", "max_words": 30, "style": "centered"}]},
    "blank": {"name": "Blank Layout", "elements": []}
}

@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

summarizer = load_summarizer()

def select_layout(scene_content):
    if re.search(r'\d+', scene_content):
        return "large_number"
    elif "!" in scene_content:
        return "centered_square"
    elif len(scene_content.split()) < 10:
        return "title_subtitle"
    elif "versus" in scene_content.lower() or "compared to" in scene_content.lower():
        return "two_column_text"
    elif "image" in scene_content.lower() or "picture" in scene_content.lower():
        return "image_caption"
    elif len(scene_content.split()) > 30:
        return "bullet_points"
    else:
        return "single_text_box"

def summarize_content(text, max_words):
    summary = summarizer(text, max_length=max_words, min_length=1, do_sample=False)[0]['summary_text']
    return ' '.join(summary.split()[:max_words])

def process_scene(scene_number, scene_content):
    layout = select_layout(scene_content)
    content = {}
    
    if layout == "large_number":
        number = re.search(r'\d+', scene_content).group()
        content = {"number": number, "caption": summarize_content(scene_content, 20)}
    elif layout in ["centered_square", "single_text_box"]:
        content = {"text": summarize_content(scene_content, 30)}
    elif layout == "title_subtitle":
        words = scene_content.split()
        content = {"title": ' '.join(words[:5]), "subtitle": summarize_content(' '.join(words[5:]), 15)}
    elif layout == "bullet_points":
        sentences = re.split(r'[.!?]+', scene_content)
        content = {"title": summarize_content(sentences[0], 5), "bullets": [summarize_content(s, 8) for s in sentences[1:5]]}
    elif layout == "image_caption":
        content = {"caption": summarize_content(scene_content, 15)}
    elif layout == "two_column_text":
        half = len(scene_content.split()) // 2
        content = {"left": summarize_content(' '.join(scene_content.split()[:half]), 30),
                   "right": summarize_content(' '.join(scene_content.split()[half:]), 30)}
    
    return f"Scene {scene_number}: layout: {layout}, content: {content}"

def process_script(script):
    scenes = re.split(r'\nScene \d+\n', script)[1:]
    results = []
    for i, scene in enumerate(scenes, 1):
        results.append(process_scene(i, scene.strip()))
    return results

st.title("Scene-Based Slide Generator")

script = st.text_area("Enter your script here (use 'Scene X' to denote scene breaks):", height=300)

if st.button("Generate Slides"):
    if script:
        with st.spinner("Processing script and generating slides..."):
            slides = process_script(script)
            for slide in slides:
                st.markdown(slide)
    else:
        st.warning("Please enter a script to generate slides.")

st.markdown("""
---
This app generates slide layouts and content based on your input script.
It uses a pre-trained summarization model to fit content into the chosen layouts.
""")