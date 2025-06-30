# utility/audio/audio_generator.py

import os
import subprocess
import tempfile

# Define the voice to be used.
VOICE = "en-AU-WilliamNeural"

def generate_audio(script: str, output_path: str) -> str | None:
    """
    Generates a voiceover audio file by calling the edge-tts command-line tool.
    This method uses a temporary file to pass the script, bypassing command-line
    length limits which cause the 'File name too long' error.

    Args:
        script (str): The full text of the script to be narrated.
        output_path (str): The file path to save the generated MP3 audio.

    Returns:
        The output path if successful, otherwise None.
    """
    temp_script_file = None
    try:
        # 1. Create a temporary file to hold the script text.
        #    'delete=False' is crucial so we can get its path to pass to the command.
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False, encoding='utf-8') as tf:
            temp_script_file = tf.name
            # Write the script to the file. No sanitization needed here,
            # as the file can handle newlines perfectly.
            tf.write(script)
        
        print(f"   Script saved to temporary file: {temp_script_file}")

        # 2. Construct the command-line arguments.
        #    This is how you would run edge-tts from your terminal.
        command = [
            "edge-tts",
            "--file", temp_script_file,  # <-- Use the --file argument
            "--voice", VOICE,
            "--write-media", output_path
        ]

        print(f"   Running command: {' '.join(command)}")

        # 3. Execute the command.
        #    'check=True' will raise an exception if the command fails.
        #    'capture_output=True' will hide the verbose output unless an error occurs.
        subprocess.run(command, check=True, capture_output=True, text=True)

        if os.path.exists(output_path):
            print(f"   ✅ Audio generated successfully at: {output_path}")
            return output_path
        else:
            raise FileNotFoundError("edge-tts command ran but the output file was not created.")

    except subprocess.CalledProcessError as e:
        # This will catch errors if the edge-tts command itself fails.
        print(f"   ❌ ERROR: edge-tts command failed.")
        print(f"   Stderr: {e.stderr}")
        return None
    except Exception as e:
        print(f"   ❌ An unexpected error occurred during audio generation: {e}")
        return None
    finally:
        # 4. CRITICAL: Clean up the temporary script file.
        #    This 'finally' block ensures the temp file is deleted even if an error occurs.
        if temp_script_file and os.path.exists(temp_script_file):
            os.remove(temp_script_file)
            print(f"   🧹 Cleaned up temporary script file: {temp_script_file}")
