import streamlit as st
import re
import requests
import time
import random
from transformers import pipeline, set_seed
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap

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
            {"role": "system", "content": "You are an AI assistant that helps create concise slide content from video script text. Never use quotation marks unless it's a direct quote. Keep the content direct and relevant to the slide. For single facts or points, don't create multiple bullets."},
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

def break_into_scenes(script):
    scenes = []
    sentences = re.split(r'(?<=[.!?])\s+', script)
    for i, sentence in enumerate(sentences, 1):
        scenes.append(f"Scene {i} {sentence.strip()}")
    return scenes

def select_layout(scene_content):
    if re.search(r'\d+\s*(?:kg|lbs?|pounds?)', scene_content, re.IGNORECASE):
        return "large_number"
    elif "!" in scene_content or len(scene_content.split()) <= 10:
        return "big_center"
    elif any(word in scene_content.lower() for word in ["first", "then", "finally", "lastly"]):
        return "timeline"
    elif "versus" in scene_content.lower() or "compared to" in scene_content.lower():
        return "comparison"
    elif len(re.findall(r'[.!?]', scene_content)) >= 3:
        return "bullet_points"
    elif "image" in scene_content.lower() or "picture" in scene_content.lower():
        return "two_columns_image"
    elif len(scene_content.split()) > 30:
        return "two_columns"
    else:
        return "left_aligned"

def process_scene(scene_number, scene_content):
    layout = select_layout(scene_content)
    content = {}
    
    if layout == "left_aligned":
        content = {"text": ai_process_content(scene_content, "Extract the key idea in 10-15 words for a left-aligned slide. Do not include any explanatory comments.")}
    elif layout == "big_center":
        content = {"text": ai_process_content(scene_content, "Extract the key idea in 3-5 words for a big, centered slide.")}
    elif layout == "bullet_points":
        content = {
            "title": ai_process_content(scene_content, "Create a short title (3-5 words) for a bullet point slide."),
            "bullets": [ai_process_content(scene_content, f"Extract unique key point {i} (5-7 words) for a bullet on the slide. Only create multiple bullets if there are distinct points in the original content.") for i in range(1, 4)]
        }
    elif layout == "two_columns":
        content = {
            "left": ai_process_content(scene_content, "Summarize the first half of the content in 10-15 words for the left column. Do not include any prompts or descriptions."),
            "right": ai_process_content(scene_content, "Summarize the second half of the content in 10-15 words for the right column. Do not include any prompts or descriptions.")
        }
    elif layout == "two_columns_image":
        content = {
            "image_caption": ai_process_content(scene_content, "Create a brief image caption (5-7 words) based on this text."),
            "text": ai_process_content(scene_content, "Summarize the main point in 10-15 words for the text column.")
        }
    elif layout == "timeline":
        content = {
            "title": ai_process_content(scene_content, "Create a short title (3-5 words) for a timeline slide."),
            "events": [ai_process_content(scene_content, f"Extract unique timeline event {i} (5-7 words). Ensure each event is distinct and relevant to the content.") for i in range(1, 4)]
        }
    elif layout == "comparison":
        content = {
            "title": ai_process_content(scene_content, "Create a short title (3-5 words) for a comparison slide."),
            "left": ai_process_content(scene_content, "Summarize the first item in 5-7 words."),
            "right": ai_process_content(scene_content, "Summarize the second item in 5-7 words.")
        }
    elif layout == "large_number":
        number = re.search(r'\d+', scene_content)
        number = number.group() if number else ""
        content = {
            "number": number,
            "caption": ai_process_content(scene_content, "Generate a brief caption (max 10 words) to accompany this number on a slide.")
        }
    
    content["subtitle"] = ' '.join(scene_content.split()[2:])  # Add original scene text as subtitle
    return f"Scene {scene_number}: layout: {layout}, content: {content}"

