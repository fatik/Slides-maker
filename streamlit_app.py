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
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "Create concise slide content from video script text. No need to lay out any prefix like here's the slide, here's the explanation, here's the summary etc. Never use quotation marks unless it's a direct quote. Keep the content direct and relevant to the slide, never exceeding the length of text provided. Never mention scene numbers in the content. Provide unique content for each bullet point. Do not include your own explanations, descriptions, or reasoning about your output. Your output MUST be direct, which means no explanation or getting me ready for the output. Avoid giving preambles such as here's your output, or what the output is about. If the slide has 1-8 words and you don't have context about it or it can't be summarized further then return the original text. Your job is to supplement the narration or subtitles, not be alternative. For two-column slides, ensure the content is distinct for each column. Use bullets layout where there are multiple and many points. No meta content, what it means is no classification of the output you are making for example no need to mention if the content is a welcome message or ending note or such"},
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
        scenes.append(f"S#{i}: {sentence.strip()}")
    return scenes

def select_layout(scene_content):
    if not scene_content.strip():
        return "blank"
    elif re.search(r'\d+%', scene_content):
        return "percentage"
    elif re.search(r'\d+\s*(?:kg|lbs?|pounds?|pizzas?)', scene_content, re.IGNORECASE):
        return "large_number"
    elif "!" in scene_content or len(scene_content.split()) <= 10:
        return "big_center"
    elif any(word in scene_content.lower() for word in ["first", "then", "finally", "lastly"]):
        return "two_columns"
    elif "versus" in scene_content.lower() or "compared to" in scene_content.lower() or "but" in scene_content.lower():
        return "two_columns"
    elif len(re.findall(r'[.!?]', scene_content)) >= 3:
        return "bullet_points"
    elif "image" in scene_content.lower() or "picture" in scene_content.lower():
        return "image_caption"
    elif len(scene_content.split()) > 30:
        return "text_box"
    else:
        return "left_aligned"

def process_scene(scene_number, scene_content):
    scene_content = re.sub(r'^S#\d+:\s*', '', scene_content)
    layout = select_layout(scene_content)
    content = {"subtitle": scene_content}

    if layout == "blank":
        return f"S#{scene_number}: layout: blank, content: {content}"
    elif layout == "left_aligned":
        content["text"] = ai_process_content(scene_content, "Extract the key idea in 10-15 words.")
    elif layout == "big_center":
        content["text"] = ai_process_content(scene_content, "Extract the key idea in 3-5 words.")
    elif layout == "bullet_points" or layout == "text_box":
        content["title"] = ai_process_content(scene_content, "Create a short title (3-5 words).")
        bullet_content = ai_process_content(scene_content, "Extract 3-4 key points (7-10 words each). Format as a list with each point on a new line, prefixed with a bullet point (•).")
        content["text"] = bullet_content
    elif layout == "two_columns":
        split_content = re.split(r'\s+but\s+|\s+versus\s+|\s+compared\s+to\s+', scene_content, flags=re.IGNORECASE)
        if len(split_content) > 1:
            content["left"] = ai_process_content(split_content[0], "Summarize this part in 5-7 words.")
            content["right"] = ai_process_content(split_content[1], "Summarize this part in 5-7 words.")
        else:
            content["left"] = ai_process_content(scene_content, "Summarize the first half in 5-7 words.")
            content["right"] = ai_process_content(scene_content, "Summarize the second half in 5-7 words.")
    elif layout == "image_caption":
        content["image_caption"] = ai_process_content(scene_content, "Create a brief image caption (5-7 words).")
    elif layout == "large_number":
        number = re.search(r'\d+', scene_content)
        content["number"] = number.group() if number else ""
        content["caption"] = ai_process_content(scene_content, "Generate a brief caption (max 5 words) to accompany this number.")
    elif layout == "percentage":
        percentage = re.search(r'\d+%', scene_content)
        content["percentage"] = percentage.group() if percentage else ""
        content["text"] = ai_process_content(scene_content, "Summarize the context of this percentage in 10-15 words.")
    
    return f"S#{scene_number}: layout: {layout}, content: {content}"

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

    d.rectangle([10, 10, width-10, height-10], outline="black")

    if layout == "blank":
        pass
    elif layout == "left_aligned":
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
    elif layout == "bullet_points" or layout == "text_box":
        d.text((width//2, 30), content['title'], font=title_font, fill="black", anchor="mt")  # Moved title up
        
        bullets = content['text'].split('\n')
        available_height = height - 100  # Increased available height
        bullet_spacing = min(available_height // (len(bullets) + 1), 50)  # Cap maximum spacing
        
        y_position = 80  # Start bullets closer to the title
        for bullet in bullets:
            wrapped_bullet = textwrap.wrap(bullet, width=40)
            for j, line in enumerate(wrapped_bullet):
                if j == 0:
                    d.text((50, y_position), line, font=font, fill="black")
                else:
                    d.text((70, y_position), line, font=font, fill="black")
                y_position += 25  # Reduced line spacing within bullets
            y_position += bullet_spacing - 25  # Add spacing between bullets, but subtract the last line spacing
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
    elif layout == "image_caption":
        d.rectangle([50, 50, width-50, height-100], outline="black")
        d.text((width//2, height-50), content['image_caption'], font=font, fill="black", anchor="mm")
    elif layout == "large_number":
        d.text((width//2, height//3), content['number'], font=big_font, fill="black", anchor="mm")
        wrapped_caption = textwrap.wrap(content['caption'], width=30)
        y_text = 2*height//3
        for line in wrapped_caption:
            d.text((width//2, y_text), line, font=font, fill="black", anchor="mm")
            y_text += 30
    elif layout == "percentage":
        d.text((width//2, height//3), content['percentage'], font=big_font, fill="black", anchor="mm")
        wrapped_text = textwrap.wrap(content['text'], width=40)
        y_text = 2*height//3
        for line in wrapped_text:
            d.text((width//2, y_text), line, font=font, fill="black", anchor="mm")
            y_text += 30

    wrapped_subtitle = textwrap.wrap(content['subtitle'], width=70)
    y_subtitle = height - 40 - (len(wrapped_subtitle) - 1) * 20
    for line in wrapped_subtitle:
        d.text((width//2, y_subtitle), line, font=subtitle_font, fill="black", anchor="mm")
        y_subtitle += 20

    return img

def parse_scene(scene_text):
    match = re.match(r"S#(\d+): layout: (\w+), content: (.+)", scene_text)
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
                    
                    buf = io.BytesIO()
                    slide_image.save(buf, format='PNG')
                    byte_im = buf.getvalue()

                    st.image(byte_im, caption=f"Wireframe for S#{scene_num}")
                    st.markdown("---")
    else:
        st.warning("Please enter a script to generate slides.")

st.markdown("""
---
This app uses Groq AI to generate intelligent slide layouts and content based on your input script.
It creates concise and relevant content for each slide, different from the original subtitles,
and provides wireframe mockups for visualization.
""")