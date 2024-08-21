import streamlit as st
import re

# Define simple slide layouts
SLIDE_LAYOUTS = {
    "Title": {
        "elements": ["title"]
    },
    "Bullet Points": {
        "elements": ["title", "bullets"]
    },
    "Quote": {
        "elements": ["quote", "attribution"]
    },
    "Image with Caption": {
        "elements": ["image_placeholder", "caption"]
    },
    "Two Columns": {
        "elements": ["left_column", "right_column"]
    }
}

def clean_text(text):
    # Remove extra whitespace and newlines
    return ' '.join(text.split())

def split_into_sentences(text):
    # Simple sentence splitting
    return re.split(r'(?<=[.!?])\s+', clean_text(text))

def create_slide_content(sentences, layout):
    content = {}
    for element in layout["elements"]:
        if sentences:
            if element == "bullets":
                content[element] = sentences[:3]  # Take up to 3 sentences for bullets
                sentences = sentences[3:]
            else:
                content[element] = sentences.pop(0) if sentences else "N/A"
        else:
            content[element] = "N/A"
    return content

def render_slide(layout_name, content):
    slide = f"[Slide: {layout_name}]\n"
    for element, text in content.items():
        if element == "bullets":
            slide += "Bullet Points:\n"
            for bullet in text:
                slide += f"- {bullet}\n"
        elif element == "image_placeholder":
            slide += "[Image Placeholder]\n"
        else:
            slide += f"{element.capitalize()}: {text}\n"
    return slide

st.title("Simple Slide Generator")

input_text = st.text_area("Enter your script here:", height=200)

if st.button("Generate Slides"):
    if input_text:
        sentences = split_into_sentences(input_text)
        slides = []
        
        while sentences:
            for layout_name, layout in SLIDE_LAYOUTS.items():
                content = create_slide_content(sentences, layout)
                slides.append((layout_name, content))
                if not sentences:
                    break
        
        for i, (layout_name, content) in enumerate(slides, 1):
            st.subheader(f"Slide {i}: {layout_name}")
            st.code(render_slide(layout_name, content))
    else:
        st.warning("Please enter some text to generate slides.")

st.markdown("""
---
This app generates simple slides based on your input text.
It uses basic text processing and predefined layouts.
""")