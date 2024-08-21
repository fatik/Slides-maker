import streamlit as st
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

# Download necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# Define slide layouts (keep the SLIDE_LAYOUTS dictionary as it was)

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



def preprocess_text(text):
    # Tokenize the text
    words = word_tokenize(text.lower())
    # Remove stopwords and punctuation
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalnum() and word not in stop_words]
    return words

def extract_key_phrases(text, max_words):
    words = preprocess_text(text)
    # Count word frequencies
    word_freq = Counter(words)
    # Sort words by frequency, then by their order of appearance in the original text
    sorted_words = sorted(word_freq, key=lambda x: (-word_freq[x], words.index(x)))
    # Return the top words up to max_words
    return ' '.join(sorted_words[:max_words])

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

def process_scene(scene_number, scene_content):
    layout = select_layout(scene_content)
    content = {}
    
    if layout == "large_number":
        number = re.search(r'\d+', scene_content).group()
        content = {"number": number, "caption": extract_key_phrases(scene_content, 20)}
    elif layout in ["centered_square", "single_text_box"]:
        content = {"text": extract_key_phrases(scene_content, 30)}
    elif layout == "title_subtitle":
        sentences = sent_tokenize(scene_content)
        content = {
            "title": extract_key_phrases(sentences[0], 5),
            "subtitle": extract_key_phrases(' '.join(sentences[1:]), 15) if len(sentences) > 1 else ""
        }
    elif layout == "bullet_points":
        sentences = sent_tokenize(scene_content)
        content = {
            "title": extract_key_phrases(sentences[0], 5),
            "bullets": [extract_key_phrases(s, 8) for s in sentences[1:5]]
        }
    elif layout == "image_caption":
        content = {"caption": extract_key_phrases(scene_content, 15)}
    elif layout == "two_column_text":
        half = len(scene_content) // 2
        content = {
            "left": extract_key_phrases(scene_content[:half], 30),
            "right": extract_key_phrases(scene_content[half:], 30)
        }
    
    return f"Scene {scene_number}: layout: {layout}, content: {content}"

def process_script(script):
    scenes = re.split(r'Scene \d+', script)
    scenes = [scene.strip() for scene in scenes if scene.strip()]
    results = []
    for i, scene in enumerate(scenes, 1):
        results.append(process_scene(i, scene))
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
It extracts key phrases and important words to fit content into the chosen layouts.
""")