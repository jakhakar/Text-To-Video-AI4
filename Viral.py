import os
import json
import random
import google.generativeai as genai

# --- Configuration: Ensure API Key is set ---
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("FATAL: GEMINI_API_KEY environment variable not set.")
    print("Please set it by running: export GEMINI_API_KEY='your_api_key'")
    exit()

# === MODEL 1: THE TOPIC STRATEGIST ===
# This model's only job is to brainstorm viral topic ideas.

TOPIC_STRATEGIST_INSTRUCTIONS = """
You are a Viral Content Strategist for YouTube Shorts. Your expertise is in identifying non-obvious, high-curiosity topics that have massive viral potential because they contain surprising secrets.

Your task is to generate a list of topics that fit these criteria:
- They seem common on the surface but have hidden depths.
- They are commonly misunderstood by the general public.
- They evoke a strong sense of "I never knew that!"

Strictly output a single, raw, parsable JSON object. The object must contain one key, "topics", which is an array of 5 unique topic strings. Do not add any other text, explanations, or markdown.

# Example of your perfect output:
{"topic": ["The Secret History of Suburbs"]}

topic_generator_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    system_instruction=TOPIC_STRATEGIST_INSTRUCTIONS,
    generation_config=genai.types.GenerationConfig(
        response_mime_type="application/json"
    )
)
