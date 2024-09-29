import streamlit as st
from PIL import Image
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Configure Cloudinary
cloudinary.config( 
  cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.environ.get("CLOUDINARY_API_KEY"), 
  api_secret = os.environ.get("CLOUDINARY_API_SECRET") 
)

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
            background-color: #8134AF;
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

def image_upload():
    st.subheader("Image Upload")
    
    if 'uploaded_images' not in st.session_state:
        st.session_state.uploaded_images = []
    if 'image_urls' not in st.session_state:
        st.session_state.image_urls = {}


    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"], key="uploader")
    if uploaded_file is not None and st.button("Add Image"):
        if len(st.session_state.uploaded_images) < 3:
            image_bytes = uploaded_file.read()
            
            # Upload to Cloudinary
            cdn_url = upload_to_cloudinary(image_bytes)
            
            st.session_state.uploaded_images.append((image_bytes, cdn_url))
            filename = uploaded_file.name
            st.session_state.image_urls[filename] = cdn_url
            st.success(f"Image {len(st.session_state.uploaded_images)} added and uploaded to CDN successfully!")
        else:
            st.warning("Maximum 3 images allowed. Please remove an image to add a new one.")
            

    for i, (image, cdn_url) in enumerate(st.session_state.uploaded_images):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.image(BytesIO(image), caption=f"Image {i+1}", use_column_width=True)
        with col2:
            st.text_input(f"CDN Link for Image {i+1}", value=cdn_url, key=f"link_{i}")
        with col3:
            if st.button(f"Remove Image {i+1}"):
                st.session_state.uploaded_images.pop(i)
                st.experimental_rerun()

    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    progress = len(st.session_state.uploaded_images) / 3
    progress_bar.progress(progress)
    progress_text.text(f"{len(st.session_state.uploaded_images)}/3 images uploaded")



def main():
    basic_setup()
    st.markdown('<div class="custom-header">Dreamy Time Machine</div>', unsafe_allow_html=True)
    image_upload()

if __name__ == "__main__":
    main()