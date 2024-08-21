import streamlit as st
import re
from transformers import pipeline
import torch

# Define all 20 slide layouts
SLIDE_LAYOUTS = {
    "3HP": {
        "name": "Three Horizontal Points",
        "elements": ["point1", "point2", "point3"],
        "max_chars": {"point1": 30, "point2": 30, "point3": 30}
    },
    "T3P": {
        "name": "Title with Three Paragraphs",
        "elements": ["title", "paragraph1", "paragraph2", "paragraph3"],
        "max_chars": {"title": 50, "paragraph1": 160, "paragraph2": 160, "paragraph3": 160}
    },
    "BQ": {
        "name": "Big Question",
        "elements": ["question"],
        "max_chars": {"question": 100}
    },
    "IC": {
        "name": "Image with Caption",
        "elements": ["image_placeholder", "caption"],
        "max_chars": {"caption": 100}
    },
    "2CC": {
        "name": "Two-Column Compare",
        "elements": ["header", "left1", "left2", "left3", "left4", "right1", "right2", "right3", "right4"],
        "max_chars": {"header": 40, "left1": 50, "left2": 50, "left3": 50, "left4": 50, 
                      "right1": 50, "right2": 50, "right3": 50, "right4": 50}
    },
    "QS": {
        "name": "Quote Spotlight",
        "elements": ["quote", "attribution"],
        "max_chars": {"quote": 200, "attribution": 50}
    },
    "PL": {
        "name": "Pyramid List",
        "elements": ["top", "middle1", "middle2", "bottom1", "bottom2", "bottom3"],
        "max_chars": {"top": 30, "middle1": 30, "middle2": 30, "bottom1": 30, "bottom2": 30, "bottom3": 30}
    },
    "CP": {
        "name": "Circular Process",
        "elements": ["circle1", "circle2", "circle3", "circle4", "circle5", "circle6"],
        "max_chars": {"circle1": 20, "circle2": 20, "circle3": 20, "circle4": 20, "circle5": 20, "circle6": 20}
    },
    "TL": {
        "name": "Timeline",
        "elements": ["date1", "event1", "date2", "event2", "date3", "event3", "date4", "event4", "date5", "event5"],
        "max_chars": {"date1": 15, "event1": 50, "date2": 15, "event2": 50, "date3": 15, "event3": 50, 
                      "date4": 15, "event4": 50, "date5": 15, "event5": 50}
    },
    "DV": {
        "name": "Data Visualization",
        "elements": ["title", "chart_placeholder", "legend1", "legend2", "legend3", "legend4", "legend5"],
        "max_chars": {"title": 60, "legend1": 20, "legend2": 20, "legend3": 20, "legend4": 20, "legend5": 20}
    },
    "PS": {
        "name": "Problem-Solution",
        "elements": ["problem", "solution"],
        "max_chars": {"problem": 200, "solution": 200}
    },
    "TS": {
        "name": "Team Showcase",
        "elements": ["name1", "name2", "name3", "name4", "name5", "name6"],
        "max_chars": {"name1": 30, "name2": 30, "name3": 30, "name4": 30, "name5": 30, "name6": 30}
    },
    "SS": {
        "name": "Single Statistic",
        "elements": ["statistic", "context"],
        "max_chars": {"statistic": 20, "context": 100}
    },
    "SWOT": {
        "name": "SWOT Analysis",
        "elements": ["title", "strengths", "weaknesses", "opportunities", "threats"],
        "max_chars": {"title": 20, "strengths": 100, "weaknesses": 100, "opportunities": 100, "threats": 100}
    },
    "MM": {
        "name": "Mind Map",
        "elements": ["center", "branch1", "branch2", "branch3", "branch4", "branch5"],
        "max_chars": {"center": 30, "branch1": 40, "branch2": 40, "branch3": 40, "branch4": 40, "branch5": 40}
    },
    "BA": {
        "name": "Before and After",
        "elements": ["before", "after"],
        "max_chars": {"before": 150, "after": 150}
    },
    "CL": {
        "name": "Checklist",
        "elements": ["title", "item1", "item2", "item3", "item4", "item5", "item6", "item7"],
        "max_chars": {"title": 50, "item1": 60, "item2": 60, "item3": 60, "item4": 60, "item5": 60, "item6": 60, "item7": 60}
    },
    "RM": {
        "name": "Roadmap",
        "elements": ["milestone1", "milestone2", "milestone3", "milestone4", "milestone5"],
        "max_chars": {"milestone1": 30, "milestone2": 30, "milestone3": 30, "milestone4": 30, "milestone5": 30}
    },
    "TM": {
        "name": "Testimonial",
        "elements": ["quote", "name", "title"],
        "max_chars": {"quote": 200, "name": 30, "title": 50}
    },
    "CTA": {
        "name": "Call to Action",
        "elements": ["statement", "button"],
        "max_chars": {"statement": 100, "button": 20}
    }
}

