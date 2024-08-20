import streamlit as st
import re
from transformers import pipeline

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
    
    def safe_get(lst, index, default=""):
        return lst[index] if index < len(lst) else default
    
    def safe_split(text, max_words):
        words = text.split()
        return ' '.join(words[:max_words])

    for element in layout['elements']:
        if element['type'] in ['heading', 'title', 'caption', 'subheading', 'description']:
            fitted_content[element['type']] = safe_split(safe_get(content, 0), element['max_words'])
            if content:
                content = content[1:]
        elif element['type'] == 'bullets':
            bullets = []
            for _ in range(min(element['max_bullets'], len(content))):
                bullets.append(safe_split(safe_get(content, 0), element['max_words_per_bullet']))
                if content:
                    content = content[1:]
            fitted_content[element['type']] = bullets
        elif element['type'] == 'quote':
            fitted_content[element['type']] = safe_split(safe_get(content, 0), element['max_words'])
            if content:
                content = content[1:]
        elif element['type'] == 'attribution':
            fitted_content[element['type']] = safe_split(safe_get(content, -1), element['max_words'])
        elif element['type'] == 'number':
            numbers = re.findall(r'\d+', ' '.join(content))
            fitted_content[element['type']] = numbers[0] if numbers else "N/A"
        elif element['type'] == 'timeline_points':
            points = []
            for _ in range(min(element['max_points'], len(content))):
                points.append(safe_split(safe_get(content, 0), element['max_words_per_point']))
                if content:
                    content = content[1:]
            fitted_content[element['type']] = points
        elif element['type'] == 'button':
            fitted_content[element['type']] = safe_split(safe_get(content, -1), element['max_words'])
        elif element['type'] == 'comparison':
            items = []
            for _ in range(element['items']):
                items.append(safe_split(safe_get(content, 0), element['max_words_per_item']))
                if content:
                    content = content[1:]
            fitted_content[element['type']] = items
        elif element['type'] == 'column':
            column_content = ' '.join(content[:2])
            fitted_content[element['type']] = fitted_content.get(element['type'], []) + [safe_split(column_content, element['max_words'])]
            content = content[2:] if len(content) > 2 else []
        elif element['type'] == 'image_placeholder':
            fitted_content[element['type']] = "[Image Placeholder]"

    return fitted_content

def select_layout(content):
    if not content:
        return "BH"  # Default to Big Heading if no content
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

st.title("Layout Generator")

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
                if not key_info:  # If we've used all content, break the loop
                    break
            
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