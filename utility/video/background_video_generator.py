# utility/video/background_video_generator.py

import os
import subprocess
import uuid
import requests

# --- CHANGE 1: Import the main 'Together' class ---
from together import Together

#TOGETHER_API_KEY: ${{ secrets.TOGETHER_API_KEY }}
# --- CHANGE 2: Instantiate the client. API key is read automatically from the environment. ---
# The client object will be used to make all API calls.
client = Together(api_key="269d47006d5b57821bc87fea56545efa61a89662bfa8c1e0ea0f1448366ddf51")

# --- CHANGE 3: Use the specific free model you provided ---
MODEL_NAME = "black-forest-labs/FLUX.1-schnell-Free"

# Directory to save generated assets
OUTPUT_DIR = "generated_videos"
TEMP_IMAGE_DIR = os.path.join(OUTPUT_DIR, "temp_images")

# Create directories if they don't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)


def generate_image_with_flux(prompt: str, width: int = 1920, height: int = 1080) -> str | None:
    """
    Generates an image using Together.ai's Flux Schnell model and saves it locally.
    """
    print(f"🎨 Generating image for prompt: '{prompt}'...")
    try:
        # --- CHANGE 4: Use the client object to generate the image ---
        response = client.images.generate(
            model=MODEL_NAME,
            prompt=prompt,
            n=1,
            width=width,
            height=height
        )

        if not response.data:
            print("❌ Image generation failed. No data in response.")
            return None

        # The free model returns image data directly as a base64 string
        image_b64 = response.data[0].b64_json
        print(f"   Image generated successfully. Decoding base64 data...")

        # Decode the base64 string into bytes
        import base64
        image_data = base64.b64decode(image_b64)

        # Save the image to a temporary file
        temp_image_filename = f"{uuid.uuid4()}.png"
        temp_image_path = os.path.join(TEMP_IMAGE_DIR, temp_image_filename)

        with open(temp_image_path, "wb") as f:
            f.write(image_data)
        
        print(f"   Image saved to: {temp_image_path}")
        return temp_image_path

    except Exception as e:
        print(f"❌ An error occurred during image generation: {e}")
        return None

# The 'animate_image_to_video' and 'create_animated_clip_from_prompt' functions
# do not need any changes, so they are included here as they were.

def animate_image_to_video(
    image_path: str,
    output_video_path: str,
    duration: int = 5,
    fps: int = 30,
    resolution: str = "1920x1080"
) -> bool:
    print(f"🎥 Animating '{os.path.basename(image_path)}' into a video...")
    try:
        ffmpeg_command = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path,
            "-vf", f"zoompan=z='min(zoom+0.001,1.2)':d={duration*fps}:s={resolution}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
            "-t", str(duration), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
            output_video_path
        ]
        subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        print(f"   ✅ Video created successfully: {output_video_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ FFmpeg command not found. Ensure it's installed and in your PATH.")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred during animation: {e}")
        return False

def create_animated_clip_from_prompt(prompt: str, duration: int) -> str | None:
    image_path = None
    try:
        image_path = generate_image_with_flux(prompt)
        if not image_path: return None
        video_filename = f"{uuid.uuid4()}.mp4"
        output_video_path = os.path.join(OUTPUT_DIR, video_filename)
        success = animate_image_to_video(image_path, output_video_path, duration=duration)
        return output_video_path if success else None
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
            print(f"   🧹 Cleaned up temporary image: {image_path}")

def generate_video_assets(timed_video_searches: list, video_server: str) -> list:
    timed_asset_paths = []
    if video_server == "flux":
        print("\n--- Starting video generation with Flux+FFmpeg ---")
        for (t1, t2), search_terms in timed_video_searches:
            video_path = None
            duration = t2 - t1
            for query in search_terms:
                video_path = create_animated_clip_from_prompt(query, duration)
                if video_path: break
            if not video_path:
                print(f"⚠️ Could not generate a video for time slot [{t1}, {t2}] with prompts: {search_terms}")
            timed_asset_paths.append([[t1, t2], video_path])
    return timed_asset_paths
