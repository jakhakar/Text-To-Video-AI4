# main.py

import sys, os, shutil, asyncio
from datetime import datetime

# Import your updated utility modules
from utility.video.video_search_query_generator import generate_timed_video_searches
from utility.video.background_video_generator import generate_video_assets
from utility.video.captions import create_caption_clip # Import the new caption utility

# Import libraries for assembly
import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip

# --- Configuration ---
FINAL_VIDEO_DIR = "final_videos"
TEMP_DIR = "temp_processing_files"
GENERATED_CLIPS_DIR = "generated_videos"
VIDEO_RESOLUTION = (1080, 1920) # Define vertical resolution once
VOICE = "en-US-JennyNeural" # High-quality Edge TTS voice

os.makedirs(FINAL_VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

async def create_voiceover(text: str, output_path: str):
    """
    NEW: Uses edge-tts to create a high-quality voiceover.
    """
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_path)

def create_video_from_topic(topic: str):
    """
    Main orchestration function, now fully updated.
    """
    print(f"🎬 Starting video creation for topic: '{topic}'")
    
    # --- Part 1: Generate Script & Prompts ---
    try:
        # This now returns the list of scenes AND the full script text for the voiceover
        timed_searches, full_script_text = generate_timed_video_searches(topic)
        if not timed_searches: raise ValueError("Could not generate any video search terms.")
    except Exception as e:
        print(f"❌ ERROR during prompt generation: {e}"); return

    # --- Part 2: Generate Video Clips ---
    # This now returns a list of dictionaries with all necessary info
    generated_clips_data = generate_video_assets(timed_searches)
    
    valid_clips_data = [clip for clip in generated_clips_data if clip['path']]
    if not valid_clips_data:
        print("❌ ERROR: Failed to generate any video clips. Exiting."); return
    print(f"✅ Successfully generated {len(valid_clips_data)} video clips.")

    # --- Part 3: Generate Voiceover using Edge TTS ---
    print("\n[3/5] Generating text-to-speech voiceover...")
    audio_path = os.path.join(TEMP_DIR, "voiceover.mp3")
    try:
        asyncio.run(create_voiceover(full_script_text, audio_path))
        print(f"✅ Voiceover saved to: {audio_path}")
        audio_clip = AudioFileClip(audio_path)
    except Exception as e:
        print(f"❌ ERROR generating audio: {e}"); audio_clip = None

    # --- Part 4: Assemble Clips with Captions ---
    print("\n[4/5] Assembling final video with captions...")
    final_clips_with_captions = []
    try:
        for clip_data in valid_clips_data:
            base_clip = VideoFileClip(clip_data['path'], target_resolution=VIDEO_RESOLUTION)
            
            # Create the caption layer for this scene
            caption_layer = create_caption_clip(
                text=clip_data['caption'],
                start_time=0, # Start at 0 relative to the base_clip
                duration=base_clip.duration,
                frame_size=(base_clip.w, base_clip.h)
            )
            
            # Overlay the caption on top of the video clip
            composite_clip = CompositeVideoClip([base_clip, caption_layer])
            final_clips_with_captions.append(composite_clip)
            
        # Concatenate all the composite clips
        final_video = concatenate_videoclips(final_clips_with_captions, method="compose")

        # Set the audio and match duration
        if audio_clip:
            final_video = final_video.set_audio(audio_clip)
            final_video.duration = min(final_video.duration, audio_clip.duration)

        # --- Write Final Video ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_video_path = os.path.join(FINAL_VIDEO_DIR, f"video_{timestamp}.mp4")
        final_video.write_videofile(final_video_path, codec="libx264", audio_codec="aac", fps=30)
        print(f"\n🎉 SUCCESS! Final video saved to: {final_video_path}")

    except Exception as e:
        print(f"❌ ERROR during final video assembly: {e}")
    finally:
        # --- Part 5: Cleanup ---
        print("\n[5/5] Cleaning up temporary files...")
        # Safely close all clips
        if 'audio_clip' in locals() and audio_clip: audio_clip.close()
        for clip in final_clips_with_captions: clip.close()
        
        if os.path.isdir(GENERATED_CLIPS_DIR): shutil.rmtree(GENERATED_CLIPS_DIR)
        if os.path.isdir(TEMP_DIR): shutil.rmtree(TEMP_DIR)
        print("✅ Cleanup complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_topic = sys.argv[1]
    else:
        print("Usage: python main.py \"<your video topic>\"")
        print("\nRunning with a default example topic...")
        input_topic = "Three mind blowing facts about ancient Rome"
    
    create_video_from_topic(input_topic)
