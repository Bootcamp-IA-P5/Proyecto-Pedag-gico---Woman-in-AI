"""
Credenciales y playlists de Spotify. Todo lo de Spotify arranca aquí.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SPOTIPY_CLIENT_ID     = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

PLAYLISTS = {
    "PY": "2zAOW5gr26b3NjeGGyF22f",
    "ES": "37i9dQZEVXbNFJfN1Vw8d9",
    "MX": "37i9dQZEVXbO3qyFxbkOE1",
    "AR": "37i9dQZEVXbMMy2roB9myp",
    "CO": "37i9dQZEVXbOa2lmxNORXQ",
}

def obtener_token_spotify() -> str:
    if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
        raise EnvironmentError("❌ Faltan SPOTIPY_CLIENT_ID o SPOTIPY_CLIENT_SECRET en .env")
    respuesta = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET),
        timeout=10
    )
    respuesta.raise_for_status()
    print("✅ Token Spotify obtenido")
    return respuesta.json()["access_token"]
if __name__ == "__main__":
    token = obtener_token_spotify()
    print("TOKEN:", token[:30], "...")