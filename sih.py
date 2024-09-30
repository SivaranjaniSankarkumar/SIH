import streamlit as st
import os
import cv2
import base64
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

# Function to resize video clips to a standard size
def resize_clip(clip, target_size=(640, 480)):
    return clip.resize(newsize=target_size)

# Function to generate the combined ISL video with sign language on the left and text on the right
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

                    try:
                        if ext == '.mp4':
                            word_clip = VideoFileClip(os.path.join(media_dir, media_files[media_file]))
                            word_clip = resize_clip(word_clip) # Resize to a standard size
                        else:
                            word_clip = ImageClip(os.path.join(media_dir, media_files[media_file])).set_duration(2)

                        # Adjust text image size based on the video clip
                        text_image = create_text_image(f"English: {part}", size=(320, 100))
                        text_clip = ImageClip(text_image).set_duration(word_clip.duration).set_position(("right", "center"))

                        # Combine video clip and text clip
                        combined_clip = CompositeVideoClip([word_clip.set_audio(None).set_position(("left", "center")),
                                                            text_clip.set_position(("right", "center"))],
                                                           size=(960, 480)) # Adjust size to fit both clips
                        clips.append(combined_clip)
                        video_added = True
                    except Exception as e:
                        st.write(f"Error loading media for {part}: {e}")
                    break

        if not video_added:
            st.write(f"Warning: No media found for word '{word}', using default video.")
            if os.path.exists(default_video):
                try:
                    word_clip = VideoFileClip(default_video)
                    word_clip = resize_clip(word_clip) # Resize the default video

                    text_image = create_text_image(f"English: {word}", size=(320, 100))
                    text_clip = ImageClip(text_image).set_duration(word_clip.duration).set_position(("right", "center"))

                    combined_clip = CompositeVideoClip([word_clip.set_audio(None).set_position(("left", "center")),
                                                        text_clip.set_position(("right", "center"))], size=(960, 480))
                    clips.append(combined_clip)
                except Exception as e:
                    st.write(f"Error loading default video: {e}")

    if clips:
        try:
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip = final_clip.resize(newsize=(960, 480)) # Ensure final video is at a standard size

            # Combine video with audio
            audio = AudioFileClip(audio_file_path)
            final_clip = final_clip.set_audio(audio)

            final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac")
            st.write(f"Video created at: {output_video_path}")
        except Exception as e:
            st.write(f"Error during video creation: {e}")
    else:
        st.write("Error: No valid clips found. Video not created.")


def get_image_as_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception as e:
        st.write(f"Error loading image: {e}")
        return None

# Correct path to your local image (modify this path as needed)
image_path = "dimmer_brightness_railway_station.png""



# Get the base64 encoded image
img_base64 = get_image_as_base64(image_path)

if img_base64:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{img_base64}");
            background-size: cover;
            color: black;
            height: 100vh;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.write("Failed to load the image.")



