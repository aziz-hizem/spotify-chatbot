import os
import logging
import json
import requests
from .spotify_api import search_song, get_playlist_id_by_name, add_tracks_to_playlist, create_playlist

# Setup logging to ensure output is visible in the terminal
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions" 

PROMPT_TEMPLATE = """
You are a helpful assistant for managing Spotify playlists.

### Examples:
User message: Add the song "Shape of You" to my playlist called "Chill Vibes"
Response:
{{
  "intent": "add_songs_to_playlist",
  "playlist_name": "Chill Vibes",
  "songs": ["Shape of You"]
}}

User message: Add these songs: blinding lights, una mattina to my spotify playlist called "test"
Response:
{{
  "intent": "add_songs_to_playlist",
  "playlist_name": "test",
  "songs": ["blinding lights", "una mattina"]
}}

User message: What's the weather today?
Response:
{{
  "intent": "unknown"
}}

### Now, analyze the following message and respond ONLY with the JSON object as shown above.

User message: {message}
"""

def call_llm(message):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a Spotify assistant that responds only with valid JSON."},
            {"role": "user", "content": PROMPT_TEMPLATE.format(message=message)}
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        api_response = response.json()

        # Defensive: check structure
        content = api_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            logging.error("No content in LLM response.")
            return {"intent": "unknown", "error": "No content in LLM response"}
        return json.loads(content)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse LLM response as JSON: {e}")
        return {"intent": "unknown", "error": "Failed to parse LLM response"}
    except Exception as e:
        logging.error(f"Exception in call_llm: {e}")
        return {"intent": "unknown", "error": str(e)}

def process_user_input(message):
    llm_response = call_llm(message)
    try:
        intent = llm_response.get("intent")
        if intent == "add_songs_to_playlist":
            playlist = llm_response.get("playlist_name")
            songs = llm_response.get("songs")
            if not playlist or not songs:
                return "Missing playlist name or songs in the request."
            playlist_id = get_playlist_id_by_name(playlist)
            if not playlist_id:
                # Try to create the playlist if not found
                playlist_id = create_playlist(playlist)
                if not playlist_id:
                    return f"Failed to create playlist '{playlist}'."
            uris = []
            for song in songs:
                search_results = search_song(song)
                if search_results and len(search_results) > 0:
                    uris.append(search_results[0]["uri"])
            if not uris:
                return "No valid songs found."
            success = add_tracks_to_playlist(playlist_id, uris)
            if success:
                return f"Added {len(uris)} song(s) to '{playlist}'."
            return "Failed to add songs."
        return f"I didn't understand that request.\nIntent: {intent}.\nLLM raw: {llm_response}\nTry asking me to add songs to a playlist."
    except Exception as e:
        logging.error(f"Exception in process_user_input: {e}")
        return f"Failed to process input: {e}"
