import streamlit as st
import re
import requests
import time
import random
from transformers import pipeline, set_seed
from PIL import Image, ImageDraw, ImageFont
import io

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

# Set up Groq client
GROQ_API_KEY = st.secrets["groq_api_key"]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn", device=-1)

summarizer = load_summarizer()
set_seed(42)

def ai_process_content(text, instruction, max_retries=5):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "system", "content": "You are an AI assistant that helps create concise slide content from video script text. Never provide multiple options or use quotation marks unless it's a direct quote."},
            {"role": "user", "content": f"Based on this text: '{text}', {instruction}"}
        ]
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(GROQ_API_URL, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            if attempt == max_retries - 1:
                st.warning(f"Failed to process content after {max_retries} attempts. Using fallback method.")
                return summarizer(text, max_length=20, min_length=5, do_sample=False)[0]['summary_text']
            time.sleep(2 ** attempt + random.random())  # Exponential backoff

def select_layout(scene_content):
    layouts = [
        "left_aligned", "big_center", "bullet_points", "blank", 
        "two_columns", "two_columns_image", "timeline", "comparison"
    ]
    return random.choice(layouts)

def process_scene(scene_number, scene_content):
    layout = select_layout(scene_content)
    content = {}
    
    if layout == "left_aligned":
        content = {"text": ai_process_content(scene_content, "Extract the key idea in 10-15 words for a left-aligned slide.")}
    elif layout == "big_center":
        content = {"text": ai_process_content(scene_content, "Extract the key idea in 3-5 words for a big, centered slide.")}
    elif layout == "bullet_points":
        content = {
            "title": ai_process_content(scene_content, "Create a short title (3-5 words) for a bullet point slide."),
            "bullets": [ai_process_content(scene_content, f"Extract key point {i} (5-7 words) for a bullet on the slide.") for i in range(1, 4)]
        }
    elif layout == "blank":
        content = {"text": ""}
    elif layout == "two_columns":
        content = {
            "left": ai_process_content(scene_content, "Summarize the first half of the content in 10-15 words for the left column."),
            "right": ai_process_content(scene_content, "Summarize the second half of the content in 10-15 words for the right column.")
        }
    elif layout == "two_columns_image":
        content = {
            "image_caption": ai_process_content(scene_content, "Create a brief image caption (5-7 words) based on this text."),
            "text": ai_process_content(scene_content, "Summarize the main point in 10-15 words for the text column.")
        }
    elif layout == "timeline":
        content = {
            "title": ai_process_content(scene_content, "Create a short title (3-5 words) for a timeline slide."),
            "events": [ai_process_content(scene_content, f"Extract timeline event {i} (5-7 words).") for i in range(1, 4)]
        }
    elif layout == "comparison":
        content = {
            "title": ai_process_content(scene_content, "Create a short title (3-5 words) for a comparison slide."),
            "left": ai_process_content(scene_content, "Summarize the first item in 5-7 words."),
            "right": ai_process_content(scene_content, "Summarize the second item in 5-7 words.")
        }
    
    return f"Scene {scene_number}: layout: {layout}, content: {content}"

def process_script(script):
    scenes = re.split(r'Scene \d+', script)
    scenes = [scene.strip() for scene in scenes if scene.strip()]
    results = []
    for i, scene in enumerate(scenes, 1):
        results.append(process_scene(i, scene))
        time.sleep(1)  # Add a small delay between processing scenes
    return results

def create_slide(layout, content, width=800, height=600):
    img = Image.new('RGB', (width, height), color='white')
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    big_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)

    # Draw slide border
    d.rectangle([10, 10, width-10, height-10], outline="black")

    if layout == "left_aligned":
        d.text((50, height//2), content['text'], font=font, fill="black", anchor="lm")

    elif layout == "big_center":
        d.text((width//2, height//2), content['text'], font=big_font, fill="black", anchor="mm")

    elif layout == "bullet_points":
        d.text((width//2, 50), content['title'], font=title_font, fill="black", anchor="mt")
        for i, bullet in enumerate(content['bullets'], 1):
            d.text((50, 100 + i*50), f"• {bullet}", font=font, fill="black")

    elif layout == "blank":
        pass  # Leave the slide blank

    elif layout == "two_columns":
        d.line([(width//2, 50), (width//2, height-50)], fill="black")
        d.text((width//4, height//2), content['left'], font=font, fill="black", anchor="mm")
        d.text((3*width//4, height//2), content['right'], font=font, fill="black", anchor="mm")

    elif layout == "two_columns_image":
        d.line([(width//2, 50), (width//2, height-50)], fill="black")
        d.rectangle([50, 50, width//2-50, height-150], outline="black")
        d.text((width//4, height-75), content['image_caption'], font=font, fill="black", anchor="mm")
        d.text((3*width//4, height//2), content['text'], font=font, fill="black", anchor="mm")

    elif layout == "timeline":
        d.text((width//2, 50), content['title'], font=title_font, fill="black", anchor="mt")
        d.line([(50, height//2), (width-50, height//2)], fill="black")
        for i, event in enumerate(content['events']):
            x = 50 + (i * (width-100) // (len(content['events'])-1))
            d.line([(x, height//2-10), (x, height//2+10)], fill="black")
            d.text((x, height//2+30), event, font=font, fill="black", anchor="mt")

    elif layout == "comparison":
        d.text((width//2, 50), content['title'], font=title_font, fill="black", anchor="mt")
        d.line([(width//2, 100), (width//2, height-50)], fill="black")
        d.text((width//4, height//2), content['left'], font=font, fill="black", anchor="mm")
        d.text((3*width//4, height//2), content['right'], font=font, fill="black", anchor="mm")

    return img

def parse_scene(scene_text):
    match = re.match(r"Scene (\d+): layout: (\w+), content: (.+)", scene_text)
    if match:
        scene_num, layout, content = match.groups()
        content = eval(content)  # Be cautious with eval in production!
        return int(scene_num), layout, content
    return None

st.title("AI-Powered Slide Generator and Visualizer")

script = st.text_area("Enter your script here (use 'Scene X' to denote scene breaks):", height=300)

if st.button("Generate Slides and Wireframes"):
    if script:
        with st.spinner("Processing script and generating intelligent slides..."):
            slides = process_script(script)
            
            for slide in slides:
                st.markdown(slide)
                
                parsed = parse_scene(slide)
                if parsed:
                    scene_num, layout, content = parsed
                    slide_image = create_slide(layout, content)
                    
                    # Convert to bytes
                    buf = io.BytesIO()
                    slide_image.save(buf, format='PNG')
                    byte_im = buf.getvalue()

                    st.image(byte_im, caption=f"Wireframe for Scene {scene_num}")
                    st.markdown("---")
    else:
        st.warning("Please enter a script to generate slides.")

st.markdown("""
---
This app uses Groq AI to generate intelligent slide layouts and content based on your input script.
It creates concise and relevant content for each slide, different from the original subtitles,
and provides wireframe mockups for visualization.
""")