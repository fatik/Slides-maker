import streamlit as st
import re
from transformers import pipeline

# Define slide types and their rules
SLIDE_TYPES = {
    "3HP": {"name": "Three Horizontal Points", "max_points": 3, "max_chars_per_point": 30},
    "T3P": {"name": "Title with Three Paragraphs", "max_title_chars": 50, "max_paragraph_chars": 160},
    "BQ": {"name": "Big Question", "max_chars": 100},
    "IC": {"name": "Image with Caption", "max_caption_chars": 100},
    "2CC": {"name": "Two-Column Compare", "max_header_chars": 40, "points_per_column": 4, "max_point_chars": 50},
    "QS": {"name": "Quote Spotlight", "max_quote_chars": 200, "max_attribution_chars": 50},
    "PL": {"name": "Pyramid List", "levels": 3, "max_chars_per_item": 30},
    "CP": {"name": "Circular Process", "min_circles": 4, "max_circles": 6, "max_chars_per_circle": 20},
    "TL": {"name": "Timeline", "points": 5, "max_date_chars": 15, "max_event_chars": 50},
    "DV": {"name": "Data Visualization", "max_title_chars": 60, "max_legend_items": 5, "max_legend_item_chars": 20},
    "PS": {"name": "Problem-Solution", "max_chars_per_side": 200},
    "TS": {"name": "Team Showcase", "grid": (3, 2), "max_name_chars": 30},
    "SS": {"name": "Single Statistic", "max_statistic_chars": 20, "max_context_chars": 100},
    "SWOT": {"name": "SWOT Analysis", "quadrants": 4, "max_title_chars": 20, "max_content_chars_per_quadrant": 100},
    "MM": {"name": "Mind Map", "branches": 5, "max_center_chars": 30, "max_branch_chars": 40},
    "BA": {"name": "Before and After", "max_chars_per_side": 150},
    "CL": {"name": "Checklist", "min_items": 5, "max_items": 7, "max_title_chars": 50, "max_item_chars": 60},
    "RM": {"name": "Roadmap", "milestones": 5, "max_chars_per_milestone": 30},
    "TM": {"name": "Testimonial", "max_quote_chars": 200, "max_name_chars": 30, "max_title_chars": 50},
    "CTA": {"name": "Call to Action", "max_statement_chars": 100, "max_button_chars": 20}
}

@st.cache_resource
def load_nlp_pipeline():
    return pipeline("text2text-generation", model="facebook/bart-large-cnn")

nlp = load_nlp_pipeline()

def analyze_content(text):
    summary = nlp(text, max_length=100, min_length=30, do_sample=False)[0]['generated_text']
    sentences = re.split(r'(?<=[.!?])\s+', summary)
    return summary, sentences

def select_slide_type(content, previous_types):
    if "?" in content and "BQ" not in previous_types:
        return "BQ"
    elif re.search(r'\d+%|\d+\s*(?:kg|lbs?|tons?)', content) and "SS" not in previous_types:
        return "SS"
    elif len(re.findall(r'[.!?]', content)) >= 3 and "T3P" not in previous_types:
        return "T3P"
    elif re.search(r'problem|challenge|difficulty', content, re.I) and re.search(r'solution|resolve|answer', content, re.I) and "PS" not in previous_types:
        return "PS"
    elif len(re.findall(r'[.!?]', content)) >= 3 and "3HP" not in previous_types:
        return "3HP"
    elif re.search(r'(image|picture|photo|illustration)', content, re.I) and "IC" not in previous_types:
        return "IC"
    elif re.search(r'(quote|said|according to)', content, re.I) and "QS" not in previous_types:
        return "QS"
    elif "CTA" not in previous_types:
        return "CTA"
    else:
        return "T3P"  # Default to T3P if no other type fits

