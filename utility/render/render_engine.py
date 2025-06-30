# utility/render/render_engine.py

import os
from moviepy.editor import (VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips)
from PIL import Image, ImageDraw, ImageFont
import numpy as np # <-- 1. IMPORT NUMPY

# --- Configuration ---
FONT_FILE = 'Montserrat-Bold.ttf'
FONT_SIZE = 80
VIDEO_RESOLUTION = (1080, 1920)

def render_video(scenes: list, audio_path: str, output_path: str):
    """
    Renders the final video from grouped scenes.
    This version correctly converts Pillow images to NumPy arrays for MoviePy.
    """
    if not os.path.exists(FONT_FILE):
        raise FileNotFoundError(f"Font file '{FONT_FILE}' not found.")

    print("--- Starting final render process from grouped scenes ---")
    
    final_scene_clips = []
    moviepy_objects_to_close = []

    try:
        for scene_data in scenes:
            print(f"   Rendering scene from {scene_data['start']:.2f}s to {scene_data['end']:.2f}s...")
            
            background_clip = VideoFileClip(scene_data['video_path']).set_duration(scene_data['duration'])
            moviepy_objects_to_close.append(background_clip)
            
            clips_for_this_scene = [background_clip]

            for caption_data in scene_data['captions']:
                relative_start = caption_data['start'] - scene_data['start']
                
                canvas = Image.new('RGBA', VIDEO_RESOLUTION, (0, 0, 0, 0))
                draw = ImageDraw.Draw(canvas)
                font = ImageFont.truetype(FONT_FILE, FONT_SIZE)
                
                text_box = draw.textbbox((0,0), caption_data['text'], font=font, align="center")
                text_width, text_height = text_box[2] - text_box[0], text_box[3] - text_box[1]
                pos = ((VIDEO_RESOLUTION[0] - text_width) / 2, (VIDEO_RESOLUTION[1] * 0.75) - (text_height / 2))

                draw.text(pos, caption_data['text'], font=font, fill=(255,255,255), align="center", stroke_width=4, stroke_fill=(0,0,0))
                
                # --- 2. THE FIX ---
                # Convert the Pillow 'canvas' object into a NumPy array.
                numpy_array_canvas = np.array(canvas)
                
                # Create the ImageClip FROM THE NUMPY ARRAY, not the Pillow object.
                caption_clip = ImageClip(numpy_array_canvas).set_start(relative_start).set_duration(caption_data['duration'])
                moviepy_objects_to_close.append(caption_clip)
                
                clips_for_this_scene.append(caption_clip)

            composed_scene_clip = CompositeVideoClip(clips_for_this_scene, size=VIDEO_RESOLUTION)
            final_scene_clips.append(composed_scene_clip)

        final_video = concatenate_videoclips(final_scene_clips)
        
        audio_clip = AudioFileClip(audio_path)
        moviepy_objects_to_close.append(audio_clip)
        
        final_video.audio = audio_clip
        final_video.duration = audio_clip.duration

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
