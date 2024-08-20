import streamlit as st
import re

def simple_classify(text):
    # Simple classification based on keywords
    action_words = ['action', 'now', 'urgent', 'immediately', 'start']
    return "Call to Action" if any(word in text.lower() for word in action_words) else "Content"

def simple_summarize(text, max_words=20):
    # Simple summarization by taking the first few sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    summary = ' '.join(sentences[:2])  # Take first two sentences
    words = summary.split()
    return ' '.join(words[:max_words])

st.title("Simple Slide Generator")

input_text = st.text_area("Enter your script here:", height=200)

if st.button("Generate Slide"):
    if input_text:
        with st.spinner("Generating slide..."):
            # Classify the input
            slide_type = simple_classify(input_text)

            # Generate summary for slide content
            summary = simple_summarize(input_text)

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
This is a simplified slide generator using basic text processing.
For more advanced features, consider using NLP libraries and fine-tuned models.
""")