# main.py

import sys, os, shutil
from datetime import datetime
# import asyncio # <-- 1. REMOVED: This import is no longer needed.

# --- Import all necessary utility functions ---
try:
    from utility.script.script_generator import generate_script
    from utility.audio.audio_generator import generate_audio
    from utility.captions.timed_captions_generator import generate_timed_captions
    from utility.video.video_search_query_generator import generate_search_query
    from utility.video.background_video_generator import generate_video_clip
    from utility.render.render_engine import render_video
except ImportError as e:
    print(f"❌ Critical Error: Failed to import a required utility module: {e}")
    sys.exit(1)

# --- Configuration ---
TEMP_DIR = "temp_processing_files"
TEMP_VIDEO_DIR = os.path.join(TEMP_DIR, "clips")
TEMP_AUDIO_PATH = os.path.join(TEMP_DIR, "voiceover.mp3")
FINAL_VIDEO_DIR = "final_videos"

def create_video_from_topic(topic: str):
    """
    Orchestrates the entire video creation pipeline by calling specialized modules.
    """
    # --- Setup ---
    if os.path.isdir(TEMP_DIR): shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_VIDEO_DIR, exist_ok=True)
    os.makedirs(FINAL_VIDEO_DIR, exist_ok=True)
    
    print(f"🎬 Starting video creation process for topic: '{topic}'")
    
    try:
        # --- Part 1: Script Generation ---
        print("\n[1/5] Generating script from topic...")
        full_script_text = generate_script(topic)
        if "Error:" in full_script_text: raise ValueError(full_script_text)
        
        # --- Part 2: Audio & Captions ---
        print("\n[2/5] Generating audio and timed captions...")
        
        # --- 2. THE FIX: Call the function directly, without asyncio.run() ---
        audio_path = generate_audio(full_script_text, TEMP_AUDIO_PATH)
        if not audio_path: raise ValueError("Audio generation failed.")
        
        timed_captions = generate_timed_captions(full_script_text)
        if not timed_captions: raise ValueError("Failed to generate timed captions.")
        print(f"   ✅ Script and assets prepared for {len(timed_captions)} scenes.")

        # --- Part 3: Video Clip Generation ---
        print("\n[3/5] Generating video clip for each scene...")
        scenes_for_render = []
        for i, caption_data in enumerate(timed_captions):
            scene_num = i + 1; caption_text = caption_data['text']
            print(f"\n   --- Scene {scene_num}/{len(timed_captions)} ---")
            
            visual_prompt = generate_search_query(full_script_text, caption_text)
            print(f"   Context-Aware Prompt: '{visual_prompt}'")
            
            clip_path = generate_video_clip(visual_prompt)
            if clip_path:
                final_clip_path = os.path.join(TEMP_VIDEO_DIR, os.path.basename(clip_path))
                shutil.move(clip_path, final_clip_path)
                caption_data['clip_path'] = final_clip_path
                scenes_for_render.append(caption_data)
                print(f"   ✅ Clip generated and saved.")
            else:
                print(f"   ⚠️ WARNING: Failed to generate a video clip for this scene. It will be skipped.")

        if not scenes_for_render: raise ValueError("All video clip generations failed.")

        # --- Part 4: Rendering & Cleanup ---
        print("\n[4/5] Rendering final video...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_video_path = os.path.join(FINAL_VIDEO_DIR, f"video_{timestamp}.mp4")
        
        render_video(scenes=scenes_for_render, audio_path=audio_path, output_path=final_video_path)
        print(f"\n🎉 SUCCESS! Final video saved to: {final_video_path}")

    except Exception as e:
        print(f"\n❌ A critical error occurred: {e}")
    finally:
        print("\n[5/5] Cleaning up temporary files...")
        if os.path.isdir(TEMP_DIR): shutil.rmtree(TEMP_DIR)
        if os.path.isdir("generated_videos"): shutil.rmtree("generated_videos")
        print("   ✅ Cleanup complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_topic = sys.argv[1]
    else:
        print("Usage: python main.py \"<your video topic>\"")
        input_topic = "The incredible life of honeybees"
    
    create_video_from_topic(input_topic)
