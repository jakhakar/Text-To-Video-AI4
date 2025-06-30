# utility/audio/audio_generator.py

import os
import asyncio
import edge_tts

# This is an async function, which is fine, but it needs to be robust.
async def generate_audio(text: str, output_filename: str) -> str | None:
    """
    Generates a voiceover audio file from a script using Microsoft Edge TTS.

    Args:
        text (str): The script text to be narrated.
        output_filename (str): The file path to save the generated MP3.

    Returns:
        The output path if successful, otherwise None.
    """
    try:
        # --- THE FIX for "File name too long" ---
        # We clean the text by replacing newlines with spaces before sending it to TTS.
        cleaned_text = text.replace('\n', ' ').strip()

        communicate = edge_tts.Communicate(cleaned_text, "en-AU-WilliamNeural")
        await communicate.save(output_filename)

        # --- ADDED ROBUSTNESS: Check if the file was actually created ---
        if os.path.exists(output_filename):
            return output_filename
        else:
            print(f"   ❌ ERROR: edge-tts reported success, but '{output_filename}' was not created.")
            return None

    except Exception as e:
        print(f"   ❌ An error occurred during audio generation in edge-tts: {e}")
        return None
