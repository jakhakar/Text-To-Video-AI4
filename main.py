import os
import asyncio
import argparse

# --- Utility Imports ---
from utility.script.script_generator import generate_script
from utility.audio.audio_generator import generate_audio
from utility.captions.timed_captions_generator import generate_timed_captions
from utility.video.video_search_query_generator import getVideoSearchQueriesTimed, merge_empty_intervals

# --- MODIFICATION 1: Corrected the import name ---
# The function is named generate_video_assets (with a 't'), not 'assests'
from utility.video.background_video_generator import generate_video_assets
from utility.render.render_engine import get_output_media


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a video from a topic.")
    parser.add_argument("topic", type=str, help="The topic for the video")
    args = parser.parse_args()

    # --- Configuration ---
    SAMPLE_TOPIC = args.topic
    SAMPLE_FILE_NAME = "audio_tts.wav"

    # --- MODIFICATION 2: Set the video server to 'flux' ---
    # This is the critical switch that tells the program to use
    # the new Together.ai + FFmpeg generation method.
    VIDEO_SERVER = "flux"

    # 1. Generate the script for the video
    response = generate_script(SAMPLE_TOPIC)
    print("script: {}".format(response))

    # 2. Generate the primary audio narration
    asyncio.run(generate_audio(response, SAMPLE_FILE_NAME))

    # 3. Generate timed captions from the audio file
    timed_captions = generate_timed_captions(SAMPLE_FILE_NAME)
    print("Timed captions generated:")
    print(timed_captions)

    # 4. Determine what video clips to generate based on the script and timings
    search_terms = getVideoSearchQueriesTimed(response, timed_captions)
    print("Video search queries generated:")
    print(search_terms)

    # --- MODIFICATION 3: Renamed variable for clarity ---
    # The function now returns a list of local file paths, not URLs.
    # Renaming the variable makes the code's intent clearer.
    generated_clips = None

    if search_terms is not None:
        # --- MODIFICATION 4: Call the new, correct function ---
        # We now call generate_video_assets with the "flux" server.
        generated_clips = generate_video_assets(search_terms, VIDEO_SERVER)
        print("Generated video clip paths:")
        print(generated_clips)
    else:
        print("No search terms were generated, cannot create background video.")

    # This function presumably handles any empty slots. It will now receive
    # a list of file paths (with None for failures) instead of URLs.
    generated_clips = merge_empty_intervals(generated_clips)

    # 5. Render the final video
    if generated_clips is not None:
        print("Starting final video render...")
        # Pass the list of local clip paths to the rendering engine.
        # The render engine must be able to handle local paths when VIDEO_SERVER is "flux".
        final_video_path = get_output_media(SAMPLE_FILE_NAME, timed_captions, generated_clips, VIDEO_SERVER)
        print(f"✅ Final video created successfully at: {final_video_path}")
    else:
        print("❌ No background video clips were generated. Cannot render final video.")
