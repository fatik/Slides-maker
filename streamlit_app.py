import streamlit as st
from transformers import pipeline

# Use Streamlit's caching to load models efficiently
@st.cache_resource
def load_classifier():
    return pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

# Load models
classifier = load_classifier()
summarizer = load_summarizer()

st.title("Quick Slide Generator")

input_text = st.text_area("Enter your script here:", height=200)

if st.button("Generate Slide"):
    if input_text:
        with st.spinner("Generating slide..."):
            # Classify the input
            classification = classifier(input_text)[0]
            slide_type = "Content" if classification['label'] == 'POSITIVE' else "Call to Action"

            # Generate summary for slide content
            summary = summarizer(input_text, max_length=50, min_length=10, do_sample=False)[0]['summary_text']

            # Display results
            st.subheader("Generated Slide")
            st.write(f"Slide Type: {slide_type}")
            st.write(f"Slide Content: {summary}")

            # Mockup of slide
            st.subheader("Slide Mockup")
            if slide_type == "Content":
                st.markdown(f"""
                ```
                +----------------------------------+
                |           Content Slide          |
                |                                  |
                | {summary[:50]}...                |
                |                                  |
                +----------------------------------+
                ```
                """)
            else:
                st.markdown(f"""
                ```
                +----------------------------------+
                |        Call to Action Slide      |
                |                                  |
                | {summary[:50]}...                |
                |                                  |
                |          [Take Action Now]       |
                +----------------------------------+
                ```
                """)
    else:
        st.warning("Please enter some text to generate a slide.")

st.markdown("""
---
This app uses Hugging Face's pre-trained models:
- DistilBERT for text classification
- BART for text summarization

For a production system, you'd want to fine-tune these models on your specific slide data.
""")