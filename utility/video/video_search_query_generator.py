# utility/video/video_search_query_generator.py

import os
import re
import together

# --- Configuration ---
# Ensure your Together.ai API key is set as an environment variable
try:
    together.api_key = "269d47006d5b57821bc87fea56545efa61a89662bfa8c1e0ea0f1448366ddf51"
except KeyError:
    print("ERROR: TOGETHER_API_KEY environment variable not set.")
    print("Please set the variable and run the script again.")
    exit(1)

# A fast and capable model for generating search queries.
# Mixtral is a great choice for this kind of task.
LLM_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"

def _generate_prompts_for_caption(caption_text: str) -> list[str]:
    """
    Uses a large language model to generate descriptive video prompts from a single line of text.
    This is a helper function and not intended to be called directly from outside.
    """
    prompt = f"""
You are an expert AI prompt engineer for a text-to-video generator. Your task is to convert a simple caption into three distinct, highly detailed, and cinematic video prompts.

RULES:
- The prompts must be visually descriptive (mention colors, lighting, camera angles, mood).
- Do not just repeat the caption. Evoke a scene.
- Return ONLY a comma-separated list of the three prompts, with no numbering or extra text.

CAPTION: "{caption_text}"

PROMPTS:
"""
    try:
        response = together.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.8,
        )
        generated_text = response.choices[0].message.content
        # Clean up the output and split into a list
        prompts = [p.strip() for p in generated_text.split(',') if p.strip()]
        # If the model fails to return 3, use the caption as a fallback
        if len(prompts) == 0:
            return [caption_text]
        return prompts
    except Exception as e:
        print(f"Warning: LLM query failed for caption '{caption_text}'. Error: {e}")
        # Fallback to the original caption text if the API call fails
        return [caption_text]

def _generate_timed_captions(script_text: str, words_per_clip: int = 15) -> list:
    """
    Splits a long script into smaller, timed chunks (captions).
    This is a helper function.
    """
    # Simple split by sentences. A more complex parser could be used for .srt files.
    sentences = re.split(r'(?<=[.!?]) +', script_text.strip())
    
    timed_captions = []
    start_time = 0
    for sentence in sentences:
        if not sentence:
            continue
        # Estimate duration based on word count (e.g., 3 words per second -> 5 seconds for 15 words)
        duration = max(3, len(sentence.split()) // 3)
        end_time = start_time + duration
        timed_captions.append([[start_time, end_time], sentence])
        start_time = end_time
        
    return timed_captions

# ----------------------------------------------------------------------------------
# THIS IS THE MAIN FUNCTION YOU WILL IMPORT INTO main.py
# ----------------------------------------------------------------------------------
def generate_timed_video_searches(script_text: str) -> list:
    """
    Takes a full script text and returns a list of timed video search prompts.
    This is the primary function to be used by other modules.

    Args:
        script_text (str): The full text of the video script.

    Returns:
        list: A data structure like: [[[t1, t2], ["prompt1", "prompt2", ...]], ...]
    """
    print("Step 1: Splitting script into timed captions...")
    timed_captions = _generate_timed_captions(script_text)
    
    print("Step 2: Generating creative video prompts for each caption...")
    timed_searches = []
    for (time_range, caption) in timed_captions:
        print(f"  - Caption: \"{caption}\"")
        # For each caption, generate a list of creative search terms/prompts
        search_prompts = _generate_prompts_for_caption(caption)
        print(f"    -> Prompts: {search_prompts}")
        timed_searches.append([time_range, search_prompts])
        
    return timed_searches

# ----------------------------------------------------------------------------------
# This block only runs when you execute this file directly (e.g., `python video_search_query_generator.py`)
# It's used for testing and will NOT run when imported by main.py
# ----------------------------------------------------------------------------------
if __name__ == '__main__':
    print("--- Running direct test of video_search_query_generator.py ---")
    
    # The 'generate_timed_captions' is now defined before being called.
    # But more importantly, this test code is now safely inside this block.
    
    SAMPLE_SCRIPT = """
The universe is vast and mysterious. In the heart of the Orion Nebula, new stars are born from clouds of dust and gas. 
These stellar nurseries are among the most beautiful sights in the cosmos. Meanwhile, on Earth, the deepest part of the ocean, the Mariana Trench, remains less explored than the surface of the moon. 
It is a world of crushing pressure and strange, bioluminescent creatures.
"""
    
    print(f"\nUsing sample script:\n{SAMPLE_SCRIPT}\n")
    
    # Call the main function to test the full workflow
    final_searches = generate_timed_video_searches(SAMPLE_SCRIPT)
    
    print("\n--- Test complete. Final data structure: ---")
    import json
    print(json.dumps(final_searches, indent=2))
