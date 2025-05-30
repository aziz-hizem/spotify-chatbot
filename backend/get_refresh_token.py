"""
One-time helper to get a Spotify refresh token for the chatbot.

1. Put SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in backend/.env
   (and add the redirect URI below to your app in the Spotify Developer Dashboard).
2. Run this script without arguments and open the printed URL to authorize the app.
3. Copy the "code" parameter from the URL you are redirected to and run:
       python backend/get_refresh_token.py <code>
4. Put the printed refresh_token in backend/.env as SPOTIFY_REFRESH_TOKEN.
"""
import base64
import os
import sys
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://127.0.0.1:8000/callback")
TOKEN_URL = "https://accounts.spotify.com/api/token"
SCOPES = "playlist-modify-private playlist-modify-public playlist-read-private user-read-private"

if len(sys.argv) < 2:
    params = {"client_id": CLIENT_ID, "response_type": "code", "redirect_uri": REDIRECT_URI, "scope": SCOPES}
    print("Open this URL, authorize the app, then rerun with the code from the redirect URL:")
    print("https://accounts.spotify.com/authorize?" + urlencode(params))
    sys.exit(0)

AUTHORIZATION_CODE = sys.argv[1]

auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
b64_auth = base64.b64encode(auth_str.encode()).decode()

headers = {
    "Authorization": f"Basic {b64_auth}",
    "Content-Type": "application/x-www-form-urlencoded"
}

data = {
    "grant_type": "authorization_code",
    "code": AUTHORIZATION_CODE,
    "redirect_uri": REDIRECT_URI
}

response = requests.post(TOKEN_URL, headers=headers, data=data)

print(response.json())
