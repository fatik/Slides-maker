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
            {"role": "system", "content": "You are an AI assistant that helps create concise slide content from video script text."},
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
    if re.search(r'\d+', scene_content):
        return "large_number"
    elif "!" in scene_content:
        return "centered_square"
    elif len(scene_content.split()) < 10:
        return "title_subtitle"
    elif "versus" in scene_content.lower() or "compared to" in scene_content.lower():
        return "two_column_text"
    elif "image" in scene_content.lower() or "picture" in scene_content.lower():
        return "image_caption"
    elif len(scene_content.split()) > 30:
        return "bullet_points"
    else:
        return "single_text_box"

def process_scene(scene_number, scene_content):
    layout = select_layout(scene_content)
    content = {}
    
    if layout == "large_number":
        number = re.search(r'\d+', scene_content).group()
        content = {"number": number, "caption": ai_process_content(scene_content, "Generate a brief caption (max 5 words) to accompany this number on a slide.")}
    elif layout in ["centered_square", "single_text_box"]:
        content = {"text": ai_process_content(scene_content, "Extract the key idea in 5-7 words for a slide.")}
    elif layout == "title_subtitle":
        content = {
            "title": ai_process_content(scene_content, "Create a catchy title (3-5 words) for a slide."),
            "subtitle": ai_process_content(scene_content, "Provide a brief subtitle (max 10 words) that complements the title.")
        }
    elif layout == "bullet_points":
        content = {
            "title": ai_process_content(scene_content, "Create a short title (3-5 words) for a bullet point slide."),
            "bullets": [ai_process_content(scene_content, f"Extract key point {i} (max 5 words) for a bullet on the slide.") for i in range(1, 4)]
        }
    elif layout == "image_caption":
        content = {"caption": ai_process_content(scene_content, "Create a brief image caption (max 10 words) based on this text.")}
    elif layout == "two_column_text":
        content = {
            "left": ai_process_content(scene_content, "Summarize the first half of the content in 5-7 words for the left column of a slide."),
            "right": ai_process_content(scene_content, "Summarize the second half of the content in 5-7 words for the right column of a slide.")
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

    # Draw slide border
    d.rectangle([10, 10, width-10, height-10], outline="black")

    if layout == "centered_square":
        d.rectangle([width//4, height//4, 3*width//4, 3*height//4], outline="black")
        d.text((width//2, height//2), content['text'], font=font, fill="black", anchor="mm")

    elif layout == "single_text_box":
        d.rectangle([50, 50, width-50, height-50], outline="black")
        d.text((width//2, height//2), content['text'], font=font, fill="black", anchor="mm")

    elif layout == "title_subtitle":
        d.text((width//2, 50), content['title'], font=title_font, fill="black", anchor="mt")
        d.text((width//2, 100), content['subtitle'], font=font, fill="black", anchor="mt")

    elif layout == "large_number":
        d.text((width//2, height//3), content['number'], font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100), fill="black", anchor="mm")
        d.text((width//2, 2*height//3), content['caption'], font=font, fill="black", anchor="mm")

    elif layout == "bullet_points":
        d.text((width//2, 50), content['title'], font=title_font, fill="black", anchor="mt")
        for i, bullet in enumerate(content['bullets'], 1):
            d.text((50, 100 + i*50), f"• {bullet}", font=font, fill="black")

    elif layout == "image_caption":
        d.rectangle([50, 50, width-50, height-150], outline="black")
        d.text((width//2, height-75), content['caption'], font=font, fill="black", anchor="mm")

    elif layout == "two_column_text":
        d.line([(width//2, 50), (width//2, height-50)], fill="black")
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