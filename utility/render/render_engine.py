# utility/render/render_engine.py

import os
from moviepy.editor import (VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips)
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
FONT_FILE = 'Montserrat-Bold.ttf'
FONT_SIZE = 80
VIDEO_RESOLUTION = (1080, 1920)

def render_video(scenes: list, audio_path: str, output_path: str):
    """
    Renders the final video from grouped scenes.
    A single background video is used for each scene, while multiple
    granular captions are overlaid on top.
    """
    if not os.path.exists(FONT_FILE):
        raise FileNotFoundError(f"Font file '{FONT_FILE}' not found.")

    print("--- Starting final render process from grouped scenes ---")
    
    final_scene_clips = []
    moviepy_objects_to_close = []

    try:
        # --- Loop 1: Process each high-level scene ---
        for scene_data in scenes:
            print(f"   Rendering scene from {scene_data['start']:.2f}s to {scene_data['end']:.2f}s...")
            
            # Create the single background video clip for this entire scene
            background_clip = VideoFileClip(scene_data['video_path']).set_duration(scene_data['duration'])
            moviepy_objects_to_close.append(background_clip)
            
            clips_for_this_scene = [background_clip]

            # --- Loop 2: Process the granular captions within this scene ---
            for caption_data in scene_data['captions']:
                # Calculate the caption's start time *relative to the scene*
                relative_start = caption_data['start'] - scene_data['start']
                
                # Create the caption image with Pillow
                canvas = Image.new('RGBA', VIDEO_RESOLUTION, (0, 0, 0, 0))
                draw = ImageDraw.Draw(canvas)
                font = ImageFont.truetype(FONT_FILE, FONT_SIZE)
                
                text_box = draw.textbbox((0,0), caption_data['text'], font=font, align="center")
                text_width, text_height = text_box[2] - text_box[0], text_box[3] - text_box[1]
                pos = ((VIDEO_RESOLUTION[0] - text_width) / 2, (VIDEO_RESOLUTION[1] * 0.75) - (text_height / 2)) # Centered on bottom 3/4 line

                # Draw outline and text
                draw.text(pos, caption_data['text'], font=font, fill=(255,255,255), align="center", stroke_width=4, stroke_fill=(0,0,0))
                
                # Convert to MoviePy clip
                caption_clip = ImageClip(canvas).set_start(relative_start).set_duration(caption_data['duration'])
                moviepy_objects_to_close.append(caption_clip)
                
                clips_for_this_scene.append(caption_clip)

            # Compose this scene's background and all its captions
            composed_scene_clip = CompositeVideoClip(clips_for_this_scene, size=VIDEO_RESOLUTION)
            final_scene_clips.append(composed_scene_clip)

        # Concatenate all the final composed scenes into one video
        final_video = concatenate_videoclips(final_scene_clips)
        
        # Add audio and finalize
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
