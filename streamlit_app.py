import streamlit as st
import re
from transformers import pipeline, set_seed
import openai



# Set up OpenAI API
openai.api_key = st.secrets["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"]

@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn", device=-1)

summarizer = load_summarizer()
set_seed(42)

def ai_process_content(text, instruction):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI assistant that helps create concise slide content from video script text."},
            {"role": "user", "content": f"Based on this text: '{text}', {instruction}"}
        ]
    )
    return response.choices[0].message['content'].strip()

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
        content = {"number": number, "caption": ai_process_content(scene_content, "Generate a brief caption (max 5 words) to accompany this number on a slide.")}
    elif layout in ["centered_square", "single_text_box"]:
        content = {"text": ai_process_content(scene_content, "Extract the key idea in 5-7 words for a slide.")}
    elif layout == "title_subtitle":
        content = {
            "title": ai_process_content(scene_content, "Create a catchy title (3-5 words) for a slide."),
            "subtitle": ai_process_content(scene_content, "Provide a brief subtitle (max 10 words) that complements the title.")
        }
    elif layout == "bullet_points":
        content = {
            "title": ai_process_content(scene_content, "Create a short title (3-5 words) for a bullet point slide."),
            "bullets": [ai_process_content(scene_content, f"Extract key point {i} (max 5 words) for a bullet on the slide.") for i in range(1, 4)]
        }
    elif layout == "image_caption":
        content = {"caption": ai_process_content(scene_content, "Create a brief image caption (max 10 words) based on this text.")}
    elif layout == "two_column_text":
        content = {
            "left": ai_process_content(scene_content, "Summarize the first half of the content in 5-7 words for the left column of a slide."),
            "right": ai_process_content(scene_content, "Summarize the second half of the content in 5-7 words for the right column of a slide.")
        }
    
    return f"Scene {scene_number}: layout: {layout}, content: {content}"

def process_script(script):
    scenes = re.split(r'Scene \d+', script)
    scenes = [scene.strip() for scene in scenes if scene.strip()]
    results = []
    for i, scene in enumerate(scenes, 1):
        results.append(process_scene(i, scene))
    return results

st.title("AI-Powered Scene-Based Slide Generator")

script = st.text_area("Enter your script here (use 'Scene X' to denote scene breaks):", height=300)

if st.button("Generate Slides"):
    if script:
        with st.spinner("Processing script and generating intelligent slides..."):
            slides = process_script(script)
            for slide in slides:
                st.markdown(slide)
    else:
        st.warning("Please enter a script to generate slides.")

st.markdown("""
---
This app uses AI to generate intelligent slide layouts and content based on your input script.
It creates concise and relevant content for each slide, different from the original subtitles.
""")