# Streamlit UI for uploading and processing audio
def main():
    st.markdown('<h1 class="title">🚉 Indian Railways ISL Video & Text Generator</h1>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### About ISL")
        # Scrollable tab content for manual scrolling
        st.markdown("""
        <div class="scrolling-container">
            <p>Welcome to our real-time railway announcement translation app, designed to bridge communication gaps by converting railway announcements into Indian Sign Language (ISL). This innovative solution processes audio announcements, transcribes them into text, and maps each word to corresponding ISL signs, which are then displayed as videos. With a user-friendly interface, passengers who are deaf or hard of hearing can easily follow important updates such as train arrivals, departures, and platform changes. Our system integrates audio, text, and visual media seamlessly, offering an inclusive travel experience for everyone.</p>
        </div>
        """, unsafe_allow_html=True)
    # Set custom font style, background color, and layout using CSS
    st.markdown(
    """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        
        /* Title Style */
        .title {
            color:#f4d03f; /* Change this to your desired color */
            font-size: 36px; /* You can adjust the font size as needed */
            font-weight: bold; /* Makes the title bold */
            text-align: center; /* Center the title */
            text-shadow: 
                 1px 1px 0px #000, /* Bottom left shadow */
                 2px 2px 0px #000, /* Bottom left deeper shadow */
                 3px 3px 0px #000, /* Bottom left deepest shadow */
                 4px 4px 0px #000, /* Further shadow depth */
                 5px 5px 10px rgba(0, 0, 0, 0.5); /* Slight blur for realism */
        }

        /* Tab Style */
        .stTabs > div > div {
            font-weight: bold;
            color: white; /* Change this to your desired tab text color */
        }

        /* Background and text color for the main app */
        .css-1d391kg {
            background-color: rgba(240, 240, 240, 1.0) !important; /* Semi-transparent background for text readability */
        }

        .css-1d391kg * {
            color: black !important;
        }

        

        /* Button and Icon Styles */
        .icon-rail {
            font-size: 4em;
            padding-right: 10px;
        }

        button[kind="primary"] {
            color: black !important;
        }

        /* CSS for moving text */
        .moving-text {
            overflow: hidden;
            white-space: nowrap;
            box-sizing: border-box;
        }
        
        /* Custom style for Train Schedules subheader */
        .custom-subheader-train {
            color: white; /* Set the subheader color to white */
            font-size: 24px; /* Adjust the font size */
            font-weight: bold; /* Make the text bold */
            margin-bottom: 10px;
        }

        /* Custom style for recognized text */
        .custom-recognized-text {
            color: white; /* Set the recognized text color to white */
            font-size: 18px; /* Adjust the font size */
            font-weight: normal; /* Set normal font weight */
            margin-top: 10px;
        }

        /* Custom style for "No transcript available" message */
        .custom-no-transcript {
            color: white; /* Set the color to white */
            font-size: 18px; /* Adjust the font size */
            font-weight: normal;
            margin-top: 10px;
        }
        /* Custom style for Train Schedules subheader */
        .custom-subheader-train {
            color: white; /* Set the subheader color to white */
            font-size: 24px; /* Adjust the font size */
            font-weight: bold; /* Make the text bold */
            margin-bottom: 10px;
        }

        /* Custom style for recognized text */
        .custom-recognized-text {
            color: white; /* Set the recognized text color to white */
            font-size: 18px; /* Adjust the font size */
            font-weight: normal; /* Set normal font weight */
            margin-top: 10px;
        }
        /* Custom style for "No transcript available" message */
        .custom-no-transcript {
            color: white; /* Set the color to white */
            font-size: 18px; /* Adjust the font size */
            font-weight: normal;
            margin-top: 10px;
        }
        
        /* Custom style for the tab names */
        .stTabs [role="tab"] {
            color: white !important; /* Set the text color to white */
            font-size: 18px; /* Adjust the font size if needed */
            font-weight: bold; /* Make the tab names bold */
            text-align: center; /* Optionally center the text */
        }

        /* Style for the tab container */
        .stTabs {
            background-color: rgba(0, 0, 0, 0.7); /* Optional: Set a background color for the tabs */
        }
        
        
        /* Custom style for Train Announcements to ISL subheader */
        .custom-subheader-isl {
            color: white; /* Set the subheader color to white */
            font-size: 24px; /* Adjust the font size */
            font-weight: bold; /* Make the text bold */
            text-align: center; /* Center the text */
        }
        
        /* Custom style for subheader */
        .custom-subheader {
            color: white; /* Change this to your desired color */
            font-size: 24px; /* Adjust the font size */
            font-weight: bold; /* Make the text bold */
            text-align: left; /* Align text left, center or right as needed */
            margin-bottom: 10px;
        }

        /* Custom style for the file uploader text */
        .custom-upload-text {
            color: white; /* Change this to your desired color */
            font-size: 16px; /* Adjust the font size */
            font-weight: bold; /* Optional: make the text bold */
            margin-bottom: 10px;
        }

        .moving-text p {
            display: inline-block;
            animation: move-text 10s linear infinite;
            padding-left: 100%;
            color: violet;
            font-weight: bold;  
        }

        @keyframes move-text {
            0% { transform: translate(0); }
            100% { transform: translate(-100%); }
        }
        </style>
        """, unsafe_allow_html=True
    )

    
    # Create a div with moving text
    st.markdown(
        """
        <div class="moving-text">
            <p>🚂 Railway Announcement to Sign Language Converter 🚋</p>
        </div>
        """, unsafe_allow_html=True
    )
   
    tab1, tab2, tab3, tab4 = st.tabs(["Train Announcements", "Train Schedules", "ISL Libraries", "ISL video"])

    with tab1:
    # Custom subheader for Train Announcements
     st.markdown('<h2 class="custom-subheader">🎤 Train Announcements</h2>', unsafe_allow_html=True)
     st.markdown('<p class="custom-upload-text">Upload train announcement audio file:</p>', unsafe_allow_html=True)

    # File uploader
     uploaded_file = st.file_uploader("", type=["wav", "mp3", "m4a"])

     if uploaded_file is not None:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            temp_file_path = temp_file.name

        # Store the file path in session state
        st.session_state['audio_file'] = temp_file_path

        # Display the audio file (audio player) only in tab1
        st.audio(uploaded_file, format='audio/wav')

        # Recognize speech without displaying the recognized text in tab1
        recognized_text = recognize_speech_from_file(temp_file_path)
        if recognized_text:
            st.session_state['transcript'] = recognized_text  # Store transcript for later use in tab2

    with tab2:
    # Custom subheader for Train Schedules
     st.markdown('<h2 class="custom-subheader-train">🚆 Train Schedules</h2>', unsafe_allow_html=True)

    # Display recognized text or "No transcript available" message in white
     if 'transcript' in st.session_state:
        st.markdown(f'<p class="custom-recognized-text">Recognized Train Schedule Text: {st.session_state["transcript"]}</p>', unsafe_allow_html=True)
     else:
        st.markdown('<p class="custom-no-transcript">No transcript available. Please upload an announcement first.</p>', unsafe_allow_html=True)
        
    with tab3:
        st.subheader("📚 ISL Libraries")

    # Set the media directory path
        media_dir = r"C:\Users\ADMIN\OneDrive\Desktop\sih-1715" # Adjust your media folder path

    # Check if the directory exists
        if os.path.exists(media_dir):
           st.write("Available ISL Media Files:")
        
        # List all media files in the directory (image and video)
           media_files = [f for f in os.listdir(media_dir) if f.endswith(('.jpg', '.jpeg', '.png', '.gif', '.mp4'))]

           if media_files:
            # Create a search bar (selectbox) to choose a file
              selected_file = st.selectbox("Search for a media file", media_files)
            
            # Once a file is selected, display the corresponding image or video
              if selected_file:
                # Full path of the selected file
                 selected_file_path = os.path.join(media_dir, selected_file)
                
                # Check the file extension and display accordingly
                 if selected_file.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    # Display the image
                    st.image(selected_file_path, caption=f"Displaying: {selected_file}", use_column_width=True)
                 elif selected_file.endswith('.mp4'):
                    # Display the video
                    st.video(selected_file_path) # Use st.video() for mp4 files
            
        else:
         st.write("Media directory not found.")

    with tab4:
        # Custom subheader for Train Announcement to ISL
        st.markdown('<h2 class="custom-subheader-isl">🎬 Train announcement to ISL</h2>', unsafe_allow_html=True)

        if 'transcript' in st.session_state and 'audio_file' in st.session_state:
            # Custom "Generating ISL Video..." text
            st.markdown('<p class="custom-generating-text">Generating ISL Video...</p>', unsafe_allow_html=True)

            # Define the path to save the video
            output_video_path = os.path.join(tempfile.gettempdir(), f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
            media_dir = r"C:\Users\ADMIN\OneDrive\Desktop\sih-1715" # Adjust your media folder path

            # Call your function to generate video
            generate_combined_video(st.session_state['transcript'], media_dir, output_video_path, st.session_state['audio_file'])
            
            # Display the generated video
            st.video(output_video_path)
if __name__ == "__main__":
    main()
