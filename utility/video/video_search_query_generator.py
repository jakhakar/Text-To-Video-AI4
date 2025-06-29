# utility/video/video_search_query_generator.py

import os
import re

# --- CHANGE 1: Import the main 'Together' class ---
from together import Together

TOGETHER_API_KEY: ${{ secrets.TOGETHER_API_KEY }}
# --- CHANGE 2: Instantiate the client ---
client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

# Mixtral is an excellent, fast model for creative text generation.
LLM_MODEL = "meta-llama/Llama-Vision-Free"

def _generate_prompts_for_caption(caption_text: str) -> list[str]:
    """
    Uses a large language model to generate descriptive video prompts from a single line of text.
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
        # --- CHANGE 3: Use the client object to call the chat completions endpoint ---
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.8,
        )
        generated_text = response.choices[0].message.content
        prompts = [p.strip() for p in generated_text.split(',') if p.strip()]
        if len(prompts) == 0:
            return [caption_text]
        return prompts
    except Exception as e:
        print(f"Warning: LLM query failed for caption '{caption_text}'. Error: {e}")
        return [caption_text]

# The rest of this file (helper functions and the main public function) needs no changes.

def _generate_timed_captions(script_text: str, words_per_clip: int = 15) -> list:
    sentences = re.split(r'(?<=[.!?]) +', script_text.strip())
    timed_captions = []
    start_time = 0
    for sentence in sentences:
        if not sentence:
            continue
        duration = max(3, len(sentence.split()) // 3)
        end_time = start_time + duration
        timed_captions.append([[start_time, end_time], sentence])
        start_time = end_time
    return timed_captions

def generate_timed_video_searches(script_text: str) -> list:
    print("Step 1: Splitting script into timed captions...")
    timed_captions = _generate_timed_captions(script_text)
    
    print("Step 2: Generating creative video prompts for each caption...")
    timed_searches = []
    for (time_range, caption) in timed_captions:
        print(f"  - Caption: \"{caption}\"")
        search_prompts = _generate_prompts_for_caption(caption)
        print(f"    -> Prompts: {search_prompts}")
        timed_searches.append([time_range, search_prompts])
    return timed_searches
