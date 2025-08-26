import os
import sys
import base64
import traceback
import requests
from flask import Flask, request, render_template, jsonify
from openai import OpenAI
from murf import Murf

# -----------------------
# App + config
# -----------------------
app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
MURF_API_KEY = os.environ.get("MURF_API_KEY")
MURF_VOICE_ID = os.environ.get("MURF_VOICE_ID", "en-US-natalie")  # default voice

if not OPENROUTER_API_KEY:
    print("Error: OPENROUTER_API_KEY is not set.", file=sys.stderr)
    sys.exit(1)
if not MURF_API_KEY:
    print("Error: MURF_API_KEY is not set.", file=sys.stderr)
    sys.exit(1)

# OpenRouter client (LLM)
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Murf client (TTS)
murf_client = Murf(api_key=MURF_API_KEY)


# -----------------------
# Core helpers
# -----------------------
def generate_llm_response(prompt: str) -> str:
    """Generate a conversational cookbook response from OpenRouter."""
    try:
        completion = openrouter_client.chat.completions.create(
            model="openai/gpt-oss-20b:free",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a friendly voice cookbook. "
                        "Speak in simple, complete sentences without markdown lists, headings, or tables. "
                        "Describe ingredients and utensils conversationally. "
                        "Example: 'You will need one cup of flour, two teaspoons of baking powder, "
                        "and half a teaspoon of salt.'"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        return (completion.choices[0].message.content or "").strip()
    except Exception as e:
        traceback.print_exc()
        return f"An error occurred with the LLM API: {e}"


def text_to_murf_mp3_bytes(text: str) -> bytes:
    """Convert text to speech using Murf TTS and return raw MP3 bytes."""
    try:
        audio_res = murf_client.text_to_speech.generate(
            text=text,
            voice_id=MURF_VOICE_ID,
        )
        audio_url = getattr(audio_res, "audio_file", None)
        if not audio_url:
            raise RuntimeError("Murf did not return an audio_file URL.")

        r = requests.get(audio_url, timeout=60)
        r.raise_for_status()
        return r.content
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"Murf TTS failed: {e}") from e


# -----------------------
# Routes
# -----------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/text", methods=["POST"])
def text_route():
    """Accepts JSON {query}, returns {text, audio(base64)}."""
    try:
        data = request.get_json(silent=True) or {}
        query = (data.get("query") or "").strip()
        if not query:
            return jsonify({"error": "No query provided."}), 400

        # Generate text response
        response_text = generate_llm_response(query)
        if not response_text or response_text.startswith("An error occurred with the LLM API"):
            return jsonify({"error": response_text}), 502

        # Generate audio
        try:
            mp3_bytes = text_to_murf_mp3_bytes(response_text)
            audio_b64 = base64.b64encode(mp3_bytes).decode("utf-8")
        except Exception as tts_err:
            # Still return text if audio fails
            return jsonify({
                "text": response_text,
                "error": str(tts_err)
            }), 502

        return jsonify({
            "text": response_text,
            "audio": audio_b64
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Server error: {e}"}), 500


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Route not found."}), 404


@app.errorhandler(405)
def method_not_allowed(_):
    return jsonify({"error": "Method not allowed."}), 405


# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
