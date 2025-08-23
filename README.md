# 🎙️ Voice-Activated Cookbook

An interactive, **voice-enabled AI cookbook** that helps you decide what to cook, lists ingredients and utensils, and reads recipes out loud.  
This project uses:
- **OpenRouter (LLM API)** for recipe instructions.
- **Murf API** for natural-sounding text-to-speech (TTS).
- **PyAudio + Pydub** for local audio playback.

---

## 🚀 Features
- Ask what you want to cook and get ingredients, utensils, and time estimates.
- Handles missing items and suggests alternative dishes.
- Speaks responses back using **Murf AI voices**.
- Interactive conversational flow in your terminal.

---

## 📦 Requirements
- Python 3.8+
- `requirements.txt` dependencies:
  ```bash
  pip install -r requirements.txt
