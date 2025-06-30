# utility/captions/timed_captions_generator.py

import whisper_timestamped as whisper
import re

def generate_timed_captions(audio_filename: str, model_size="base") -> list:
    """
    Generates highly granular, timed captions from an audio file using Whisper.
    This function breaks down sentences into smaller, rapidly displayed chunks.

    Args:
        audio_filename (str): The path to the voiceover audio file.
        model_size (str): The Whisper model size ('tiny', 'base', 'small', etc.).

    Returns:
        A list of caption data in the format: [((start_time, end_time), "text"), ...]
    """
    print(f"   Loading Whisper model '{model_size}' for detailed captioning...")
    try:
        # It's often better to run Whisper on CPU to avoid potential VRAM issues
        # fp16=False is recommended for CPU
        model = whisper.load_model(model_size, device="cpu")
        
        print(f"   Transcribing audio to get word-level timestamps...")
        result = whisper.transcribe(model, audio_filename, language="en", fp16=False, verbose=False)
        
        # This function processes the detailed result to create the fast-paced captions
        return get_captions_with_time(result)

    except Exception as e:
        print(f"   ❌ ERROR during Whisper transcription: {e}")
        return None

def _split_words_by_size(words: list, max_caption_size: int) -> list:
    """
    Helper function to split a list of words into smaller caption strings.
    """
    captions = []
    current_caption = ""
    for word in words:
        # If adding the next word doesn't exceed the max size, add it
        if len(current_caption) + len(word) + 1 <= max_caption_size:
            if current_caption:
                current_caption += " " + word
            else:
                current_caption = word
        # If it does exceed, finalize the current caption and start a new one
        else:
            captions.append(current_caption)
            current_caption = word
    # Add the last remaining caption
    if current_caption:
        captions.append(current_caption)
    return captions

def _get_timestamp_mapping(whisper_analysis: dict) -> dict:
    """
    Creates a dictionary mapping the character position of each word in the full
    script to that word's end time. Essential for timing the small chunks.
    """
    location_to_timestamp = {}
    char_position = 0
    for segment in whisper_analysis['segments']:
        for word in segment['words']:
            # The key is a tuple (start_char_pos, end_char_pos)
            # The value is the word's audio end time
            start_char_pos = char_position
            end_char_pos = start_char_pos + len(word['text'])
            location_to_timestamp[(start_char_pos, end_char_pos)] = word['end']
            # Move position forward, accounting for a space
            char_position = end_char_pos + 1
    return location_to_timestamp

def _interpolate_time_from_dict(char_position: int, time_map: dict) -> float | None:
    """Finds the timestamp for a given character position in the text."""
    for key, value in time_map.items():
        if key[0] <= char_position <= key[1]:
            return value
    return None

def get_captions_with_time(whisper_analysis: dict, max_caption_size: int = 25) -> list:
    """
    The main orchestration function for this module.
    It takes the raw Whisper output and processes it into the final list of
    small, fast-paced caption segments.
    """
    word_location_to_time = _get_timestamp_mapping(whisper_analysis)
    
    # Clean the full text by removing punctuation for better splitting
    full_text = whisper_analysis['text']
    clean_text = re.sub(r'[.!?,-]', '', full_text).upper()
    
    # Split the entire text into words, then group into small chunks
    all_words = clean_text.split()
    caption_chunks = _split_words_by_size(all_words, max_caption_size)
    
    char_position = 0
    start_time = 0.0
    captions_with_time = []
    
    for chunk in caption_chunks:
        # Find the character end position of the current chunk
        char_position += len(chunk) + 1
        
        # Find the corresponding end time from our map
        end_time = _interpolate_time_from_dict(char_position, word_location_to_time)
        
        if end_time is not None:
            captions_with_time.append(((start_time, end_time), chunk))
            # The start time of the next caption is the end time of this one
            start_time = end_time

    return captions_with_time
