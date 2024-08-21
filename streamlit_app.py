import streamlit as st
import re
import random

# Define more sophisticated slide layouts
SLIDE_LAYOUTS = {
    "Title": {
        "elements": ["title"],
        "conditions": lambda s: len(s.split()) <= 10 and any(s.endswith(char) for char in "!?")
    },
    "Bullet Points": {
        "elements": ["title", "bullets"],
        "conditions": lambda s: len(s.split('.')) >= 3
    },
    "Big Fact": {
        "elements": ["fact", "explanation"],
        "conditions": lambda s: re.search(r'\d+', s) and len(s.split(',')) > 1
    },
    "Quote": {
        "elements": ["quote", "attribution"],
        "conditions": lambda s: '"' in s or "'" in s
    },
    "Image Idea": {
        "elements": ["image_description", "caption"],
        "conditions": lambda s: any(word in s.lower() for word in ['look', 'appear', 'image', 'picture', 'photo'])
    },
    "Two Columns": {
        "elements": ["left_column", "right_column"],
        "conditions": lambda s: any(word in s.lower() for word in ['versus', 'compared to', 'while', 'on the other hand'])
    },
    "Process": {
        "elements": ["title", "steps"],
        "conditions": lambda s: any(word in s.lower() for word in ['first', 'then', 'finally', 'lastly', 'step'])
    },
    "Comparison": {
        "elements": ["title", "item1", "item2"],
        "conditions": lambda s: 'more' in s.lower() or 'less' in s.lower() or 'than' in s.lower()
    },
    "Definition": {
        "elements": ["term", "definition"],
        "conditions": lambda s: 'is a' in s.lower() or 'are' in s.lower() or 'refers to' in s.lower()
    },
    "Statistic": {
        "elements": ["number", "context"],
        "conditions": lambda s: re.search(r'\d+%|\d+\s*(?:kg|lbs?|tons?)', s)
    }
}

def clean_text(text):
    return ' '.join(text.split())

def split_into_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text(text)) if s.strip()]

def select_layout(sentence, used_layouts):
    suitable_layouts = [name for name, layout in SLIDE_LAYOUTS.items() if layout["conditions"](sentence)]
    if suitable_layouts:
        # Prefer layouts that haven't been used recently
        for layout in suitable_layouts:
            if layout not in used_layouts[-3:]:
                return layout
        return random.choice(suitable_layouts)
    return "Bullet Points"  # Default to bullet points if no other layout fits

def create_slide_content(sentence, layout):
    content = {}
    if layout == "Title":
        content["title"] = sentence
    elif layout == "Bullet Points":
        parts = sentence.split('.')
        content["title"] = parts[0]
        content["bullets"] = [p.strip() for p in parts[1:] if p.strip()]
    elif layout == "Big Fact":
        parts = sentence.split(',', 1)
        content["fact"] = parts[0]
        content["explanation"] = parts[1] if len(parts) > 1 else ""
    elif layout == "Quote":
        match = re.search(r'"([^"]*)"', sentence)
        if match:
            content["quote"] = match.group(1)
            content["attribution"] = sentence.split('"')[-1].strip()
        else:
            content["quote"] = sentence
            content["attribution"] = "Anonymous"
    elif layout == "Image Idea":
        parts = sentence.split(',', 1)
        content["image_description"] = parts[0]
        content["caption"] = parts[1] if len(parts) > 1 else ""
    elif layout == "Two Columns":
        for split_word in ['versus', 'compared to', 'while', 'on the other hand']:
            if split_word in sentence.lower():
                parts = sentence.lower().split(split_word)
                content["left_column"] = parts[0].strip()
                content["right_column"] = parts[1].strip()
                break
        if "left_column" not in content:
            parts = sentence.split(',', 1)
            content["left_column"] = parts[0]
            content["right_column"] = parts[1] if len(parts) > 1 else ""
    elif layout == "Process":
        parts = sentence.split(',')
        content["title"] = parts[0]
        content["steps"] = [p.strip() for p in parts[1:] if p.strip()]
    elif layout == "Comparison":
        match = re.search(r'(.*)\s(?:is|are)\s(more|less)\s(.*)\sthan\s(.*)', sentence, re.IGNORECASE)
        if match:
            content["title"] = f"Comparing {match.group(1)} and {match.group(4)}"
            content["item1"] = f"{match.group(1)}: {match.group(2)} {match.group(3)}"
            content["item2"] = match.group(4)
        else:
            parts = sentence.split(',')
            content["title"] = "Comparison"
            content["item1"] = parts[0]
            content["item2"] = parts[1] if len(parts) > 1 else ""
    elif layout == "Definition":
        parts = re.split(r'\sis\s|\sare\s|\srefers to\s', sentence, 1, re.IGNORECASE)
        content["term"] = parts[0]
        content["definition"] = parts[1] if len(parts) > 1 else ""
    elif layout == "Statistic":
        match = re.search(r'(\d+(?:%|\s*(?:kg|lbs?|tons?)))', sentence)
        if match:
            content["number"] = match.group(1)
            content["context"] = sentence.replace(match.group(1), '___')
        else:
            content["number"] = "N/A"
            content["context"] = sentence
    return content

def render_slide(layout_name, content):
    slide = f"[Slide: {layout_name}]\n"
    for element, text in content.items():
        if isinstance(text, list):
            slide += f"{element.replace('_', ' ').capitalize()}:\n"
            for item in text:
                slide += f"- {item}\n"
        else:
            slide += f"{element.replace('_', ' ').capitalize()}: {text}\n"
    return slide

st.title("Advanced Intelligent Slide Generator")

input_text = st.text_area("Enter your script here:", height=200)

if st.button("Generate Slides"):
    if input_text:
        sentences = split_into_sentences(input_text)
        slides = []
        used_layouts = []
        
        for sentence in sentences:
            layout_name = select_layout(sentence, used_layouts)
            content = create_slide_content(sentence, layout_name)
            slides.append((layout_name, content))
            used_layouts.append(layout_name)
        
        for i, (layout_name, content) in enumerate(slides, 1):
            st.subheader(f"Slide {i}: {layout_name}")
            st.code(render_slide(layout_name, content))
    else:
        st.warning("Please enter some text to generate slides.")

st.markdown("""
---
This app generates slides based on your input text.
It uses advanced content analysis to select appropriate layouts and ensure variety.
""")