def generate_slide_content(text, slide_type):
    rules = SLIDE_TYPES[slide_type]
    
    def truncate(s, max_len):
        return s[:max_len] if s else ""

    if slide_type == "3HP":
        points = re.split(r'(?<=[.!?])\s+', text)[:3]
        return [truncate(point, rules["max_chars_per_point"]) for point in points]
    elif slide_type == "T3P":
        sentences = re.split(r'(?<=[.!?])\s+', text)
        title = truncate(sentences[0], rules["max_title_chars"])
        paragraphs = [truncate(s, rules["max_paragraph_chars"]) for s in sentences[1:4]]
        return [title] + paragraphs
    elif slide_type == "BQ":
        return truncate(text, rules["max_chars"])
    elif slide_type == "SS":
        statistic = re.search(r'\d+(?:%|\s*(?:kg|lbs?|tons?))', text)
        stat = truncate(statistic.group(0), rules["max_statistic_chars"]) if statistic else "N/A"
        context = truncate(text, rules["max_context_chars"])
        return stat, context
    elif slide_type == "PS":
        parts = text.split(',', 1)
        problem = truncate(parts[0], rules["max_chars_per_side"])
        solution = truncate(parts[1], rules["max_chars_per_side"]) if len(parts) > 1 else ""
        return problem, solution
    elif slide_type == "QS":
        parts = text.split('-')
        quote = truncate(parts[0], rules["max_quote_chars"])
        attribution = truncate(parts[1], rules["max_attribution_chars"]) if len(parts) > 1 else "Anonymous"
        return quote, attribution
    elif slide_type == "CTA":
        parts = text.split('.')
        statement = truncate(parts[0], rules["max_statement_chars"])
        return statement, "Learn More"
    else:
        return truncate(text, 100)  # Default fallback

def render_slide(slide_type, content):
    if slide_type == "3HP":
        return f"""
+----------------------------------+
|                                  |
| {content[0][:10]}... | {content[1][:10]}... | {content[2][:10]}... |
|                                  |
+----------------------------------+
"""
    elif slide_type == "T3P":
        return f"""
+----------------------------------+
| {content[0][:30]}...             |
|                                  |
| • {content[1][:50]}...           |
|                                  |
| • {content[2][:50]}...           |
|                                  |
| • {content[3][:50]}...           |
+----------------------------------+
"""
    elif slide_type == "BQ":
        return f"""
+----------------------------------+
|                                  |
|   {content[:50]}...              |
|                                  |
+----------------------------------+
"""
    elif slide_type == "SS":
        return f"""
+----------------------------------+
|                                  |
|          {content[0]}            |
|                                  |
| {content[1][:50]}...             |
|                                  |
+----------------------------------+
"""
    elif slide_type == "PS":
        return f"""
+----------------------------------+
| Problem:        | Solution:      |
| {content[0][:15]}... | {content[1][:15]}... |
|                 |                |
|                 |                |
+----------------------------------+
"""
    elif slide_type == "QS":
        return f"""
+----------------------------------+
|                                  |
|  "{content[0][:50]}..."          |
|                                  |
|             - {content[1]}       |
+----------------------------------+
"""
    elif slide_type == "CTA":
        return f"""
+----------------------------------+
|                                  |
| {content[0][:50]}...             |
|                                  |
|     [{content[1]}]               |
|                                  |
+----------------------------------+
"""
    else:
        return f"""
+----------------------------------+
|                                  |
| {SLIDE_TYPES[slide_type]['name']} |
|                                  |
| {str(content)[:50]}...           |
|                                  |
+----------------------------------+
"""

st.title("Script to Layout Video")

input_text = st.text_area("Enter your script here:", height=200)

if st.button("Generate Slides"):
    if input_text:
        with st.spinner("Analyzing content and generating slides..."):
            summary, sentences = analyze_content(input_text)
            slides = []
            previous_types = []

            for sentence in sentences:
                slide_type = select_slide_type(sentence, previous_types)
                content = generate_slide_content(sentence, slide_type)
                slides.append((slide_type, content))
                previous_types.append(slide_type)

            for i, (slide_type, content) in enumerate(slides, 1):
                st.subheader(f"Slide {i}: {SLIDE_TYPES[slide_type]['name']} (Key: {slide_type})")
                st.code(render_slide(slide_type, content))
    else:
        st.warning("Please enter some text to generate slides.")

st.markdown("""
---
This app uses a pre-trained NLP model to analyze your input and generate appropriate slides.
The slide types and layouts are based on predefined rules, but the content is dynamically generated.
""")