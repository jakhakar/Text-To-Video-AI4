# utility/render/render_engine.py

import os
from moviepy.editor import (VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip)
from PIL import Image, ImageDraw, ImageFont

# --- THE FIX: Explicitly define the path to the font file ---
# This tells the script to look for 'Arial.ttf' in the same directory as main.py
FONT_FILE = 'Montserrat-Bold.ttf'
FONT_SIZE = 80
VIDEO_RESOLUTION = (1080, 1920)

def render_video(scenes: list, audio_path: str, output_path: str):
    """
    Renders the final video. This version uses Pillow and an explicit font path.
    """
    # --- Check if the required font file exists ---
    if not os.path.exists(FONT_FILE):
        error_message = (f"❌ FONT ERROR: The font file '{FONT_FILE}' was not found in the project's root directory. "
                         "Please download it and place it there before running.")
        raise FileNotFoundError(error_message)

    print("--- Starting final render process (with Pillow captions) ---")
    
    all_clips = []
    moviepy_objects_to_close = []
    current_time = 0.0

    try:
        for scene_data in scenes:
            clip_path = scene_data['clip_path']
            duration = scene_data['duration']
            caption_text = scene_data['text']

            video_clip = VideoFileClip(clip_path).set_start(current_time).set_duration(duration)
            moviepy_objects_to_close.append(video_clip)

            # Create caption image using Pillow
            canvas = Image.new('RGBA', VIDEO_RESOLUTION, (0, 0, 0, 0))
            draw = ImageDraw.Draw(canvas)
            font = ImageFont.truetype(FONT_FILE, FONT_SIZE)

            # Calculate text position for centering
            # Use textbbox for more accurate size calculation
            text_box = draw.textbbox((0, 0), caption_text, font=font, align="center")
            text_width = text_box[2] - text_box[0]
            text_height = text_box[3] - text_box[1]
            position = ((VIDEO_RESOLUTION[0] - text_width) / 2, (VIDEO_RESOLUTION[1] - text_height) / 2)

            # Draw outline
            stroke_width = 4
            for x_offset in range(-stroke_width, stroke_width + 1):
                for y_offset in range(-stroke_width, stroke_width + 1):
                    if x_offset != 0 or y_offset != 0:
                        draw.text((position[0] + x_offset, position[1] + y_offset), caption_text, font=font, fill=(0,0,0,255), align="center")
            
            # Draw main text
            draw.text(position, caption_text, font=font, fill=(255,255,255,255), align="center")

            caption_clip = ImageClip(canvas).set_start(current_time).set_duration(duration)
            moviepy_objects_to_close.append(caption_clip)

            all_clips.append(video_clip)
            all_clips.append(caption_clip)
            
            current_time += duration

        final_video = CompositeVideoClip(all_clips, size=VIDEO_RESOLUTION)
        audio_clip = AudioFileClip(audio_path)
        moviepy_objects_to_close.append(audio_clip)
        
        final_video.audio = audio_clip
        # Use the accumulated duration of clips or the audio duration, whichever is shorter
        final_video.duration = min(current_time, audio_clip.duration)

        print(f"   Writing final video to: {output_path}")
        final_video.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=30, preset='medium')
        print("--- Render complete! ---")

    except Exception as e:
        print(f"❌ An error occurred during the rendering process: {e}")
        raise e
    finally:
        print("   Closing all media clips...")
        for obj in moviepy_objects_to_close:
            try: obj.close()
            except Exception: pass
