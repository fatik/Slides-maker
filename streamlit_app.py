import streamlit as st
import re

# Define slide layouts with more specific content requirements
SLIDE_LAYOUTS = {
    "Title": {
        "elements": ["title"],
        "conditions": lambda s: len(s) <= 10 and s.endswith('!')
    },
    "Bullet Points": {
        "elements": ["title", "bullets"],
        "conditions": lambda s: len(s.split('.')) >= 3
    },
    "Big Fact": {
        "elements": ["fact", "explanation"],
        "conditions": lambda s: any(word.isdigit() for word in s.split())
    },
    "Quote": {
        "elements": ["quote", "attribution"],
        "conditions": lambda s: '"' in s or 'said' in s.lower()
    },
    "Image Idea": {
        "elements": ["image_description", "caption"],
        "conditions": lambda s: 'looks' in s.lower() or 'appears' in s.lower() or 'image' in s.lower()
    },
    "Two Columns": {
        "elements": ["left_column", "right_column"],
        "conditions": lambda s: 'versus' in s.lower() or 'compared to' in s.lower() or 'while' in s.lower()
    }
}

def clean_text(text):
    return ' '.join(text.split())

def split_into_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text(text)) if s.strip()]

def select_layout(sentence, used_layouts):
    for layout_name, layout in SLIDE_LAYOUTS.items():
        if layout_name not in used_layouts and layout["conditions"](sentence):
            return layout_name
    return "Bullet Points"  # Default to bullet points if no other layout fits

def create_slide_content(sentence, layout):
    content = {}
    if layout == "Title":
        content["title"] = sentence
    elif layout == "Bullet Points":
        content["title"] = sentence.split('.')[0]
        content["bullets"] = [s.strip() for s in sentence.split('.')[1:] if s.strip()]
    elif layout == "Big Fact":
        parts = sentence.split(',', 1)
        content["fact"] = parts[0]
        content["explanation"] = parts[1] if len(parts) > 1 else ""
    elif layout == "Quote":
        parts = sentence.split('"')
        content["quote"] = f'"{parts[1]}"' if len(parts) > 1 else sentence
        content["attribution"] = parts[2].strip() if len(parts) > 2 else "Anonymous"
    elif layout == "Image Idea":
        parts = sentence.split(',', 1)
        content["image_description"] = parts[0]
        content["caption"] = parts[1] if len(parts) > 1 else ""
    elif layout == "Two Columns":
        parts = re.split(r'\sversus\s|\scompared to\s|\swhile\s', sentence, flags=re.IGNORECASE)
        content["left_column"] = parts[0]
        content["right_column"] = parts[1] if len(parts) > 1 else ""
    return content

def render_slide(layout_name, content):
    slide = f"[Slide: {layout_name}]\n"
    for element, text in content.items():
        if element == "bullets":
            slide += "Bullet Points:\n"
            for bullet in text:
                slide += f"- {bullet}\n"
        elif element == "image_description":
            slide += f"[Image of: {text}]\n"
        else:
            slide += f"{element.replace('_', ' ').capitalize()}: {text}\n"
    return slide

st.title("Intelligent Slide Generator")

input_text = st.text_area("Enter your script here:", height=200)

if st.button("Generate Slides"):
    if input_text:
        sentences = split_into_sentences(input_text)
        slides = []
        used_layouts = set()
        
        for sentence in sentences:
            layout_name = select_layout(sentence, used_layouts)
            content = create_slide_content(sentence, layout_name)
            slides.append((layout_name, content))
            used_layouts.add(layout_name)
            
            # Reset used_layouts if all layouts have been used
            if len(used_layouts) == len(SLIDE_LAYOUTS):
                used_layouts = set()
        
        for i, (layout_name, content) in enumerate(slides, 1):
            st.subheader(f"Slide {i}: {layout_name}")
            st.code(render_slide(layout_name, content))
    else:
        st.warning("Please enter some text to generate slides.")

st.markdown("""
---
This app generates slides based on your input text.
It uses content analysis to select appropriate layouts and avoid repetitions.
""")