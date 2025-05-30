import base64
import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

print(f"Client ID loaded: {'Yes' if os.getenv('SPOTIFY_CLIENT_ID') else 'No'}")
print(f"Client Secret loaded: {'Yes' if os.getenv('SPOTIFY_CLIENT_SECRET') else 'No'}")
print(f"Refresh Token loaded: {'Yes' if os.getenv('SPOTIFY_REFRESH_TOKEN') else 'No'}")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

ACCESS_TOKEN = None

def ensure_token_validity():
    global ACCESS_TOKEN
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET or not REFRESH_TOKEN:
        raise Exception("Missing Spotify credentials. Check your .env file.")
    if ACCESS_TOKEN:
        return
    print("[Spotify] Refreshing access token...")
    auth_str = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
    }
    try:
        response = requests.post(SPOTIFY_TOKEN_URL, data=data, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"[Spotify] Token refresh failed: {e}")
        print("[Spotify] Response content:", response.text)
        raise
    token_data = response.json()
    ACCESS_TOKEN = token_data["access_token"]
    print("[Spotify] Access token refreshed.")

def get_headers():
    if not ACCESS_TOKEN:
        ensure_token_validity()
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

def search_song(query, type="track"):
    search_url = f"https://api.spotify.com/v1/search?q={query}&type={type}&limit=5"
    headers = get_headers()
    response = requests.get(search_url, headers=headers)
    if response.status_code != 200:
        print(f"[Spotify] Search failed: {response.text}")
        return None
    data = response.json()
    return data.get("tracks", {}).get("items", [])

def get_all_playlist_names():
    ensure_token_validity()
    playlists_url = "https://api.spotify.com/v1/me/playlists?limit=50"
    headers = get_headers()
    all_playlists = []
    url = playlists_url
    while url:
        response = requests.get(url, headers=headers)
        print(f"[Spotify] Raw playlist API response: {response.text}")
        if response.status_code != 200:
            print(f"[Spotify] Failed to retrieve playlists: {response.text}")
            return []
        data = response.json()
        items = data.get("items", [])
        all_playlists.extend(items)
        url = data.get("next")
    playlist_names = [playlist["name"] for playlist in all_playlists]
    print("[Spotify] Your playlists:")
    for name in playlist_names:
        print(f"  - {name}")
    return playlist_names

def get_all_song_names_in_playlist(playlist_name):
    ensure_token_validity()
    playlists_url = "https://api.spotify.com/v1/me/playlists"
    headers = get_headers()
    playlist_id = None
    url = playlists_url
    while url and not playlist_id:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"[Spotify] Failed to retrieve playlists: {response.text}")
            return []
        data = response.json()
        for playlist in data.get("items", []):
            if playlist["name"].lower() == playlist_name.lower():
                playlist_id = playlist["id"]
                break
        url = data.get("next")
    if not playlist_id:
        print(f"[Spotify] Playlist '{playlist_name}' not found.")
        return []
    # Now, get all tracks in the playlist
    tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    song_names = []
    url = tracks_url
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"[Spotify] Failed to retrieve tracks: {response.text}")
            return []
        data = response.json()
        for item in data.get("items", []):
            track = item.get("track")
            if track and track.get("name"):
                song_names.append(track["name"])
        url = data.get("next")
    print(f"[Spotify] Songs in playlist '{playlist_name}':")
    for name in song_names:
        print(f"  - {name}")
    return song_names

def print_token_scopes():
    ensure_token_validity()
    headers = get_headers()
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    if response.status_code == 200:
        print(f"[Spotify] Token scopes: {response.headers.get('scope', 'unknown')}")
        print(f"[Spotify] User info: {response.text}")
    else:
        print(f"[Spotify] Failed to get user info: {response.text}")

