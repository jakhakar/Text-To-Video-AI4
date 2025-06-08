import os
import asyncio
import argparse

# --- Utility Imports ---
from utility.script.script_generator import generate_script
from utility.audio.audio_generator import generate_audio
from utility.captions.timed_captions_generator import generate_timed_captions

# --- MODIFICATION 1: Import the new, correctly named functions ---
from utility.video.video_search_query_generator import (
    generate_image_prompts_timed,
    fill_empty_prompts
)
from utility.video.background_video_generator import generate_video_assets
from utility.render.render_engine import get_output_media


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a video from a topic.")
    parser.add_argument("topic", type=str, help="The topic for the video")
    args = parser.parse_args()

    # --- Configuration ---
    SAMPLE_TOPIC = args.topic
    SAMPLE_FILE_NAME = "audio_tts.wav"
    VIDEO_SERVER = "flux" # Ensure this is set to use the new image generation logic

    # 1. Generate the script for the video
    response = generate_script(SAMPLE_TOPIC)
    print("script: {}".format(response))

    # 2. Generate the primary audio narration
    asyncio.run(generate_audio(response, SAMPLE_FILE_NAME))

    # 3. Generate timed captions from the audio file
    timed_captions = generate_timed_captions(SAMPLE_FILE_NAME)
    print("Timed captions generated.")

    # --- MODIFICATION 2: Call the new prompt generation function ---
    # Instead of getting search queries, we now generate rich image prompts for each caption.
    timed_image_prompts = None
    if timed_captions:
        print("Generating detailed image prompts for each caption...")
        timed_image_prompts = generate_image_prompts_timed(timed_captions)
    else:
        print("No captions were generated, cannot create image prompts.")

    # --- MODIFICATION 3: Call the new function to handle any API failures ---
    # This will fill any gaps where prompt generation might have failed.
    if timed_image_prompts:
        timed_image_prompts = fill_empty_prompts(timed_image_prompts)
        print("Final timed image prompts have been prepared.")
    
    # --- MODIFICATION 4: Generate video clips from the new prompts ---
    generated_clips = None
    if timed_image_prompts:
        print("Generating video assets from image prompts...")
        # The 'generate_video_assets' function now receives the list of detailed prompts
        generated_clips = generate_video_assets(timed_image_prompts, VIDEO_SERVER)
    else:
        print("No image prompts available, cannot generate video clips.")
        
    # 5. Render the final video
    if generated_clips:
        print("Starting final video render...")
        final_video_path = get_output_media(SAMPLE_FILE_NAME, timed_captions, generated_clips, VIDEO_SERVER)
        if final_video_path:
            print(f"✅ Final video created successfully at: {final_video_path}")
        else:
            print("❌ The rendering process failed.")
    else:
        print("❌ No background video clips were generated. Cannot render final video.")
