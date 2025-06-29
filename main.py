# main.py

import sys
import os
import shutil
from datetime import datetime

# --- Configuration: Define temporary and final directories ---
TEMP_DIR = "temp_processing_files"
TEMP_VIDEO_DIR = os.path.join(TEMP_DIR, "clips")
TEMP_AUDIO_PATH = os.path.join(TEMP_DIR, "voiceover.mp3")
FINAL_VIDEO_DIR = "final_videos"

# --- 1. Import all necessary utility functions ---
# Each import corresponds to a specific step in our pipeline.
try:
    from utility.script.script_generator import generate_script
    from utility.audio.audio_generator import generate_audio
    from utility.captions.timed_captions_generator import generate_timed_captions
    from utility.video.video_search_query_generator import generate_search_queries
    from utility.video.background_video_generator import generate_video_clip
    from utility.render.render_engine import render_video
except ImportError as e:
    print(f"❌ Critical Error: Failed to import a required utility module.")
    print(f"   Please ensure all utility files exist and are correctly named.")
    print(f"   Details: {e}")
    sys.exit(1)


def create_video_from_topic(topic: str):
    """
    Orchestrates the entire video creation pipeline by calling specialized modules.
    This function acts as the conductor of the project.
    """
    # --- Setup: Create clean temporary directories for the run ---
    if os.path.isdir(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_VIDEO_DIR, exist_ok=True)
    os.makedirs(FINAL_VIDEO_DIR, exist_ok=True)
    
    print(f"🎬 Starting video creation process for topic: '{topic}'")
    
    try:
        # --- Part 1: Script Generation ---
        print("\n[1/6] Generating script from topic...")
        full_script_text = generate_script(topic)
        if not full_script_text: raise ValueError("Script generation failed.")
        print(f"   ✅ Script generated successfully.")

        # --- Part 2: Audio Generation ---
        print("\n[2/6] Generating voiceover audio...")
        audio_path = generate_audio(full_script_text, TEMP_AUDIO_PATH)
        if not audio_path: raise ValueError("Audio generation failed.")
        print(f"   ✅ Voiceover saved to: {audio_path}")
        
        # --- Part 3: Timed Captions ---
        print("\n[3/6] Splitting script into timed captions...")
        timed_captions = generate_timed_captions(full_script_text)
        if not timed_captions: raise ValueError("Failed to generate timed captions.")
        print(f"   ✅ Script split into {len(timed_captions)} scenes.")

        # --- Part 4: Video Clip Generation (Loop through each scene) ---
        print("\n[4/6] Generating video clip for each scene...")
        scenes_for_render = []
        for i, caption_data in enumerate(timed_captions):
            scene_num = i + 1
            caption_text = caption_data['text']
            print(f"\n   --- Scene {scene_num}/{len(timed_captions)}: '{caption_text[:40]}...' ---")
            
            # Get multiple visual ideas (prompts) for the scene's text
            prompts = generate_search_queries(caption_text)
            
            # Try each prompt until one successfully generates a video
            clip_path = None
            for prompt in prompts:
                # This function MUST be configured to produce 9:16 vertical video
                generated_path = generate_video_clip(prompt)
                if generated_path:
                    # Move the generated clip to our temporary directory for this run
                    final_clip_path = os.path.join(TEMP_VIDEO_DIR, os.path.basename(generated_path))
                    shutil.move(generated_path, final_clip_path)
                    clip_path = final_clip_path
                    print(f"   ✅ Clip generated for prompt: '{prompt}'")
                    break # Success, move to the next scene
            
            if clip_path:
                # Add all necessary information for the render engine
                caption_data['clip_path'] = clip_path
                scenes_for_render.append(caption_data)
            else:
                print(f"   ⚠️ WARNING: Failed to generate a video clip for scene {scene_num}. It will be skipped.")

        if not scenes_for_render:
            raise ValueError("All video clip generations failed. Cannot proceed.")

        # --- Part 5: Final Video Rendering ---
        print("\n[5/6] Rendering final video with captions and audio...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_video_path = os.path.join(FINAL_VIDEO_DIR, f"video_{timestamp}.mp4")
        
        # The render engine does the heavy lifting of combining everything
        render_video(
            scenes=scenes_for_render,
            audio_path=audio_path,
            output_path=final_video_path
        )
        print(f"\n🎉 SUCCESS! Final video saved to: {final_video_path}")

    except Exception as e:
        print(f"\n❌ A critical error occurred during the process: {e}")
        print("   Video creation failed.")
    finally:
        # --- Part 6: Cleanup ---
        print("\n[6/6] Cleaning up temporary files...")
        if os.path.isdir(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        # Also clean the root-level folder that background_video_generator might create
        if os.path.isdir("generated_videos"):
            shutil.rmtree("generated_videos")
        print("   ✅ Cleanup complete.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_topic = sys.argv[1]
    else:
        print("Usage: python main.py \"<your video topic>\"")
        print("\nRunning with a default example topic...")
        input_topic = "Three mind blowing facts about the deep ocean"
    
    create_video_from_topic(input_topic)
