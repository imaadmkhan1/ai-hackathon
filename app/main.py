import os
import io
import time
from io import BytesIO
from PIL import Image
import base64
from lumaai import LumaAI
import requests
import tempfile

from moviepy.editor import VideoFileClip, concatenate_videoclips
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

def basic_setup():
    # Remove default header and footer
    st.set_page_config(page_title="Dreamy Time Machine", page_icon="⏳", layout="wide", initial_sidebar_state="collapsed")
    # Custom CSS to remove default header and footer, and create the custom header
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .custom-header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background-color: #894028;
            color: white;
            text-align: center;
            padding: 15px 0;
            font-size: 24px;
            font-weight: bold;
            z-index: 999;
        }
        .block-container {
            padding-top: 50px;
        }
        </style>
        """, unsafe_allow_html=True)

def upload_to_cloudinary(image_bytes):
    result = cloudinary.uploader.upload(image_bytes)
    return result['secure_url']

def poll_for_video_url(client, generation_id, max_attempts=60, initial_delay=5, max_delay=60):
    attempts = 0
    delay = initial_delay

    while attempts < max_attempts:
        generation = client.generations.get(id=generation_id)
        
        if generation.assets:
            return generation.assets

        attempts += 1
        st.text(f"Attempt {attempts}: Video not ready yet. Waiting {delay} seconds...")
        time.sleep(delay)
        
        # Implement exponential backoff with a maximum delay
        delay = min(delay * 2, max_delay)

    st.error("Max attempts reached. Video generation may have failed.")
    return None


def image_to_video():
    all_urls = list(st.session_state.image_urls.values())
    if 'video_urls' not in st.session_state:
        st.session_state.video_urls = []
    client = LumaAI(
    auth_token=os.environ.get("LUMAAI_API_KEY")
    )
    if len(all_urls)>=2:
        for url in all_urls:
            generation = client.generations.create(
                prompt="Zoom In",
                aspect_ratio="9:16",
                keyframes={
                    "frame0": {
                        "type": "image",
                        "url": url
                    }
                }
            )
            generation_id = generation.id
            # Create a placeholder for the video URL
            url_placeholder = st.empty()
        
            # Start polling
            url_placeholder.text("Waiting for video to be generated...")
            video_url = poll_for_video_url(client, generation_id)
        
            if video_url:
                url_placeholder.success(f"Video is ready! URL: {video_url}")
                st.session_state.video_urls.append(video_url)
                # You can add code here to display the video or provide a download link
            else:
                url_placeholder.error("Failed to retrieve the video URL.")

def stitch_videos():
    all_video_urls = list(st.session_state.video_urls)    
    # Create a temporary directory to store downloaded videos
    with tempfile.TemporaryDirectory() as temp_dir:
        video_clips = []
        
        # Download videos from the URLs
        for i, url in enumerate(all_video_urls):
            response = requests.get(url)
            if response.status_code == 200:
                file_path = os.path.join(temp_dir, f"video_{i}.mp4")
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                # Create VideoFileClip object and add to list
                clip = VideoFileClip(file_path)
                video_clips.append(clip)
            else:
                print(f"Failed to download video from {url}")
        
        # Stitch videos together using moviepy
        if video_clips:
            final_clip = concatenate_videoclips(video_clips)
            
            # Define output path (you may want to customize this)
            output_path = "stitched_video.mp4"
            
            # Write the final video
            final_clip.write_videofile(output_path)
            
            # Close all clips
            final_clip.close()
            for clip in video_clips:
                clip.close()
            
            print(f"Stitched video saved as {output_path}")
        else:
            print("No videos were successfully downloaded and stitched.")

def resize_images(image_path, width, height):
    # Open the image
    img = Image.open(image_path)
    # Resize the image
    resized_img = img.resize((width, height))
    # Convert the resized image to bytes
    img_byte_arr = io.BytesIO()
    resized_img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    # Encode the bytes to base64
    base64_encoded = base64.b64encode(img_byte_arr).decode('utf-8')
    return base64_encoded
    
def main():
    basic_setup()
    st.markdown('<div class="custom-header">Dreamy Time Machine</div>', unsafe_allow_html=True)
    #st.subheader("Dreamy Time Machine")
    st.markdown("""
    <style>
    .big-font {
        font-size:20px !important;
    }
    .brown-text {
        color: #894028;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<p class="big-font"><b>Step into the Past with Dreamy Time Machine!</b></br>Ever wished you could relive a moment in history? With <span class="brown-text">Dreamy Time Machine</span>, you can! Using our platform, you can create stunning videos in just minutes. Experience the magic of time travel and feel as though you’re truly there, witnessing unforgettable moments firsthand. Unleash your imagination and let history come alive—one video at a time!</p>', unsafe_allow_html=True)

        #st.markdown("""
        #<style>
        #[data-testid="stImage"] {
        #    text-align: center;
        #    display: block;
        #    margin-left: auto;
        #    margin-right: auto;
        #    width: 100%;
        #}
        #</style>
        #""", unsafe_allow_html=True)

        #resized_image_base64 = resize_images('../images/anant_1.jpeg', 256, 256)
        #st.image(f"data:image/jpeg;base64,{resized_image_base64}")
        #st.image("")

    card_style = """
    {
    border: 1px groove #52546a;
    border-radius: 10px;
    padding-left: 25px;
    padding-top: 10px;
    padding-bottom: 10px;
    box-shadow: -6px 8px 20px 1px #00000052;  }
    """
    col1, col2,col3 = st.columns(3)
    with col1:
        with stylable_container("Card1",
                                css_styles="""
                                img {
                                border-radius: 20px;
                                }"""
                               ):
            #st.image("https://cdn.britannica.com/01/150101-050-810CE9A9/soldiers-German-part-Soviet-Union-Operation-Barbarossa-1941.jpg?w=500&h=500")
            resized_image_base64 = resize_images('../images/mahatma-gandhi.jpg', 520, 310)
            st.image(f"data:image/jpeg;base64,{resized_image_base64}")
            st.markdown("<div style='text-align: center;'><a href='/indian_independence' target='_self'>Indian Independence Struggle</a></div>", unsafe_allow_html=True)    
    st.write("")
    with col2:
        with stylable_container("Card1",
                                css_styles="""
                                img {
                                border-radius: 20px;
                                }"""
                               ):
            resized_image_base64 = resize_images('../images/oppenheimer.jpg', 520, 310)
            st.image(f"data:image/jpeg;base64,{resized_image_base64}")
            st.markdown("<div style='text-align: center;'><a href='/oppenheimer' target='_self'>The Real Oppenheimer</a></div>", unsafe_allow_html=True)    
    st.write("")
    with col3:
        with stylable_container("Card1",
                                css_styles="""
                                img {
                                border-radius: 20px;
                                }"""
                               ):
            resized_image_base64 = resize_images('../images/personal_history_2.jpeg', 520, 310)
            st.image(f"data:image/jpeg;base64,{resized_image_base64}")
            st.markdown("<div style='text-align: center;'><a href='/personal_events' target='_self'>Personal History</a></div>", unsafe_allow_html=True)    
    st.write("")

    st.markdown('<p class="big-font">Want other historical events? Let us know or click <a href="/custom_event" target="_self">here</a></p>', unsafe_allow_html=True) 
    #image_upload()
    #image_to_video()
    #stitch_videos()
    
if __name__ == '__main__':
    main()