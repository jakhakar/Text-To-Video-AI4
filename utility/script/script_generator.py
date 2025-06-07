import os
import sys
import json
from google import genai
from google.genai import types

client = genai.Client(api_key="GEMINI_API_KEY")

# Configure Gemini 2.5 Flash using API key from environment variable
#configure(api_key=os.environ["GEMINI_API_KEY"])
#model = GenerativeModel("gemini-1.5-flash-latest")

def generate_script(topic):
    prompt = (
        """You are a seasoned content writer for a YouTube Shorts channel, specializing in facts videos. 
        Your facts shorts are concise, each lasting less than 50 seconds (approximately 140 words). 
        They are incredibly engaging and original. When a user requests a specific type of facts short, you will create it.

        For instance, if the user asks for:
        Weird facts
        You would produce content like this:

        Weird facts you don't know:
        - Bananas are berries, but strawberries aren't.
        - A single cloud can weigh over a million pounds.
        - There's a species of jellyfish that is biologically immortal.
        - Honey never spoils; archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still edible.
        - The shortest war in history was between Britain and Zanzibar on August 27, 1896. Zanzibar surrendered after 38 minutes.
        - Octopuses have three hearts and blue blood.

        You are now tasked with creating the best short script based on the user's requested type of 'facts'.

        Keep it brief, highly interesting, and unique.

        Strictly output the script in a JSON format like below, and only provide a parsable JSON object with the key 'script'.

        # Output
        {"script": "Here is the script ..."}
        """
    )
    response = client.models.generate_content(
    model="gemini-1.5-flash",
    config=types.GenerateContentConfig(
        system_instruction=prompt
        content = response.choices[0].message.content
    ),
  
)

    

    try:
        script = json.loads(content)["script"]
    except Exception:
        json_start_index = content.find('{')
        json_end_index = content.rfind('}')
        print(content)
        content = content[json_start_index:json_end_index+1]
        script = json.loads(content)["script"]
    return script
