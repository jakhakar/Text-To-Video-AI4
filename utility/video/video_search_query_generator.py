import os
import json
import re
from groq import Groq # Use the correct import
from utility.utils import log_response, LOG_TYPE_GPT

# --- Configuration ---
# Check for API key at the start and provide a clear error.
try:
    GROQ_API_KEY = os.environ["GROQ_API_KEY"]
except KeyError:
    raise EnvironmentError("FATAL: GROQ_API_KEY environment variable not set.")

CLIENT = Groq(api_key=GROQ_API_KEY)
MODEL = "llama3-70b-8192"

PROMPT = """
# Instructions
You are an AI assistant that generates video search keywords.
Given a video script and a JSON array of timed captions, your task is to generate a new JSON array of timed visual keywords.

# Rules
1.  **Output Format:** Your response MUST be ONLY a valid JSON array. Do not include any extra text, explanations, or markdown fences like ```json.
2.  **Time Segmentation:** Each keyword segment should be 2-4 seconds long. The time periods in your output must be strictly consecutive and cover the entire duration of the input captions.
3.  **Keywords:** For each time segment, provide one to three visually concrete and specific keywords. Keywords must be in English and describe something that can be seen.
    - **GOOD:** "crying child", "futuristic city at night", "lion running"
    - **BAD:** "emotional moment", "sadness" (not visually concrete)
4.  **Context:** Use the full script for context, but base the timing of keywords on the provided timed captions.
5.  **Input Example:** If you receive timed captions like `[[[0, 2.1], "The cheetah is the fastest"], [[2.1, 4.5], "land animal on Earth."]]`, you could output `[[[0, 4.5], ["cheetah running", "fast savanna", "sprinting animal"]]]`.

# Example Output Structure
[[[t1, t2], ["keyword1", "keyword2"]], [[t2, t3], ["keyword3", "keyword4", "keyword5"]], ...]
"""

def _fix_and_load_json(json_string: str):
    """Attempts to fix and parse a JSON string from LLM output."""
    # Remove markdown fences and surrounding whitespace
    json_string = json_string.strip().replace("```json", "").replace("```", "").strip()
    # Replace typographical apostrophes that can break JSON
    json_string = json_string.replace("’", "'")
    
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Initial JSON parsing failed: {e}")
        print(f"Problematic string: {json_string}")
        # Add more advanced fixing logic here if needed in the future
        return None

def _call_groq_api(script: str, formatted_captions: str, max_retries: int = 3):
    """Calls the Groq API to get video search queries, with a retry mechanism."""
    user_content = f"Video Script for context:\n{script}\n\nTimed Captions to process:\n{formatted_captions}"
    
    for attempt in range(max_retries):
        print(f"Attempting to generate keywords (Attempt {attempt + 1}/{max_retries})...")
        try:
            response = CLIENT.chat.completions.create(
                model=MODEL,
                temperature=0.2, # Lower temperature for more predictable JSON output
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": user_content}
                ]
            )
            text = response.choices[0].message.content
            log_response(LOG_TYPE_GPT, script, text)
            
            # Attempt to parse the response
            parsed_json = _fix_and_load_json(text)
            if parsed_json and isinstance(parsed_json, list):
                print("Successfully generated and parsed keywords.")
                return parsed_json
            else:
                print("Failed to parse JSON or response was not a list.")

        except Exception as e:
            print(f"An error occurred during API call attempt {attempt + 1}: {e}")

    print("Failed to get a valid response from the API after all retries.")
    return None

def get_video_search_queries_timed(script: str, captions_timed: list):
    """
    Main function to generate timed video search queries from a script and captions.
    This has been corrected to remove the infinite loop.
    """
    if not captions_timed:
        print("Error: Received empty timed captions.")
        return None

    # --- FIX: Format the captions as a clean JSON string for the LLM ---
    # This is much easier for the model to understand than a mashed-together string.
    formatted_captions = json.dumps(captions_timed, indent=2)
    
    # --- FIX: The dangerous `while` loop is replaced by a single, robust call ---
    search_queries = _call_groq_api(script, formatted_captions)
    
    return search_queries


def merge_empty_intervals(segments: list):
    """
    Corrected and simplified logic to fill gaps in video assets.
    If a segment has no video, it will be covered by the previous valid video.
    """
    if not segments:
        return []

    # Find the first valid asset to fill any initial gaps
    first_valid_asset = None
    for _, asset in segments:
        if asset is not None:
            first_valid_asset = asset
            break
            
    # Use a forward-fill approach
    last_valid_asset = first_valid_asset
    for i in range(len(segments)):
        interval, asset = segments[i]
        if asset is None:
            # If the current asset is None, replace it with the last valid one
            segments[i][1] = last_valid_asset
        else:
            # If the current asset is valid, it becomes the new "last valid" one
            last_valid_asset = asset
            
    # Now merge consecutive segments that have the same asset path
    if not segments:
        return []

    merged = []
    current_interval, current_asset = segments[0]
    
    for i in range(1, len(segments)):
        next_interval, next_asset = segments[i]
        # If the asset is the same, extend the current interval
        if next_asset == current_asset:
            current_interval[1] = next_interval[1]
        # Otherwise, finalize the current segment and start a new one
        else:
            merged.append([current_interval, current_asset])
            current_interval, current_asset = next_interval

    # Append the very last segment
    merged.append([current_interval, current_asset])

    return merged
