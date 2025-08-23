import os
import io
import requests
import pyaudio
import sys
from murf import Murf
from openai import OpenAI
from pydub import AudioSegment

# --- 1. API KEY & CLIENT SETUP ---
# Environment variables are used for security.
# Ensure OPENROUTER_API_KEY and MURF_API_KEY are set on your system.

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
MURF_API_KEY = os.environ.get('MURF_API_KEY')

if not OPENROUTER_API_KEY:
    print("Error: The OPENROUTER_API_KEY environment variable is not set.")
    sys.exit()
if not MURF_API_KEY:
    print("Error: The MURF_API_KEY environment variable is not set.")
    sys.exit()

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

murf_client = Murf(api_key=MURF_API_KEY)
murf_voice_id = "en-US-natalie" # You can choose a different voice ID here.

# --- 2. AUDIO INPUT/OUTPUT FUNCTIONS ---
def speak(text: str):
    """
    Generates audio from text using the Murf API and plays it using PyAudio.
    """
    try:
        # Generate the audio file URL from the text
        audio_res = murf_client.text_to_speech.generate(
            text=text,
            voice_id=murf_voice_id
        )
        
        audio_url = audio_res.audio_file
        
        print(f"Assistant: {text}")
        
        # Use requests to download the audio data
        response = requests.get(audio_url)
        response.raise_for_status() 
        
        # Load the audio into an in-memory AudioSegment
        audio_segment = AudioSegment.from_file(io.BytesIO(response.content), format="wav")
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(audio_segment.sample_width),
                        channels=audio_segment.channels,
                        rate=audio_segment.frame_rate,
                        output=True)
        
        # Play the audio
        stream.write(audio_segment.raw_data)
        
        # Clean up
        stream.stop_stream()
        stream.close()
        p.terminate()
        
    except requests.exceptions.RequestException as e:
        print(f"Network error while fetching audio: {e}")
    except Exception as e:
        print(f"An error occurred with the Murf API or PyAudio: {e}")

def get_text_input(prompt_text: str) -> str:
    """Gets text input from the user via the console."""
    return input(prompt_text).lower()

# --- 3. LLM INTERACTION FUNCTIONS ---
def generate_llm_response(prompt: str) -> str:
    """Sends a prompt to the LLM and returns the text response."""
    try:
        # This is where the updated prompt is applied to get the desired output format
        completion = openrouter_client.chat.completions.create(
          model="openai/gpt-oss-20b:free",
          messages=[
              {
                  "role": "user",
                  "content": prompt
              },
              {
                  "role": "system",
                  "content": "Your responses must be in simple, complete sentences. Avoid using markdown formatting like lists, headings, or tables. Describe ingredients and utensils in a spoken, conversational tone. Example: 'You will need one cup of flour, two teaspoons of baking powder, and half a teaspoon of salt.'"
              }
          ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"An error occurred with the LLM API: {e}"

# --- 4. MAIN CONVERSATIONAL LOOP ---
def run_interactive_cookbook():
    speak("Hello! Welcome to your voice-activated cookbook.")
    
    current_dish = ""
    unavailable_items = []
    
    while True:
        if not current_dish:
            speak("What would you like to cook today?")
            dish_input = get_text_input("You: ")
            if not dish_input:
                continue
            
            current_dish = dish_input
            
            prompt = (
                f"For {current_dish}, list the required ingredients, utensils, "
                f"and the estimated cooking time. Do not include a full recipe yet."
            )
            speak(f"Getting the requirements for {current_dish}...")
            response = generate_llm_response(prompt)
            speak(response)

        speak("Do you have everything you need to cook this dish? (yes/no/something else)")
        user_response = get_text_input("You: ")
        if not user_response:
            continue
        
        if "no" in user_response:
            speak("Please tell me what you are missing.")
            missing_items = get_text_input("You: ")
            if missing_items:
                unavailable_items.append(missing_items)
                
                prompt = (
                    f"I would like to cook {current_dish} but I don't have the following items: {', '.join(unavailable_items)}. "
                    f"Suggest a new dish that I can cook with the ingredients and utensils I do have. "
                    f"List the new dish's required ingredients, utensils, and time, but do not provide the full recipe yet."
                )
                
                speak(f"Okay, finding a new recipe without {missing_items}...")
                new_response = generate_llm_response(prompt)
                speak(new_response)

        elif "yes" in user_response or "cook it" in user_response:
            speak(f"Great! I will now give you the full recipe for {current_dish}.")
            recipe_prompt = (
                f"Give me the full recipe for {current_dish}. Include a list of ingredients and a numbered list of steps."
            )
            full_recipe = generate_llm_response(recipe_prompt)
            speak(full_recipe)
            speak("Enjoy your meal! Let me know if you want to cook something else.")
            
            current_dish = ""
            unavailable_items = []
            
        elif "something else" in user_response or "new dish" in user_response:
            current_dish = ""
            unavailable_items = []
            speak("Alright, let's find something new.")
            
        elif "quit" in user_response or "exit" in user_response or "stop" in user_response:
            speak("Goodbye!")
            sys.exit()

# --- Run the main application ---
if __name__ == "__main__":
    run_interactive_cookbook()