def process_script(scenes):
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
    subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)

    # Draw slide border
    d.rectangle([10, 10, width-10, height-10], outline="black")

    if layout == "left_aligned":
        wrapped_text = textwrap.wrap(content['text'], width=40)
        y_text = height // 2 - len(wrapped_text) * 15
        for line in wrapped_text:
            d.text((50, y_text), line, font=font, fill="black")
            y_text += 30

    elif layout == "big_center":
        wrapped_text = textwrap.wrap(content['text'], width=20)
        y_text = height // 2 - len(wrapped_text) * 30
        for line in wrapped_text:
            d.text((width//2, y_text), line, font=big_font, fill="black", anchor="mm")
            y_text += 60

    elif layout == "bullet_points":
        d.text((width//2, 50), content['title'], font=title_font, fill="black", anchor="mt")
        for i, bullet in enumerate(content['bullets'], 1):
            d.text((50, 100 + i*50), f"• {bullet}", font=font, fill="black")

    elif layout == "two_columns":
        d.line([(width//2, 50), (width//2, height-50)], fill="black")
        wrapped_left = textwrap.wrap(content['left'], width=20)
        wrapped_right = textwrap.wrap(content['right'], width=20)
        y_left = height // 2 - len(wrapped_left) * 15
        y_right = height // 2 - len(wrapped_right) * 15
        for line in wrapped_left:
            d.text((width//4, y_left), line, font=font, fill="black", anchor="mm")
            y_left += 30
        for line in wrapped_right:
            d.text((3*width//4, y_right), line, font=font, fill="black", anchor="mm")
            y_right += 30

    elif layout == "two_columns_image":
        d.line([(width//2, 50), (width//2, height-50)], fill="black")
        d.rectangle([50, 50, width//2-50, height-150], outline="black")
        d.text((width//4, height-75), content['image_caption'], font=font, fill="black", anchor="mm")
        wrapped_text = textwrap.wrap(content['text'], width=20)
        y_text = height // 2 - len(wrapped_text) * 15
        for line in wrapped_text:
            d.text((3*width//4, y_text), line, font=font, fill="black", anchor="mm")
            y_text += 30

    elif layout == "timeline":
        d.text((width//2, 50), content['title'], font=title_font, fill="black", anchor="mt")
        d.line([(50, height//2), (width-50, height//2)], fill="black")
        for i, event in enumerate(content['events']):
            x = 50 + (i * (width-100) // (len(content['events'])-1))
            d.line([(x, height//2-10), (x, height//2+10)], fill="black")
            wrapped_event = textwrap.wrap(event, width=10)
            y_event = height//2 + 30
            for line in wrapped_event:
                d.text((x, y_event), line, font=font, fill="black", anchor="mt")
                y_event += 20

    elif layout == "comparison":
        d.text((width//2, 50), content['title'], font=title_font, fill="black", anchor="mt")
        d.line([(width//2, 100), (width//2, height-50)], fill="black")
        wrapped_left = textwrap.wrap(content['left'], width=15)
        wrapped_right = textwrap.wrap(content['right'], width=15)
        y_left = height // 2 - len(wrapped_left) * 15
        y_right = height // 2 - len(wrapped_right) * 15
        for line in wrapped_left:
            d.text((width//4, y_left), line, font=font, fill="black", anchor="mm")
            y_left += 30
        for line in wrapped_right:
            d.text((3*width//4, y_right), line, font=font, fill="black", anchor="mm")
            y_right += 30

    elif layout == "large_number":
        d.text((width//2, height//3), content['number'], font=big_font, fill="black", anchor="mm")
        wrapped_caption = textwrap.wrap(content['caption'], width=30)
        y_text = 2*height//3
        for line in wrapped_caption:
            d.text((width//2, y_text), line, font=font, fill="black", anchor="mm")
            y_text += 30

    # Add subtitle at the bottom
    wrapped_subtitle = textwrap.wrap(content['subtitle'], width=70)
    y_subtitle = height - 40 - (len(wrapped_subtitle) - 1) * 20
    for line in wrapped_subtitle:
        d.text((width//2, y_subtitle), line, font=subtitle_font, fill="black", anchor="mm")
        y_subtitle += 20

    return img

def parse_scene(scene_text):
    match = re.match(r"Scene (\d+): layout: (\w+), content: (.+)", scene_text)
    if match:
        scene_num, layout, content = match.groups()
        content = eval(content)  # Be cautious with eval in production!
        return int(scene_num), layout, content
    return None

st.title("AI-Powered Slide Generator and Visualizer")

script = st.text_area("Enter your script here:", height=300)

if st.button("Generate Slides and Wireframes"):
    if script:
        with st.spinner("Breaking script into scenes..."):
            scenes = break_into_scenes(script)
            st.subheader("Scenes:")
            for scene in scenes:
                st.write(scene)
            
        with st.spinner("Processing scenes and generating intelligent slides..."):
            slides = process_script(scenes)
            
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