@st.cache_resource
def load_pipeline():
    return pipeline("summarization", model="facebook/bart-large-cnn", device=0 if torch.cuda.is_available() else -1)

summarizer = load_pipeline()

def clean_text(text):
    return ' '.join(text.split())

def split_into_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text(text)) if s.strip()]

def summarize_text(text, max_length=30):
    summary = summarizer(text, max_length=max_length, min_length=10, do_sample=False)[0]['summary_text']
    return summary

def select_layout(content, used_layouts):
    if "?" in content and "BQ" not in used_layouts:
        return "BQ"
    elif re.search(r'\d+(?:%|\s*(?:kg|lbs?|tons?))', content) and "SS" not in used_layouts:
        return "SS"
    elif '"' in content and "QS" not in used_layouts:
        return "QS"
    elif any(word in content.lower() for word in ["image", "picture", "photo"]) and "IC" not in used_layouts:
        return "IC"
    elif ("versus" in content.lower() or "compared to" in content.lower()) and "2CC" not in used_layouts:
        return "2CC"
    elif any(word in content.lower() for word in ["first", "then", "finally", "lastly"]) and "CP" not in used_layouts:
        return "CP"
    elif any(word in content.lower() for word in ["year", "date", "period"]) and "TL" not in used_layouts:
        return "TL"
    elif any(word in content.lower() for word in ["data", "chart", "graph"]) and "DV" not in used_layouts:
        return "DV"
    elif ("problem" in content.lower() and "solution" in content.lower()) and "PS" not in used_layouts:
        return "PS"
    elif "team" in content.lower() and "TS" not in used_layouts:
        return "TS"
    elif any(word in content.lower() for word in ["strength", "weakness", "opportunity", "threat"]) and "SWOT" not in used_layouts:
        return "SWOT"
    elif "idea" in content.lower() and "MM" not in used_layouts:
        return "MM"
    elif ("before" in content.lower() and "after" in content.lower()) and "BA" not in used_layouts:
        return "BA"
    elif any(word in content.lower() for word in ["checklist", "to-do"]) and "CL" not in used_layouts:
        return "CL"
    elif any(word in content.lower() for word in ["roadmap", "plan", "strategy"]) and "RM" not in used_layouts:
        return "RM"
    elif "said" in content.lower() and "TM" not in used_layouts:
        return "TM"
    elif any(word in content.lower() for word in ["subscribe", "follow", "join"]) and "CTA" not in used_layouts:
        return "CTA"
    elif "3HP" not in used_layouts:
        return "3HP"
    elif "T3P" not in used_layouts:
        return "T3P"
    elif "PL" not in used_layouts:
        return "PL"
    else:
        return "T3P"  # Default to T3P if all others have been used

def create_slide_content(content, layout_key):
    layout = SLIDE_LAYOUTS[layout_key]
    slide_content = {}
    sentences = split_into_sentences(content)
    
    for i, element in enumerate(layout["elements"]):
        if element.startswith("image") or element.startswith("chart"):
            slide_content[element] = f"[{element.replace('_', ' ').title()}]"
        else:
            text = sentences[i] if i < len(sentences) else ""
            slide_content[element] = summarize_text(text, layout["max_chars"][element])
    
    return slide_content

def render_slide(layout_key, content):
    layout = SLIDE_LAYOUTS[layout_key]
    slide = f"[Slide: {layout['name']} (Key: {layout_key})]\n"
    for element in layout["elements"]:
        slide += f"{element}: {content.get(element, 'N/A')}\n"
    return slide

st.title("Full Custom Layout Slide Generator")

input_text = st.text_area("Enter your script here:", height=200)

if st.button("Generate Slides"):
    if input_text:
        with st.spinner("Analyzing content and generating slides..."):
            sentences = split_into_sentences(input_text)
            slides = []
            used_layouts = set()
            
            for sentence in sentences:
                layout_key = select_layout(sentence, used_layouts)
                content = create_slide_content(sentence, layout_key)
                slides.append((layout_key, content))
                used_layouts.add(layout_key)
                
                if len(used_layouts) == len(SLIDE_LAYOUTS):
                    used_layouts.clear()
            
            for i, (layout_key, content) in enumerate(slides, 1):
                st.subheader(f"Slide {i}: {SLIDE_LAYOUTS[layout_key]['name']} (Key: {layout_key})")
                st.code(render_slide(layout_key, content))
    else:
        st.warning("Please enter some text to generate slides.")

st.markdown("""
---
This app uses the BART model to analyze your input and generate slides based on 20 custom layouts.
It selects layouts based on content type and summarizes content to fit slide constraints.
""")