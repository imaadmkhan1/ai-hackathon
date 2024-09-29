import os
import io
import time
import random
from io import BytesIO
from PIL import Image
import base64
from lumaai import LumaAI
import requests
import tempfile
import re
import ffmpeg
import streamlit as st
import cloudinary
import cloudinary.uploader
import cloudinary.api
from moviepy.editor import VideoFileClip, concatenate_videoclips

# Configure Cloudinary
cloudinary.config( 
  cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.environ.get("CLOUDINARY_API_KEY"), 
  api_secret = os.environ.get("CLOUDINARY_API_SECRET") 
)

prompts_list = ["Very slow Zoom In while panning from left to right","Slowly Orbit Right with consistent speed",
                "Slo-mo zoom in","Slow Push In","Crane Right"]

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
        img {
        border-radius: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
    
def get_image_bytes(file_path):
    with open(file_path, 'rb') as file:
        return file.read()
        
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


# Assume you have 5 image paths
image_paths = [
    "../images/opp_1.jpg",
    "../images/opp_2.jpg",
    "../images/opp_3.jpg",
    "../images/opp_4.jpg",
    "../images/opp_5.jpg"
]


def display_images():
    # Display images in two rows with 3 images each
    for row in range(2):
        cols = st.columns(3)
        for col in range(3):
            idx = row * 3 + col
            if idx < len(image_paths):
                with cols[col]:
                    #img = Image.open(image_paths[idx])
                    #st.image(img, use_column_width=True, caption=f"Image {idx+1}")
                    resized_image_base64 = resize_images(image_paths[idx], 520, 310)
                    st.image(f"data:image/jpeg;base64,{resized_image_base64}",caption=f"Image {idx+1}")


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
        #st.text(f"Attempt {attempts}: Video not ready yet. Waiting {delay} seconds...")
        time.sleep(delay)
        
        # Implement exponential backoff with a maximum delay
        delay = min(delay * 2, max_delay)

    st.error("Max attempts reached. Video generation may have failed.")
    return None
            
def image_to_video():
    all_urls = list(st.session_state.image_urls)
    if 'video_urls' not in st.session_state:
        st.session_state.video_urls = []
    client = LumaAI(
    auth_token=os.environ.get("LUMAAI_API_KEY")
    )
    if len(all_urls)>=2:
        for url in all_urls:
            generation = client.generations.create(
                prompt=random.choice(prompts_list),
                aspect_ratio="16:9",
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
            url_placeholder.text("Waiting for Luma video to be generated...")
            video_url = poll_for_video_url(client, generation_id)
        
            if video_url:
                #url_placeholder.success(f"Video is ready! URL: {video_url}")
                url_placeholder.success(f"Luma video is ready! Getting the final video ready in a bit.")
                st.session_state.video_urls.append(video_url)
                # You can add code here to display the video or provide a download link
            else:
                url_placeholder.error("Failed to retrieve the video URL.")


def image_upload(image_path):
    if 'image_urls' not in st.session_state:
        st.session_state.image_urls = []
    image_bytes = get_image_bytes(image_path)
    uploaded_url = upload_to_cloudinary(image_bytes)
    st.session_state.image_urls.append(uploaded_url)

def extract_url(asset_string):
    asset_string = str(asset_string)
    match = re.search(r"'(https?://[^']+)'", asset_string)
    return match.group(1) if match else None

def download_video(url, output_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def get_video_info(file_path):
    probe = ffmpeg.probe(file_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    return {
        'width': int(video_stream['width']),
        'height': int(video_stream['height']),
        'duration': float(video_stream['duration'])
    }

def stitch_videos():
    all_video_urls = list(st.session_state.video_urls)    

    if len(all_video_urls) >= 2:
        with tempfile.TemporaryDirectory() as temp_dir:
            video_files = []
            
            for i, asset_string in enumerate(all_video_urls):
                url = extract_url(asset_string)
                if url:
                    try:
                        file_path = os.path.join(temp_dir, f"video_{i}.mp4")
                        download_video(url, file_path)
                        video_files.append(file_path)
                        print(f"Successfully downloaded video {i+1}")
                    except Exception as e:
                        print(f"Error downloading video: {e}")
                else:
                    print(f"Failed to extract URL from: {asset_string}")
            
            if len(video_files) >= 2:
                try:
                    output_path = "../videos/stitched_video.mp4"
                    
                    # Get info for all videos
                    video_infos = [get_video_info(file) for file in video_files]
                    
                    # Determine target resolution (use the smallest width and height)
                    target_width = min(info['width'] for info in video_infos)
                    target_height = min(info['height'] for info in video_infos)
                    
                    # Create a list to hold input files
                    inputs = []
                    for file in video_files:
                        # Resize video to target resolution
                        input_video = (
                            ffmpeg
                            .input(file)
                            .filter('scale', target_width, target_height)
                        )
                        inputs.append(input_video)
                    
                    # Concatenate videos
                    joined = ffmpeg.concat(*inputs)
                    
                    # Output to file
                    output = ffmpeg.output(joined, output_path)
                    
                    # Run FFmpeg command
                    ffmpeg.run(output, overwrite_output=True)
                    
                    print(f"Stitched video saved as {output_path}")
                except ffmpeg.Error as e:
                    print(f"FFmpeg error: {str(e)}")
                    if e.stderr:
                        print(f"FFmpeg stderr: {e.stderr.decode()}")
                except Exception as e:
                    print(f"Error during video concatenation: {str(e)}")
            else:
                print("Not enough videos were successfully downloaded to stitch.")
    else:
        print("Not enough video URLs provided.")
        
def main():
    basic_setup()
    st.markdown('<div class="custom-header">Dreamy Time Machine</div>', unsafe_allow_html=True)
    st.subheader("The Real Oppenheimer")
    display_images()
    image_options = [f"{i+1}" for i in range(len(image_paths))]
    selected_images = st.multiselect("Select up to 2 images to create a video:", image_options, max_selections=2)
    if selected_images:
        st.write("You selected:", ", ".join(selected_images))
    col1, col2 = st.columns([1, 5.5])  # Adjust column widths

    # Custom CSS to reduce button margin
    st.markdown("""
    <style>
        .stButton > button {
            margin-right: 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with col1:
        submit_button = st.button("Submit Selection")
    with col2:
        sample_video_button = st.button("Sample Video")
    
    if submit_button:
        with st.spinner():
            with st.expander("Updates"):
                for image in selected_images:
                    image_upload(image_paths[int(image)-1])
                    st.write(f"Got Image URL for {int(image)}, now moving on to generating Luma videos")
                    image_to_video()
                stitch_videos()
                
        video_file = open("../videos/stitched_video.mp4", "rb")
        video_bytes = video_file.read()
        st.video(video_bytes)
    
    if sample_video_button:
        video_file = open("../videos/sample_opp_video.mp4", "rb")
        video_bytes = video_file.read()
        st.video(video_bytes)


if __name__ == "__main__":
    main()