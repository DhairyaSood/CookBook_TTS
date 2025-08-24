import os
import sys
from openai import OpenAI
from flask import Flask, request, jsonify, render_template, session

# --- 1. API KEY & CLIENT SETUP ---
# Make sure to set these environment variables in your system
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
MURF_API_KEY = os.environ.get('MURF_API_KEY')

if not OPENROUTER_API_KEY:
    print("Error: The OPENROUTER_API_KEY environment variable is not set.")
    sys.exit()

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

app = Flask(__name__, static_folder='static', template_folder='.')
app.secret_key = 'super_secret_key_for_session_management' # Needed for session

# --- 2. LLM INTERACTION FUNCTION ---
def generate_llm_response(prompt: str) -> str:
    """Sends a prompt to the LLM and returns the text response."""
    try:
        completion = openrouter_client.chat.completions.create(
          model="openai/gpt-3.5-turbo", # Using a standard model
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

# --- 3. WEB ROUTES ---
@app.route('/')
def index():
    """Render the main chat page."""
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_conversation():
    """Initializes the conversation state."""
    session['current_dish'] = ""
    session['unavailable_items'] = []
    session['state'] = 'initial' # 'initial', 'awaiting_confirmation', 'awaiting_missing_items'
    return jsonify({"reply": "Hello! Welcome to your voice-activated cookbook. What would you like to cook today?"})


@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint to handle the conversation logic."""
    user_input = request.json.get('message', '').lower()
    state = session.get('state', 'initial')
    current_dish = session.get('current_dish', "")
    unavailable_items = session.get('unavailable_items', [])
    reply = ""

    if state == 'initial':
        if not user_input:
            reply = "Please tell me what you would like to cook."
        else:
            current_dish = user_input
            session['current_dish'] = current_dish
            prompt = (
                f"For {current_dish}, list the required ingredients, utensils, "
                f"and the estimated cooking time. Do not include a full recipe yet."
            )
            reply = f"Getting the requirements for {current_dish}... "
            reply += generate_llm_response(prompt)
            reply += "\nDo you have everything you need to cook this dish?"
            session['state'] = 'awaiting_confirmation'

    elif state == 'awaiting_confirmation':
        if "yes" in user_input or "cook it" in user_input:
            recipe_prompt = f"Give me the full recipe for {current_dish}. Include a list of ingredients and a numbered list of steps."
            full_recipe = generate_llm_response(recipe_prompt)
            reply = f"Great! Here is the full recipe for {current_dish}.\n" + full_recipe
            reply += "\nEnjoy your meal! Let me know if you want to cook something else."
            session['state'] = 'initial'
            session['current_dish'] = ""

        elif "no" in user_input:
            reply = "Please tell me what you are missing."
            session['state'] = 'awaiting_missing_items'

        else:
            reply = "Sorry, I didn't understand. Do you have all the ingredients? (yes/no)"

    elif state == 'awaiting_missing_items':
        missing_items = user_input
        unavailable_items.append(missing_items)
        session['unavailable_items'] = unavailable_items
        prompt = (
            f"I would like to cook {current_dish} but I don't have: {', '.join(unavailable_items)}. "
            f"Suggest a new dish. List the new dish's required ingredients, utensils, and time, but not the full recipe yet."
        )
        reply = f"Okay, finding a new recipe without {missing_items}... "
        new_dish_suggestion = generate_llm_response(prompt)
        reply += new_dish_suggestion
        reply += "\nDo you want to cook this new dish?"
        # The logic would need to be expanded here to parse the new dish name from the response
        # For simplicity, we'll reset to a state where the user can confirm
        session['state'] = 'awaiting_confirmation'


    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)