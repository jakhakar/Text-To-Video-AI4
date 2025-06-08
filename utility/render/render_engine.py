import os
import platform
import subprocess
import tempfile
from moviepy.editor import (AudioFileClip, CompositeVideoClip, CompositeAudioClip,
                            TextClip, VideoFileClip)
import requests

# This helper function is only needed for the 'pexel' workflow
def download_file_from_url(url, filename):
    """Downloads a file from a URL and saves it locally."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()  # Will raise an exception for bad status codes
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return False

def get_program_path(program_name):
    """Finds the path of an executable on the system."""
    try:
        search_cmd = "where" if platform.system() == "Windows" else "which"
        return subprocess.check_output([search_cmd, program_name]).decode().strip()
    except subprocess.CalledProcessError:
        print(f"WARN: '{program_name}' not found in system's PATH. MoviePy may fail for TextClips.")
        return None

def get_output_media(audio_file_path, timed_captions, background_video_data, video_server):
    """
    Renders the final video by combining background clips, audio, and captions.
    This function now handles both remote URLs (pexel) and local file paths (flux).
    """
    OUTPUT_FILE_NAME = "rendered_video.mp4"
    
    # Set up ImageMagick for MoviePy's TextClip
    magick_path = get_program_path("magick")
    if magick_path:
        os.environ['IMAGEMAGICK_BINARY'] = magick_path
    
    visual_clips = []
    temp_files_to_clean = [] # List to hold temp files for Pexels cleanup

    try:
        print(f"--- Starting render process using '{video_server}' server logic ---")
        
        # --- CORE LOGIC: Process background video assets ---
        for (t1, t2), asset_identifier in background_video_data:
            video_clip_path = None

            if asset_identifier is None:
                print(f"Skipping empty clip for time {t1}-{t2}s.")
                continue

            # --- This is the main conditional logic ---
            if video_server == "pexel":
                print(f"Downloading Pexel clip from URL for {t1}-{t2}s...")
                # Create a temporary file to store the downloaded video
                temp_video_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
                if download_file_from_url(asset_identifier, temp_video_file):
                    video_clip_path = temp_video_file
                    temp_files_to_clean.append(video_clip_path) # Mark for cleanup
                else:
                    print(f"Failed to download video for time {t1}-{t2}s.")

            elif video_server == "flux":
                print(f"Using local Flux clip '{os.path.basename(asset_identifier)}' for {t1}-{t2}s...")
                # The asset_identifier is already the local file path. No download needed.
                video_clip_path = asset_identifier
            
            # --- Common logic to create the MoviePy clip ---
            if video_clip_path and os.path.exists(video_clip_path):
                clip = VideoFileClip(video_clip_path)
                # Ensure the clip has the correct duration for its segment
                clip = clip.subclip(0, t2 - t1)
                clip = clip.set_start(t1).set_duration(t2 - t1)
                # Resize to a standard format like 1080p if needed
                clip = clip.resize(height=1080)
                visual_clips.append(clip)

        # --- Process captions (this logic is unchanged) ---
        print("Adding text captions...")
        for (t1, t2), text in timed_captions:
            text_clip = TextClip(
                txt=text,
                fontsize=70,
                color="white",
                stroke_width=2,
                stroke_color="black",
                method="caption", # 'caption' is better for wrapping text
                size=(1000, None) # Set width for text wrapping
            )
            text_clip = text_clip.set_start(t1).set_duration(t2 - t1)
            text_clip = text_clip.set_position(("center", "bottom"))
            visual_clips.append(text_clip)

        if not visual_clips:
            print("ERROR: No visual clips were created. Aborting render.")
            return None

        # --- Composite video and audio ---
        print("Compositing video clips...")
        final_video = CompositeVideoClip(visual_clips, size=(1920, 1080))
        
        print("Adding audio track...")
        audio_clip = AudioFileClip(audio_file_path)
        final_video.audio = audio_clip
        final_video.duration = audio_clip.duration

        # --- Write the final file ---
        print(f"Writing final video to '{OUTPUT_FILE_NAME}'...")
        final_video.write_videofile(
            OUTPUT_FILE_NAME, 
            codec='libx264', 
            audio_codec='aac', 
            fps=30, # Increased FPS for smoother animation
            preset='medium', # 'medium' is a good balance of speed/quality
            threads=os.cpu_count() # Use all available CPU cores
        )
        print("--- Render complete! ---")
        return OUTPUT_FILE_NAME

    finally:
        # --- ROBUST CLEANUP ---
        # This block will run even if the rendering fails, ensuring no temp files are left.
        # This only cleans up files downloaded from Pexels. Flux files are permanent.
        if temp_files_to_clean:
            print("Cleaning up temporary video files...")
            for f in temp_files_to_clean:
                try:
                    os.remove(f)
                    print(f"  - Removed {f}")
                except OSError as e:
                    print(f"Error removing temp file {f}: {e}")
