# utility/render/render_engine.py

import os
from moviepy.editor import (VideoFileClip, AudioFileClip, ImageClip,
                            CompositeVideoClip)
# --- 1. IMPORT PILLOW LIBRARIES ---
from PIL import Image, ImageDraw, ImageFont

# --- 2. DEFINE FONT AND STYLING ---
# Assumes 'Poppins-Bold.ttf' is in your project's root directory.
try:
    FONT_FILE = 'Poppins-Bold.ttf' if os.path.exists('Poppins-Bold.ttf') else 'arial.ttf'
    FONT_SIZE = 80
except Exception:
    print("Warning: Font file not found. Defaulting may occur.")
    FONT_FILE = 'arial' # A last resort fallback
    FONT_SIZE = 80
    
VIDEO_RESOLUTION = (1080, 1920)

def render_video(scenes: list, audio_path: str, output_path: str):
    """
    Renders the final video. This version uses Pillow to create captions,
    bypassing the need for ImageMagick.
    """
    print("--- Starting final render process (with Pillow captions) ---")
    
    all_clips = []
    moviepy_objects_to_close = []

    try:
        current_time = 0.0
        # --- 3. LOOP THROUGH SCENES AND BUILD CLIPS ---
        for scene_data in scenes:
            clip_path = scene_data['clip_path']
            duration = scene_data['duration']
            caption_text = scene_data['text']

            # Create the base video clip
            video_clip = VideoFileClip(clip_path).set_start(current_time).set_duration(duration)
            moviepy_objects_to_close.append(video_clip)

            # --- 4. CREATE CAPTION IMAGE USING PILLOW ---
            # Create a transparent canvas
            canvas = Image.new('RGBA', VIDEO_RESOLUTION, (0, 0, 0, 0))
            draw = ImageDraw.Draw(canvas)
            font = ImageFont.truetype(FONT_FILE, FONT_SIZE)

            # Calculate text position
            text_bbox = draw.textbbox((0, 0), caption_text, font=font, align="center")
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            position = ((VIDEO_RESOLUTION[0] - text_width) / 2, (VIDEO_RESOLUTION[1] - text_height) / 2)

            # Draw black stroke for outline
            stroke_width = 4
            for x_offset in range(-stroke_width, stroke_width + 1):
                for y_offset in range(-stroke_width, stroke_width + 1):
                    draw.text((position[0] + x_offset, position[1] + y_offset), caption_text, font=font, fill=(0, 0, 0, 255), align="center")
            
            # Draw white text on top
            draw.text(position, caption_text, font=font, fill=(255, 255, 255, 255), align="center")

            # Convert the Pillow Image to a MoviePy ImageClip
            caption_clip = ImageClip(canvas).set_start(current_time).set_duration(duration)
            moviepy_objects_to_close.append(caption_clip)

            all_clips.append(video_clip)
            all_clips.append(caption_clip)
            
            current_time += duration

        if not all_clips:
            raise ValueError("No clips were provided to the render engine.")

        # --- 5. COMPOSITE AND FINALIZE ---
        final_video = CompositeVideoClip(all_clips, size=VIDEO_RESOLUTION)

        audio_clip = AudioFileClip(audio_path)
        moviepy_objects_to_close.append(audio_clip)
        
        final_video.audio = audio_clip
        final_video.duration = audio_clip.duration

        print(f"   Writing final video to: {output_path}")
        final_video.write_videofile(
            output_path, codec='libx264', audio_codec='aac', fps=30, preset='medium', threads=os.cpu_count()
        )
        print("--- Render complete! ---")

    except Exception as e:
        print(f"❌ An error occurred during the rendering process: {e}")
        raise e
    finally:
        print("   Closing all media clips...")
        for obj in moviepy_objects_to_close:
            try: obj.close()
            except Exception: pass
