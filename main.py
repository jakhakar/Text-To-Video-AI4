# main.py

import sys
import os
import shutil
from datetime import datetime

# --- Step 1: Import your custom utility modules ---
# These modules do the heavy lifting of generating content.
from utility.video.video_search_query_generator import generate_timed_video_searches
from utility.video.background_video_generator import generate_video_assets

# --- Step 2: Import libraries for final video assembly ---
# gTTS creates the voiceover from your script.
from gtts import gTTS
# moviepy stitches the video clips and audio together.
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

# --- Configuration ---
# Define directories for output and temporary files to keep the project organized.
FINAL_VIDEO_DIR = "final_videos"
TEMP_DIR = "temp_processing_files"

# Create directories if they don't exist
os.makedirs(FINAL_VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


def create_video_from_topic(topic: str):
    """
    Orchestrates the entire video creation pipeline from a single topic.
    1. Generates a script and timed prompts.
    2. Generates individual video clips for each prompt.
    3. Generates a text-to-speech voiceover.
    4. Combines clips and audio into a final video.
    5. Cleans up temporary files.
    """
    print(f"🎬 Starting video creation process for topic: '{topic}'")
    
    # --- Part 1: Generate Timed Prompts ---
    print("\n[1/5] Generating script and video prompts...")
    try:
        # This function takes the simple topic and expands it into timed sentences,
        # then generates creative visual prompts for each sentence.
        timed_searches = generate_timed_video_searches(topic)
        if not timed_searches:
            print("❌ ERROR: Could not generate any timed search prompts. Exiting.")
            return
    except Exception as e:
        print(f"❌ ERROR during prompt generation: {e}")
        return

    # --- Part 2: Generate Video Clips ---
    print("\n[2/5] Generating individual video clips using Flux+FFmpeg...")
    # This function takes the prompts and uses Together.ai and FFmpeg
    # to create a video clip for each one.
    # The output is a list like: [[time_range, 'path/to/clip1.mp4'], ...]
    generated_clips_data = generate_video_assets(timed_searches, video_server="flux")
    
    # Filter out any clips that failed to generate
    valid_clip_paths = [path for _, path in generated_clips_data if path]
    if not valid_clip_paths:
        print("❌ ERROR: Failed to generate any video clips. Exiting.")
        return
    print(f"✅ Successfully generated {len(valid_clip_paths)} video clips.")

    # --- Part 3: Generate Voiceover Audio ---
    print("\n[3/5] Generating text-to-speech voiceover...")
    audio_path = os.path.join(TEMP_DIR, "voiceover.mp3")
    try:
        # Use the original topic/script as the text for the voiceover
        tts = gTTS(text=topic, lang='en', slow=False)
        tts.save(audio_path)
        print(f"✅ Voiceover saved to: {audio_path}")
    except Exception as e:
        print(f"❌ ERROR: Failed to generate audio: {e}")
        # We can still proceed to create a silent video
        audio_path = None

    # --- Part 4: Assemble Final Video ---
    print("\n[4/5] Assembling final video...")
    try:
        # Load all the generated video clips into moviepy
        moviepy_clips = [VideoFileClip(path) for path in valid_clip_paths]
        
        # Combine the clips into one long video
        final_clip = concatenate_videoclips(moviepy_clips, method="compose")

        # Add the voiceover if it was created successfully
        if audio_path:
            voiceover = AudioFileClip(audio_path)
            # If the audio is longer than the video, trim the audio.
            # If the video is longer, the audio will just stop playing.
            final_clip = final_clip.set_audio(voiceover.subclip(0, min(voiceover.duration, final_clip.duration)))

        # Create a unique filename for the final video
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_video_filename = f"video_{timestamp}.mp4"
        final_video_path = os.path.join(FINAL_VIDEO_DIR, final_video_filename)

        # Write the final video file to disk
        # Use a high-quality preset for better results
        final_clip.write_videofile(
            final_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=30
        )
        print(f"🎉 SUCCESS! Final video saved to: {final_video_path}")

    except Exception as e:
        print(f"❌ ERROR during final video assembly: {e}")
        return
    finally:
        # --- Part 5: Cleanup ---
        # This block runs whether assembly succeeds or fails, ensuring we clean up.
        print("\n[5/5] Cleaning up temporary files...")
        # Close all moviepy clips to release file locks before deleting
        for clip in moviepy_clips:
            clip.close()
        if 'voiceover' in locals() and voiceover:
            voiceover.close()
            
        # Delete the temporary files
        for path in valid_clip_paths:
            try:
                os.remove(path)
            except OSError as e:
                print(f"Warning: Could not remove temp clip {path}: {e}")
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
            
        # Optional: Clean the temp_images folder created by the generator
        temp_image_dir = os.path.join("generated_videos", "temp_images")
        if os.path.isdir(temp_image_dir):
            shutil.rmtree(temp_image_dir)

        print("✅ Cleanup complete.")


# This special block runs when you execute the script directly from the command line.
if __name__ == "__main__":
    # Check if a command-line argument (the topic) was provided
    if len(sys.argv) > 1:
        input_topic = sys.argv[1]
    else:
        # If no topic is provided, use a default one and inform the user.
        print("Usage: python main.py \"<your video topic or a full script>\"")
        print("\nRunning with a default example topic...")
        input_topic = "The Sahara desert is the largest hot desert in the world. It covers over 9 million square kilometers. Despite its arid conditions, it is home to a variety of wildlife, including the fennec fox and the addax antelope."
    
    # Call the main function to start the process
    create_video_from_topic(input_topic)
