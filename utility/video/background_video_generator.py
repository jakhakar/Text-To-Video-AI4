# utility/video/background_video_generator.py

import os
import subprocess
import uuid
import base64
import requests
from together import Together

# --- Configuration ---
try:
    client = Together(api_key="269d47006d5b57821bc87fea56545efa61a89662bfa8c1e0ea0f1448366ddf51")
except Exception as e:
    print(f"❌ CRITICAL: Could not initialize Together AI client. Ensure TOGETHER_API_KEY is set.")
    exit(1)

MODEL_NAME = "black-forest-labs/FLUX.1-schnell-Free"
OUTPUT_DIR = "generated_videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _generate_image(prompt: str, width: int = 1008, height: int = 1792) -> str | None:
    """INTERNAL FUNCTION: Generates a 9:16 vertical image and saves it to a temp file."""
    temp_image_dir = os.path.join(OUTPUT_DIR, "temp_images")
    os.makedirs(temp_image_dir, exist_ok=True)
    
    print(f"   🎨 Generating 9:16 image for prompt: '{prompt[:50]}...'")
    try:
        response = client.images.generate(
            model=MODEL_NAME, prompt=prompt, n=1, width=width, height=height, steps=4
        )
        if not response.data: return None

        response_item = response.data[0]
        image_data = None
        image_b64 = getattr(response_item, 'b64_json', None)
        
        if image_b64:
            image_data = base64.b64decode(image_b64)
        else:
            image_url = getattr(response_item, 'url', None)
            if image_url: image_data = requests.get(image_url).content
            else: return None

        temp_image_path = os.path.join(temp_image_dir, f"{uuid.uuid4()}.png")
        with open(temp_image_path, "wb") as f: f.write(image_data)
        return temp_image_path
    except Exception as e:
        print(f"   ❌ Error during image generation: {e}")
        return None


def _animate_video(image_path: str, output_video_path: str, resolution: str = "1080x1920") -> bool:
    """INTERNAL FUNCTION: Animates the image to a 9:16 vertical video."""
    print(f"   🎥 Animating to {resolution} video...")
    try:
        # --- THE FIX IS HERE ---
        # The 'pad' filter requires width and height to be separated by a colon, not an 'x'.
        # We change 'pad=1080x1920' to 'pad=1080:1920'.
        video_filter_chain = (
            f"scale={resolution}:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"  # <-- CORRECTED SYNTAX
            f"zoompan=z='min(zoom+0.001,1.2)':d=125:s={resolution}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        )
        
        ffmpeg_command = [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path,
            "-vf", video_filter_chain,
            "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
            output_video_path
        ]
        
        # We run the command and capture stderr to print only if an error occurs.
        result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        return True
        
    except subprocess.CalledProcessError as e:
        # This will now print the specific FFmpeg error message.
        print(f"   ❌ FFmpeg Error:\n{e.stderr}")
        return False
    except Exception as e:
        print(f"   ❌ An unexpected error occurred during animation: {e}")
        return False


def generate_video_clip(prompt: str) -> str | None:
    """
    Generates a single, animated 9:16 video clip from a text prompt.
    This is the main public function for this module.
    """
    image_path = None
    try:
        image_path = _generate_image(prompt)
        if not image_path: return None

        video_filename = f"{uuid.uuid4()}.mp4"
        output_video_path = os.path.join(OUTPUT_DIR, video_filename)
        
        success = _animate_video(image_path, output_video_path)
        
        if success: return output_video_path
        else: return None

    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
