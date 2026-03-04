"""
Credenciales y playlists de Spotify. Todo lo de Spotify arranca aquí.
"""
import os, requests
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

PLAYLISTS = {
    "PY": "37i9dQZEVXbMXbN3EUUhlg",
    "ES": "37i9dQZEVXbNFJfN1Vw8d9",
    "MX": "37i9dQZEVXbO3qyFxbkOE1",
    "AR": "37i9dQZEVXbMMy2roB9myp",
    "CO": "37i9dQZEVXbOa2lmxNORXQ",
}

def obtener_token_spotify() -> str:
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise EnvironmentError("❌ Faltan SPOTIFY_CLIENT_ID o SPOTIFY_CLIENT_SECRET en .env")
    respuesta = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=10
    )
    respuesta.raise_for_status()
    print("✅ Token Spotify obtenido")
    return respuesta.json()["access_token"]