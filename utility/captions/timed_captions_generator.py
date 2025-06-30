# utility/captions/timed_captions_generator.py

import whisper_timestamped as whisper

def generate_timed_captions(audio_filename: str, model_size="base") -> list:
    """
    Generates timed captions for a script by analyzing the provided audio file.
    This version correctly uses Whisper's sentence-level segments.

    Args:
        audio_filename (str): The path to the voiceover audio file.
        model_size (str): The size of the Whisper model to use (e.g., 'tiny', 'base', 'small').

    Returns:
        A list of dictionaries, where each dictionary represents a scene (caption).
    """
    try:
        print(f"   Loading Whisper model '{model_size}'...")
        # fp16=False is recommended for CPU execution
        model = whisper.load_model(model_size, device="cpu")
        
        print(f"   Transcribing audio to get word timestamps...")
        # Use whisper_timestamped to get detailed transcription data
        result = whisper.transcribe(model, audio_filename, language="en", fp16=False)

    except Exception as e:
        print(f"   ❌ ERROR during Whisper transcription: {e}")
        return None

    # --- THE CORE FIX ---
    # Instead of complex word splitting, we now iterate through Whisper's 'segments'.
    # Each segment is a coherent phrase or sentence, perfect for one scene.
    captions = []
    for segment in result["segments"]:
        captions.append({
            "text": segment["text"].strip(),
            "start": segment["start"],
            "end": segment["end"],
            "duration": segment["end"] - segment["start"]
        })
        
    return captions
