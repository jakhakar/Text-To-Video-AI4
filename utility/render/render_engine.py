# utility/render/render_engine.py

import os
from moviepy.editor import (VideoFileClip, AudioFileClip, TextClip,
                            CompositeVideoClip, concatenate_videoclips)

# --- 1. CORRECT FUNCTION NAME AND SIGNATURE ---
# This function is now correctly named 'render_video' and accepts the
# arguments that main.py provides.
def render_video(scenes: list, audio_path: str, output_path: str):
    """
    Renders the final video by combining video clips, adding captions, and syncing audio.
    This is a pure rendering function; it assumes all assets have been prepared.

    Args:
        scenes (list): A list of dictionaries, where each dict contains info
                       about a scene (clip_path, text, start, duration).
        audio_path (str): The file path to the voiceover audio.
        output_path (str): The file path to save the final rendered video.
    """
    print(f"--- Starting final render process ---")
    
    all_clips = []
    moviepy_objects_to_close = []

    try:
        # --- 2. LOOP THROUGH PREPARED SCENES ---
        # The logic is now much cleaner. We just loop through the data main.py gives us.
        for scene_data in scenes:
            clip_path = scene_data['clip_path']
            start_time = scene_data['start']
            duration = scene_data['duration']
            caption_text = scene_data['text']

            # Create the base video clip
            video_clip = VideoFileClip(clip_path).set_start(start_time).set_duration(duration)
            moviepy_objects_to_close.append(video_clip)

            # Create the caption clip
            # This styling creates white text with a black outline for maximum readability.
            text_clip = TextClip(
                txt=caption_text,
                fontsize=70,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2,
                size=(video_clip.w * 0.9, None), # 90% of video width
                method='caption' # Handles word wrapping
            ).set_start(start_time).set_duration(duration).set_position(('center', 'center'))
            moviepy_objects_to_close.append(text_clip)

            all_clips.append(video_clip)
            all_clips.append(text_clip)

        if not all_clips:
            raise ValueError("No clips were provided to the render engine.")

        # --- 3. FIX: SET CORRECT 9:16 VERTICAL RESOLUTION ---
        # The final composite is now correctly sized for Shorts/Reels/TikTok.
        final_video = CompositeVideoClip(all_clips, size=(1080, 1920))

        # --- 4. ADD AUDIO AND SET DURATION ---
        print("   Adding audio track...")
        audio_clip = AudioFileClip(audio_path)
        moviepy_objects_to_close.append(audio_clip)
        
        final_video.audio = audio_clip
        # Ensure the final video duration doesn't exceed the audio length
        final_video.duration = audio_clip.duration

        # --- 5. USE THE PROVIDED output_path ---
        # The output filename is now dynamic as controlled by main.py.
        print(f"   Writing final video to: {output_path}")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=30,
            preset='medium',
            threads=os.cpu_count()
        )
        print("--- Render complete! ---")

    except Exception as e:
        print(f"❌ An error occurred during the rendering process: {e}")
        # Re-raise the exception to allow main.py to catch it for cleanup
        raise e
    finally:
        # --- 6. ROBUST CLEANUP ---
        # Ensures all file handles from MoviePy are closed, even if an error occurs.
        print("   Closing all media clips...")
        for obj in moviepy_objects_to_close:
            try:
                obj.close()
            except Exception:
                pass # Ignore errors during cleanup
