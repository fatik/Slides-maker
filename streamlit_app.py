import streamlit as st
from transformers import pipeline
import re

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
def load_classifier():
    return pipeline("zero-shot-classification")

@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

classifier = load_classifier()
summarizer = load_summarizer()

def classify_slide_type(text):
    candidate_labels = list(SLIDE_TYPES.keys())
    result = classifier(text, candidate_labels)
    return result['labels'][0]

def generate_slide_content(text, slide_type):
    rules = SLIDE_TYPES[slide_type]
    summary = summarizer(text, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
    
    if slide_type == "3HP":
        points = re.split(r'\. |\n', summary)[:3]
        return [point[:rules["max_chars_per_point"]] for point in points]
    elif slide_type == "T3P":
        title = summary[:rules["max_title_chars"]]
        paragraphs = re.split(r'\. |\n', summary)[1:4]
        return [title] + [p[:rules["max_paragraph_chars"]] for p in paragraphs]
    elif slide_type == "BQ":
        return summary[:rules["max_chars"]]
    # Add more slide type content generation logic here
    else:
        return summary[:100]  # Default fallback

st.title("Advanced Slide Generator")

input_text = st.text_area("Enter your script here:", height=200)

if st.button("Generate Slide"):
    if input_text:
        with st.spinner("Generating slide..."):
            slide_type = classify_slide_type(input_text)
            content = generate_slide_content(input_text, slide_type)

            st.subheader(f"Generated Slide: {SLIDE_TYPES[slide_type]['name']} (Key: {slide_type})")
            st.write(f"Content: {content}")

            # Mockup of slide (simplified for demonstration)
            st.subheader("Slide Mockup")
            st.code(f"""
+----------------------------------+
|     {SLIDE_TYPES[slide_type]['name']}
|
| {str(content)[:50]}...
|
+----------------------------------+
            """)
    else:
        st.warning("Please enter some text to generate a slide.")

st.markdown("""
---
This app uses Hugging Face's pre-trained models for classification and summarization.
It supports multiple slide types with specific rules for each.
""")