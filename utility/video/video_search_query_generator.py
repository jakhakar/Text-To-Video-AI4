# utility/video/video_search_query_generator.py

import os
import google.generativeai as genai

# --- 1. SETUP THE GOOGLE GEMINI CLIENT ---
# This safely loads your Google API key from the environment.
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"❌ CRITICAL: Failed to configure Google Gemini. {e}")
    exit(1)

# --- 2. DEFINE THE GEMINI MODEL ---
# Using the latest fast and capable model.
LLM_MODEL = "gemini-2.0-flash-lite"

# --- 3. THE NEW, MORE SOPHISTICATED PROMPT GENERATION FUNCTION ---
# This is the ONLY function this module needs to export.
def generate_search_query(full_script: str, current_sentence: str) -> str:
    """
    Generates a single, context-aware visual prompt for a sentence,
    using the entire script for thematic context.

    Args:
        full_script (str): The entire video script for context.
        current_sentence (str): The specific sentence to generate a visual for.

    Returns:
        str: A single, high-quality visual prompt string.
    """
    
    # This new prompt structure is much more powerful.
    # It provides the model with the overall theme and the specific focus.
    prompt = f"""
You are a highly creative AI prompt engineer for a text-to-image generator.
Your task is to create a single, perfect visual prompt for a specific sentence, making sure it aligns with the overall theme of the full script.

**Overall Script Theme:**
---
{full_script}
---

**Specific Sentence for This Scene:**
"{current_sentence}"

**Instructions:**
1.  Read the **Overall Script Theme** to understand the mood, setting, and subject.
2.  Focus on the **Specific Sentence for This Scene**.
3.  Generate a single, visually rich, and descriptive prompt for the image generator.
4.  The prompt should be cinematic, mentioning details like lighting (e.g., "soft morning light," "dramatic shadows"), camera view (e.g., "close-up shot," "wide panoramic view"), and style (e.g., "hyperrealistic," "fantasy art style").
5.  **Do not** just repeat the sentence. Translate its meaning into a beautiful visual concept.
6.  Return ONLY the single prompt string, with no extra text, quotes, or labels.

**PROMPT:**
"""
    try:
        model = genai.GenerativeModel(LLM_MODEL)
        response = model.generate_content(prompt)
        
        # Clean up the response to ensure it's a single, clean string.
        visual_prompt = response.text.strip()
        
        if not visual_prompt:
            print("   Warning: Gemini returned an empty prompt. Falling back to the sentence itself.")
            return current_sentence
            
        return visual_prompt
        
    except Exception as e:
        print(f"   Warning: Google Gemini query failed. Error: {e}")
        # Fallback to the original sentence if the API call fails.
        return current_sentence
