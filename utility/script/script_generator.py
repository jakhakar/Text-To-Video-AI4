import os
import json
import google.generativeai as genai

# --- Configuration ---
# 1. Set up your API key. 
#    It's best practice to set this as an environment variable.
#    In your terminal: export GEMINI_API_KEY="YOUR_API_KEY"
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    print("ERROR: GEMINI_API_KEY environment variable not set.")
    exit()

# 2. Define the System Instructions for the AI
#    This tells the model its role, rules, and output format.
SYSTEM_INSTRUCTIONS = """You are a seasoned content writer for a YouTube Shorts channel specializing in facts videos.
Your facts shorts are concise, each lasting less than 50 seconds (approximately 140 words).
They are incredibly engaging and original.

When a user provides a topic for a facts short, you will create a script for it.

For instance, if the user's topic is "Weird facts", you would produce content like this:

Weird facts you don't know:
- Bananas are berries, but strawberries aren't.
- A single cloud can weigh over a million pounds.
- There's a species of jellyfish that is biologically immortal.
- Honey never spoils; archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still edible.
- The shortest war in history was between Britain and Zanzibar on August 27, 1896. Zanzibar surrendered after 38 minutes.
- Octopuses have three hearts and blue blood.

You are now tasked with creating the best short script based on the user's requested topic.
Keep it brief, highly interesting, and unique.

Strictly output the script in a JSON format like below. Only provide a single, parsable JSON object with the key 'script'. Do not add any other text or formatting before or after the JSON.

# Example Output
{"script": "Here is the script..."}
"""

# 3. Create the Generative Model instance (do this only once)
#    We use gemini-1.5-flash for speed and cost-effectiveness.
#    We also enable JSON mode for reliable parsing.
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-lite",
    system_instruction=SYSTEM_INSTRUCTIONS,
    generation_config=genai.types.GenerationConfig(
        response_mime_type="application/json"
    )
)

def generate_script(topic: str) -> str:
    """
    Generates a YouTube Shorts script for a given topic using Gemini.

    Args:
        topic: The subject for the facts video (e.g., "Space Facts").

    Returns:
        The generated script as a string, or an error message.
    """
    print(f"Generating script for topic: '{topic}'...")
    
    # The user's request is the prompt
    prompt = f"Create a YouTube facts short about: {topic}"

    try:
        response = model.generate_content(prompt)
        
        # The API's JSON mode helps ensure the response is valid JSON.
        # We parse the text content of the response.
        script_data = json.loads(response.text)
        
        return script_data.get("script", "Error: 'script' key not found in response.")

    except json.JSONDecodeError:
        print("---ERROR: Failed to decode JSON from the model's response.---")
        print("Model Response Text:", response.text)
        return "Error: Could not parse the script from the AI's response."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "Error: An unexpected error occurred during script generation."
