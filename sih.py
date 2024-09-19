import streamlit as st
import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip, AudioFileClip
import speech_recognition as sr
import tempfile
from datetime import datetime

# Function to recognize speech from an audio file and convert it to text
def recognize_speech_from_file(audio_file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file_path) as source:
        st.write("Processing audio file...")
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
        st.write(f"Recognized text: {text}")
        return text
    except sr.UnknownValueError:
        st.write("Google Speech Recognition could not understand the audio")
    except sr.RequestError as e:
        st.write(f"Could not request results from Google Speech Recognition service; {e}")
    return None

# Function to create an image with text using OpenCV
def create_text_image(text, size=(640, 100), font_scale=1, thickness=2):
    img = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (255, 255, 255)
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = (size[0] - text_size[0]) // 2
    text_y = (size[1] + text_size[1]) // 2
    cv2.putText(img, text, (text_x, text_y), font, font_scale, color, thickness)
    return img

# Function to map recognized words to video or image clips with audio and display sign language on the left and text on the right
def generate_combined_video(transcript, media_dir, output_video_path, audio_file_path):
    if not os.path.exists(media_dir):
        st.write(f"Error: Media directory '{media_dir}' does not exist.")
        return

    clips = []
    media_files = {file.lower(): file for file in os.listdir(media_dir)}
    st.write("Media directory files:", media_files)

    default_video = os.path.join(media_dir, "default_video.mp4")

    for word in transcript.split():
        word_lower = word.lower()
        video_added = False

        if word.isdigit():
            word_split = [char for char in word if char.isdigit()]
        else:
            word_split = [word_lower]

        for part in word_split:
            for ext in ['.mp4', '.png', '.jpg', '.jpeg']:
                media_file = f"{part}{ext}"
                if media_file in media_files:
                    st.write(f"Adding media for part: {part}")

                    if ext == '.mp4':
                        word_clip = VideoFileClip(os.path.join(media_dir, media_files[media_file]))
                    else:
                        word_clip = ImageClip(os.path.join(media_dir, media_files[media_file])).set_duration(2)

                    text_image = create_text_image(f"English: {part}", size=(320, 100))
                    text_clip = ImageClip(text_image).set_duration(word_clip.duration).set_position(("right", "center"))

                    final_width = word_clip.size[0] + text_clip.size[0]
                    final_height = max(word_clip.size[1], text_clip.size[1])
                    combined_clip = CompositeVideoClip([word_clip.set_audio(None).set_position(("left", "center")),
                                                        text_clip.set_position(("right", "center"))], size=(final_width, final_height))
                    clips.append(combined_clip)
                    video_added = True
                    break

        if not video_added:
            st.write(f"Warning: No media found for word '{word}', using default video.")
            if os.path.exists(default_video):
                word_clip = VideoFileClip(default_video)
                text_image = create_text_image(f"English: {word}", size=(320, 100))
                text_clip = ImageClip(text_image).set_duration(word_clip.duration).set_position(("right", "center"))

                combined_clip = CompositeVideoClip([word_clip.set_audio(None).set_position(("left", "center")),
                                                    text_clip.set_position(("right", "center"))], size=(word_clip.size[0] + text_clip.size[0], max(word_clip.size[1], text_clip.size[1])))
                clips.append(combined_clip)

    if clips:
        final_clip = concatenate_videoclips(clips, method="compose")

        # Combine video with audio
        audio = AudioFileClip(audio_file_path)
        final_clip = final_clip.set_audio(audio)
        
        final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac")
        st.write(f"Video created at: {output_video_path}")
    else:
        st.write("Error: No valid clips found. Video not created.")

# Streamlit UI with updated styling
def main():
    st.set_page_config(page_title="Indian Railways", page_icon="🚂", layout="wide")

    # Set custom font style, background color, and layout using CSS
    st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap'); /* Google Fonts example */
    
    .stApp {
        background-color: #4a90e2;  /* Neat blue background */
        color: black;
        height: 100vh;
    }
    
    .train-announcement {
        font-family: 'Roboto', sans-serif;
        font-size: 3em;
        font-weight: bold;
        color: white;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    
    .moving-text {
        font-family: 'Roboto', sans-serif;
        font-size: 1.8em;
        font-weight: 700;
        color: #FF4500;
        white-space: nowrap;
        overflow: hidden;
        margin-top: 0px;
        margin-bottom: 20px;
    }

    .moving-text p {
        display: inline-block;
        animation: move 9s linear infinite;
        padding-left: 100%;
    }

    @keyframes move {
        from { transform: translateX(100%); }
        to { transform: translateX(-100%); }
    }

    /* Position the date and time at the top right */
    .date-time {
        position: absolute;
        top: 10px;
        right: 20px;
        font-size: 1.2em;
        color: white;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: #F0F0F0 !important;
    }
    
    /* Sidebar menu options font color */
    .css-1d391kg * {
        color: black !important;  /* Change sidebar menu font color to black */
    }

    /* Sidebar menu icons */
    .icon-rail {
        font-size: 4em;
        padding-right: 10px;
    }

    /* Rerun and Deploy button styling */
    button[kind="primary"] {
        color: black !important;  /* Change Rerun and Deploy font color */
    }
    
    </style>
    """, unsafe_allow_html=True
)

    # Sidebar with menu options
    with st.sidebar:
        st.write("📝 **Menu**")
        st.write("🚉 Train Announcements")
        st.write("🕒 Train Schedules")
        st.write("📚 ISL Libraries")
        st.write("⚙️ Settings")

    # Display the "INDIAN RAILWAYS" heading once with custom font style
    st.markdown('<div class="train-announcement">🚂 INDIAN RAILWAYS 🚋</div>', unsafe_allow_html=True)

    # Display the moving text
    st.markdown(
        """
        <div class="moving-text">
            <p>🚂 Railway Announcement to Sign Language Converter 🚋</p>
        </div>
        """, unsafe_allow_html=True
    )

    # Get the current time and date and display it in the top right corner
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.markdown(f'<div class="date-time">{current_time}</div>', unsafe_allow_html=True)

    # Section to upload audio file
    st.write("Please upload an audio file")
    audio_file = st.file_uploader("Drag and drop file here", type=["wav", "mp3"])
    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_file.name.split('.')[-1]}") as temp_audio_file:
            temp_audio_file.write(audio_file.getbuffer())
            audio_path = temp_audio_file.name
        st.write(f"Audio file saved: {audio_path}")

        transcript = recognize_speech_from_file(audio_path)

        if transcript:
            media_dir = r"sih-1715"  # Adjust to your media folder
            output_video_path = r"sih-1715/output.mp4"
            generate_combined_video(transcript, media_dir, output_video_path, audio_path)
            st.video(output_video_path)

if __name__ == "__main__":
    main()
