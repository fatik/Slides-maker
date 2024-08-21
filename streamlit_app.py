import streamlit as st
import re

# Define slide layouts
SLIDE_LAYOUTS = {
    "Title": {"elements": ["title", "subtitle"], "max_chars": {"title": 50, "subtitle": 100}},
    "Bullet": {"elements": ["title", "bullet1", "bullet2", "bullet3"], "max_chars": {"title": 50, "bullet1": 60, "bullet2": 60, "bullet3": 60}},
    "Quote": {"elements": ["quote", "attribution"], "max_chars": {"quote": 200, "attribution": 50}},
    "Image": {"elements": ["caption"], "max_chars": {"caption": 100}},
    "Fact": {"elements": ["fact", "explanation"], "max_chars": {"fact": 50, "explanation": 150}},
    "Compare": {"elements": ["title", "left", "right"], "max_chars": {"title": 50, "left": 100, "right": 100}},
    "Conclusion": {"elements": ["title", "summary", "call_to_action"], "max_chars": {"title": 50, "summary": 150, "call_to_action": 50}}
}

def clean_text(text):
    return ' '.join(text.split())

def split_into_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text(text)) if s.strip()]

def truncate_text(text, max_length):
    words = text.split()
    if len(words) <= max_length:
        return text
    return ' '.join(words[:max_length]) + '...'

def select_layout(index, total_slides):
    if index == 0:
        return "Title"
    elif index == total_slides - 1:
        return "Conclusion"
    elif '"' in sentences[index]:
        return "Quote"
    elif any(word in sentences[index].lower() for word in ['image', 'picture', 'photo']):
        return "Image"
    elif re.search(r'\d+', sentences[index]):
        return "Fact"
    elif 'versus' in sentences[index].lower() or 'compared to' in sentences[index].lower():
        return "Compare"
    else:
        return "Bullet"

def create_slide_content(sentences, layout_key, index):
    layout = SLIDE_LAYOUTS[layout_key]
    content = {}
    
    for element in layout['elements']:
        if element == 'title':
            content[element] = truncate_text(sentences[index], layout['max_chars'][element] // 5)
        elif element == 'subtitle' or element == 'summary':
            content[element] = truncate_text(' '.join(sentences[index:index+2]), layout['max_chars'][element] // 5)
        elif element.startswith('bullet'):
            bullet_index = int(element[-1]) - 1
            if index + bullet_index < len(sentences):
                content[element] = truncate_text(sentences[index + bullet_index], layout['max_chars'][element] // 5)
            else:
                content[element] = ""
        elif element == 'quote':
            match = re.search(r'"([^"]*)"', sentences[index])
            content[element] = truncate_text(match.group(1) if match else sentences[index], layout['max_chars'][element] // 5)
        elif element == 'attribution':
            content[element] = truncate_text(sentences[index].split('"')[-1].strip(), layout['max_chars'][element] // 5)
        elif element == 'fact':
            content[element] = truncate_text(re.search(r'\d+[^.!?]*', sentences[index]).group(), layout['max_chars'][element] // 5)
        elif element == 'explanation':
            content[element] = truncate_text(sentences[index], layout['max_chars'][element] // 5)
        elif element in ['left', 'right']:
            parts = re.split(r'\sversus\s|\scompared to\s', sentences[index], flags=re.IGNORECASE)
            content[element] = truncate_text(parts[0] if element == 'left' else parts[1], layout['max_chars'][element] // 5)
        elif element == 'call_to_action':
            content[element] = truncate_text(sentences[-1], layout['max_chars'][element] // 5)
        else:
            content[element] = truncate_text(sentences[index], layout['max_chars'][element] // 5)
    
    return content

def render_slide(layout_key, content):
    layout = SLIDE_LAYOUTS[layout_key]
    slide = f"[Slide: {layout_key}]\n"
    for element in layout['elements']:
        slide += f"{element.capitalize()}: {content.get(element, 'N/A')}\n"
    return slide

st.title("Coherent Slide Generator")

input_text = st.text_area("Enter your script here:", height=200)

if st.button("Generate Slides"):
    if input_text:
        with st.spinner("Generating slides..."):
            sentences = split_into_sentences(input_text)
            slides = []
            
            for i in range(len(sentences)):
                layout_key = select_layout(i, len(sentences))
                content = create_slide_content(sentences, layout_key, i)
                slides.append((layout_key, content))
            
            for i, (layout_key, content) in enumerate(slides, 1):
                st.subheader(f"Slide {i}: {layout_key}")
                st.code(render_slide(layout_key, content))
    else:
        st.warning("Please enter some text to generate slides.")

st.markdown("""
---
This app generates coherent slides based on your input text.
It selects appropriate layouts and adapts content to fit each slide type.
""")