import os
import subprocess
import uuid
import requests
import together

# --- Configuration ---
# Ensure the TOGETHER_API_KEY environment variable is set
try:
    together.api_key = "269d47006d5b57821bc87fea56545efa61a89662bfa8c1e0ea0f1448366ddf51"
except KeyError:
    print("ERROR: TOGETHER_API_KEY environment variable not set.")
    print("Please set the variable and run the script again.")
    exit(1)

# Model to use for image generation
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

    Args:
        prompt (str): The text prompt for image generation.
        width (int): The desired width of the image.
        height (int): The desired height of the image.

    Returns:
        str | None: The file path to the saved image, or None if generation failed.
    """
    print(f"🎨 Generating image for prompt: '{prompt}'...")
    try:
        response = together.images.generate(
            model=MODEL_NAME,
            prompt=prompt,
            n=1,
            width=width,
            height=height
        )

        if not response.data:
            print("❌ Image generation failed. No data in response.")
            return None

        image_url = response.data[0].url
        print(f"   Image generated successfully. Downloading from URL...")

        # Download the image
        image_response = requests.get(image_url, stream=True)
        image_response.raise_for_status() # Raise an exception for bad status codes

        # Save the image to a temporary file
        temp_image_filename = f"{uuid.uuid4()}.png"
        temp_image_path = os.path.join(TEMP_IMAGE_DIR, temp_image_filename)

        with open(temp_image_path, "wb") as f:
            for chunk in image_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"   Image saved to: {temp_image_path}")
        return temp_image_path

    except Exception as e:
        print(f"❌ An error occurred during image generation: {e}")
        return None


def animate_image_to_video(
    image_path: str,
    output_video_path: str,
    duration: int = 5,
    fps: int = 30,
    resolution: str = "1920x1080"
) -> bool:
    """
    Animates a static image into a video with a Ken Burns effect (slow zoom) using FFmpeg.

    Args:
        image_path (str): Path to the input image.
        output_video_path (str): Path to save the output MP4 video.
        duration (int): Duration of the video in seconds.
        fps (int): Frames per second for the video.
        resolution (str): The output video resolution (e.g., "1920x1080").

    Returns:
        bool: True if animation was successful, False otherwise.
    """
    print(f"🎥 Animating '{os.path.basename(image_path)}' into a video...")
    try:
        # This FFmpeg command creates a slow zooming effect (Ken Burns)
        # -loop 1: Loops the single input image
        # -i: Input image file
        # -vf "zoompan...": The video filter for the Ken Burns effect
        #   - z='min(zoom+0.001,1.2)': Zoom level, slowly increasing up to 1.2x
        #   - d: Duration of the pan/zoom effect in frames
        #   - s: Output size
        # -t: Total duration of the output video
        # -c:v libx264: Use the H.264 video codec
        # -pix_fmt yuv420p: Standard pixel format for compatibility
        ffmpeg_command = [
            "ffmpeg",
            "-y",  # Overwrite output file if it exists
            "-loop", "1",
            "-i", image_path,
            "-vf", f"zoompan=z='min(zoom+0.001,1.2)':d={duration*fps}:s={resolution}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            output_video_path
        ]

        # Execute the command
        subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        print(f"   ✅ Video created successfully: {output_video_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg Error:")
        print(f"   Command: {' '.join(e.cmd)}")
        print(f"   Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ FFmpeg command not found. Please ensure FFmpeg is installed and in your system's PATH.")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred during animation: {e}")
        return False


def create_animated_clip_from_prompt(prompt: str, duration: int) -> str | None:
    """
    Orchestrates the process of generating an image and animating it.

    Args:
        prompt (str): The text prompt for the clip.
        duration (int): The desired duration of the final clip.

    Returns:
        str | None: The path to the final video file, or None on failure.
    """
    image_path = None
    try:
        image_path = generate_image_with_flux(prompt)
        if not image_path:
            return None

        # Define the output video path
        video_filename = f"{uuid.uuid4()}.mp4"
        output_video_path = os.path.join(OUTPUT_DIR, video_filename)

        # Animate the image
        success = animate_image_to_video(image_path, output_video_path, duration=duration)

        if success:
            return output_video_path
        else:
            return None
    finally:
        # Clean up the temporary image file
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
            print(f"   🧹 Cleaned up temporary image: {image_path}")


# --- This function REPLACES your original `generate_video_url` ---

def generate_video_assets(timed_video_searches: list, video_server: str) -> list:
    """
    Generates video assets based on a list of timed searches.
    This new version supports 'flux' for generative video.

    Args:
        timed_video_searches (list): A list of tuples, where each tuple contains
                                     a time range and a list of search terms.
                                     e.g., [([0, 5], ["a beautiful sunset over a mountain"]), ...]
        video_server (str): The service to use. Accepts "flux" or "pexel" (legacy).

    Returns:
        list: A list of `[[start_time, end_time], asset_path]`
    """
    timed_asset_paths = []
    
    if video_server == "flux":
        print("\n--- Starting video generation with Flux+FFmpeg ---\n")
        for (t1, t2), search_terms in timed_video_searches:
            video_path = None
            duration = t2 - t1
            # Try each search term until one succeeds
            for query in search_terms:
                video_path = create_animated_clip_from_prompt(query, duration)
                if video_path:
                    break  # Success, move to the next time slot
            
            # If no query worked, path will be None
            if not video_path:
                print(f"⚠️ Could not generate a video for time slot [{t1}, {t2}] with prompts: {search_terms}")

            timed_asset_paths.append([[t1, t2], video_path])

    elif video_server == "pexel":
        print("Pexel server logic is now legacy. Please use 'flux'.")
        # You could place your original Pexels code here for backward compatibility
        # For this example, we'll just return an empty list.
        timed_asset_paths = [] 
        
    else:
        print(f"Unknown video server: {video_server}")

    return timed_asset_paths


# --- Example Usage ---

if __name__ == "__main__":
    # 1. Define the structure of your video with prompts
    # Format: [ ([start_time, end_time], [list_of_prompts]), ... ]
    my_video_script = [
        ([0, 5], ["A cinematic shot of a majestic lion in the Serengeti savanna"]),
        ([5, 10], ["A hyperrealistic, detailed shot of a futuristic city at night, neon lights reflecting on wet streets"]),
        ([10, 15], ["A serene, calm, beautiful beach with crystal clear water and a pirate ship in the distance"]),
        ([15, 20], ["A fantasy landscape, glowing mushrooms in an enchanted forest, epic style"]),
    ]

    # 2. Generate the video clips using the new "flux" server option
    # This will generate 4 video clips of 5 seconds each in the 'generated_videos' folder
    generated_clips = generate_video_assets(my_video_script, video_server="flux")

    # 3. Print the results
    print("\n--- Generation Complete! ---")
    print("Generated video clip assets:")
    for (time_range, path) in generated_clips:
        if path:
            print(f"  - Time {time_range}: {path}")
        else:
            print(f"  - Time {time_range}: FAILED")
            
    print(f"\nAll video files are located in the '{OUTPUT_DIR}' directory.")
    print("You can now use these clips in a video editor to assemble your final video.")
