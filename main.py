# main.py

import sys, os, shutil
from datetime import datetime

# Import all necessary utility functions
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
SCENE_DURATION_SECONDS = 5

def group_captions_into_scenes(raw_timed_captions: list, scene_duration: int) -> list:
    """
    Groups granular captions into larger scenes of a fixed duration.
    This version correctly handles the tuple output from the caption generator.
    """
    if not raw_timed_captions:
        return []
    
    scenes = []
    total_duration = raw_timed_captions[-1][0][1] # Get the end time of the very last caption
    scene_start_time = 0.0

    # Iterate through the timeline, creating scenes every 'scene_duration' seconds
    for i in range(0, int(total_duration) + scene_duration, scene_duration):
        scene_end_time = i + scene_duration
        
        # This list will hold captions converted to the dictionary format
        captions_for_this_scene = []
        
        # --- THE FIX IS HERE ---
        # We now correctly unpack the tuple `cap` using integer indices.
        for cap in raw_timed_captions:
            start_time = cap[0][0]
            
            # Check if the caption's start time falls within the current scene's time block
            if start_time >= scene_start_time and start_time < scene_end_time:
                # Convert the tuple to the dictionary format the renderer needs
                captions_for_this_scene.append({
                    "text": cap[1],
                    "start": cap[0][0],
                    "end": cap[0][1],
                    "duration": cap[0][1] - cap[0][0]
                })

        if not captions_for_this_scene:
            continue

        # Combine the text of all captions in the scene for a better prompt
        prompt_text = " ".join([cap_dict['text'] for cap_dict in captions_for_this_scene])
        
        scenes.append({
            "start": scene_start_time,
            "end": scene_end_time,
            "duration": scene_duration,
            "prompt_text": prompt_text,
            "captions": captions_for_this_scene # Pass the list of dicts to the scene
        })
        scene_start_time = scene_end_time
        
    return scenes

def create_video_from_topic(topic: str):
    """
    Orchestrates the entire video creation pipeline with scene grouping.
    """
    # --- Setup ---
    if os.path.isdir(TEMP_DIR): shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_VIDEO_DIR, exist_ok=True)
    os.makedirs(FINAL_VIDEO_DIR, exist_ok=True)
    
    print(f"🎬 Starting video creation process for topic: '{topic}'")
    
    try:
        # --- Part 1: Generate Script, Audio, and Granular Captions ---
        print("\n[1/4] Generating script, audio, and detailed captions...")
        full_script_text = generate_script(topic)
        audio_path = generate_audio(full_script_text, TEMP_AUDIO_PATH)
        # This returns the raw tuple data: [((start, end), text), ...]
        raw_captions = generate_timed_captions(audio_path)
        if not raw_captions: raise ValueError("Caption generation failed.")
        print(f"   ✅ Generated {len(raw_captions)} granular caption segments.")

        # --- Part 2: Group Captions and Generate Background Videos ---
        print(f"\n[2/4] Grouping captions into {SCENE_DURATION_SECONDS}-second scenes and generating backgrounds...")
        # This function now correctly processes the raw tuple data
        grouped_scenes = group_captions_into_scenes(raw_captions, SCENE_DURATION_SECONDS)
        
        for i, scene in enumerate(grouped_scenes):
            print(f"\n   --- Scene {i+1}/{len(grouped_scenes)} (Time: {scene['start']:.2f}s - {scene['end']:.2f}s) ---")
            visual_prompt = generate_search_query(full_script_text, scene['prompt_text'])
            print(f"   Context-Aware Prompt: '{visual_prompt}'")
            
            clip_path = generate_video_clip(visual_prompt)
            if clip_path:
                final_clip_path = os.path.join(TEMP_VIDEO_DIR, os.path.basename(clip_path))
                shutil.move(clip_path, final_clip_path)
                scene['video_path'] = final_clip_path
                print(f"   ✅ Background video generated for scene.")
            else:
                scene['video_path'] = None
                print(f"   ⚠️ WARNING: Failed to generate background for this scene.")

        scenes_for_render = [s for s in grouped_scenes if s.get('video_path')]
        if not scenes_for_render: raise ValueError("All background video generations failed.")

        # --- Part 3 & 4: Rendering & Cleanup ---
        print("\n[3/4] Rendering final video with grouped scenes and captions...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_video_path = os.path.join(FINAL_VIDEO_DIR, f"video_{timestamp}.mp4")
        
        render_video(scenes=scenes_for_render, audio_path=audio_path, output_path=final_video_path)
        print(f"\n🎉 SUCCESS! Final video saved to: {final_video_path}")

    except Exception as e:
        print(f"\n❌ A critical error occurred: {e}")
    finally:
        print("\n[4/4] Cleaning up temporary files...")
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
