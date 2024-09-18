import streamlit as st
import os
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips
import speech_recognition as sr
import tempfile

# Function to recognize speech from an audio file and convert it to text
def recognize_speech_from_file(audio_file_path):
    recognizer = sr.Recognizer()

    # Load the audio file
    with sr.AudioFile(audio_file_path) as source:
        st.write("Processing audio file...")
        audio = recognizer.record(source)

    try:
        # Use Google's speech recognition to transcribe the audio file
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
    # Create a black background image
    img = np.zeros((size[1], size[0], 3), dtype=np.uint8)

    # Set font parameters
    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (255, 255, 255)  # White color for text
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]

    # Position text in the center
    text_x = (size[0] - text_size[0]) // 2
    text_y = (size[1] + text_size[1]) // 2

    # Put the text on the image
    cv2.putText(img, text, (text_x, text_y), font, font_scale, color, thickness)

    return img

# Function to split numeric words into individual digits
def split_numeric_word(word):
    return [char for char in word if char.isdigit()]

# Function to map recognized words to video or image clips with English captions
def generate_combined_video(transcript, media_dir, output_video_path):
    if not os.path.exists(media_dir):
        st.write(f"Error: Media directory '{media_dir}' does not exist.")
        return
    
    clips = []

    # List files in the media directory and convert filenames to lowercase
    media_files = {file.lower(): file for file in os.listdir(media_dir)}

    # Debugging: Print files in the media directory
    st.write("Media directory files:", media_files)

    # Placeholder paths for missing media
    default_video = os.path.join(media_dir, "default_video.mp4")

    for word in transcript.split():
        word_lower = word.lower()  # Convert the word to lowercase
        video_added = False  # Flag to track if a video or image is already added for this word

        # If word contains numeric characters, split it into individual digits
        if word.isdigit():
            word_split = split_numeric_word(word)
        else:
            word_split = [word_lower]

        # Handle each part (map them to sign language video or image files)
        for part in word_split:
            for ext in ['.mp4', '.png', '.jpg', '.jpeg']:  # Add image extensions
                media_file = f"{part}{ext}"
                if media_file in media_files:
                    st.write(f"Adding media for part: {part}")

                    # Check if it's a video or an image file
                    if ext == '.mp4':
                        word_clip = VideoFileClip(os.path.join(media_dir, media_files[media_file]))
                    else:
                        word_clip = ImageClip(os.path.join(media_dir, media_files[media_file])).set_duration(2)  # Image duration is 2 seconds

                    # Create a text image using OpenCV
                    text_image = create_text_image(f"English: {part}")
                    text_clip = ImageClip(text_image).set_duration(word_clip.duration).set_position(("center", "bottom"))

                    # Combine the word_clip with the text overlay
                    combined_clip = concatenate_videoclips([word_clip.set_audio(None), text_clip], method="compose")
                    clips.append(combined_clip)
                    video_added = True
                    break  # Exit loop if a media file is found

        if not video_added:
            st.write(f"Warning: No media found for word '{word}', using default video.")
            if os.path.exists(default_video):
                word_clip = VideoFileClip(default_video)
                # Create a text image using OpenCV
                text_image = create_text_image(f"English: {word}")
                text_clip = ImageClip(text_image).set_duration(word_clip.duration).set_position(("center", "bottom"))

                # Combine the word_clip with the text overlay
                combined_clip = concatenate_videoclips([word_clip.set_audio(None), text_clip], method="compose")
                clips.append(combined_clip)

    # Combine all the clips and save the final video
    if clips:
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(output_video_path, codec="libx264", audio=False)
        st.write(f"Video created at: {output_video_path}")
    else:
        st.write("Error: No valid clips found. Video not created.")

# Streamlit UI
def main():
    st.title("Audio to Sign Language Video Generator")

    # Upload audio file
    audio_file = st.file_uploader("Upload an audio file", type=["wav", "mp3"])

    if audio_file is not None:
        # Save the uploaded file to a temporary directory
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_file.name.split('.')[-1]}") as temp_audio_file:
            temp_audio_file.write(audio_file.getbuffer())
            audio_path = temp_audio_file.name
        st.write(f"Audio file saved: {audio_path}")

        # Recognize speech from the uploaded file
        transcript = recognize_speech_from_file(audio_path)

        if transcript:
            # Set the media directory path and output video path
            media_dir = r"sih-1715"  # Adjust to your media folder
            output_video_path = r"sih-1715\output.mp4"

            # Generate the combined video with English captions only
            generate_combined_video(transcript, media_dir, output_video_path)

            # Display the video
            st.video(output_video_path)

if __name__ == "__main__":
    main() 
    # to start the functions