def create_playlist(name, description="", public=False):
    ensure_token_validity()
    headers = get_headers()

    # Get user ID first
    user_profile = requests.get("https://api.spotify.com/v1/me", headers=headers)
    if user_profile.status_code != 200:
        print(f"[Spotify] Failed to get user profile: {user_profile.text}")
        return None
    user_id = user_profile.json()["id"]

    # Create playlist
    payload = {
        "name": name,
        "description": description,
        "public": public
    }
    response = requests.post(
        f"https://api.spotify.com/v1/users/{user_id}/playlists",
        headers=headers,
        json=payload
    )
    if response.status_code == 201:
        playlist = response.json()
        print(f"[Spotify] Created playlist '{name}' with ID: {playlist['id']}")
        return playlist["id"]
    else:
        print(f"[Spotify] Failed to create playlist: {response.text}")
        return None

def get_playlist_id_by_name(playlist_name):
    ensure_token_validity()
    headers = get_headers()
    url = "https://api.spotify.com/v1/me/playlists"
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"[Spotify] Failed to retrieve playlists: {response.text}")
            return None
        data = response.json()
        for playlist in data.get("items", []):
            if playlist["name"].lower() == playlist_name.lower():
                return playlist["id"]
        url = data.get("next")
    print(f"[Spotify] Playlist '{playlist_name}' not found.")
    return None

def search_track_uri(song_name, artist_name=None):
    ensure_token_validity()
    headers = get_headers()
    query = f"track:{song_name}"
    if artist_name:
        query += f" artist:{artist_name}"
    url = f"https://api.spotify.com/v1/search?q={requests.utils.quote(query)}&type=track&limit=1"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"[Spotify] Failed to search track: {response.text}")
        return None
    results = response.json()
    tracks = results.get("tracks", {}).get("items", [])
    if tracks:
        return tracks[0]["uri"]
    print(f"[Spotify] No results for: {song_name} by {artist_name}")
    return None

def add_track_to_playlist(playlist_id, track_uri):
    ensure_token_validity()
    headers = get_headers()

    payload = {
        "uris": [track_uri]  # track_uri format: "spotify:track:..."
    }
    response = requests.post(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
        headers=headers,
        json=payload
    )
    if response.status_code == 201:
        print(f"[Spotify] Added track {track_uri} to playlist {playlist_id}")
        return True
    else:
        print(f"[Spotify] Failed to add track: {response.text}")
        return False

def add_track_to_playlist_by_name(playlist_name, song_name, artist_name=None):
    playlist_id = get_playlist_id_by_name(playlist_name)
    if not playlist_id:
        return False
    track_uri = search_track_uri(song_name, artist_name)
    if not track_uri:
        return False
    return add_track_to_playlist(playlist_id, track_uri)



def get_playlist_id_by_name_og(playlist_name):
    playlists_url = "https://api.spotify.com/v1/me/playlists"
    headers = get_headers()
    all_playlists = []
    url = playlists_url
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"[Spotify] Failed to retrieve playlists: {response.text}")
            return None
        data = response.json()
        items = data.get("items", [])
        all_playlists.extend(items)
        url = data.get("next")  # Spotify paginates playlists
    print("[Spotify] Available playlists:")
    found = False
    for playlist in all_playlists:
        print(f"  - {playlist['name']}")
        if playlist["name"].lower() == playlist_name.lower():
            found = True
            return playlist["id"]
    if not found:
        print(f"[Spotify] Playlist '{playlist_name}' not found.")
    return None

def create_playlist_og(playlist_name, description="Created by Aziz's Spotify Chatbot", public=False):
    create_url = "https://api.spotify.com/v1/me/playlists"
    headers = get_headers()
    data = {
        "name": playlist_name,
        "description": description,
        "public": public
    }
    response = requests.post(create_url, headers=headers, json=data)
    if response.status_code not in (200, 201):
        print(f"[Spotify] Failed to create playlist: {response.text}")
        return None
    playlist = response.json()
    print(f"[Spotify] Created playlist '{playlist_name}' with ID {playlist['id']}")
    return playlist["id"]

def add_tracks_to_playlist_og(playlist_id, track_uris):
    add_tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = get_headers()
    data = {
        "uris": track_uris
    }
    response = requests.post(add_tracks_url, json=data, headers=headers)
    if response.status_code != 201:
        print(f"[Spotify] Failed to add tracks: {response.text}")
        return False
    print(f"[Spotify] Successfully added tracks to playlist {playlist_id}.")
    return True
