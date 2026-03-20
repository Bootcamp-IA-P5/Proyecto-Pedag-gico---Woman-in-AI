# backend/app/tests/test_spotify_scraper.py
import os
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

PLAYLIST_ID_PUBLICA = "37i9dQZF1DX4JAvHpjipBk"
LIMITE_TEST = 5

def _obtener_token() -> str | None:
    client_id     = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    try:
        respuesta = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=10,
        )
        respuesta.raise_for_status()
        return respuesta.json()["access_token"]
    except Exception:
        return None

def _obtener_tracks(token: str) -> list:
    respuesta = requests.get(
        f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID_PUBLICA}/tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": LIMITE_TEST, "fields": "items(track(id,name,artists,album,duration_ms,popularity,external_urls))"},
        timeout=10,
    )
    respuesta.raise_for_status()
    return respuesta.json().get("items", [])


# ── fixture: crea el token una sola vez y lo comparte ──────────────────────────
@pytest.fixture
def token() -> str:
    """Se salta si no hay credenciales en el entorno."""
    t = _obtener_token()
    if not t:
        pytest.skip("Credenciales Spotify no disponibles en este entorno")
    return t


# ── Test 1 ─────────────────────────────────────────────────────────────────────
@pytest.mark.skipif(not os.getenv("SPOTIPY_CLIENT_ID") or not os.getenv("SPOTIPY_CLIENT_SECRET"), reason="Credenciales Spotify no configuradas")
def test_credenciales_spotify():
    """Verifica que las variables de entorno de Spotify están presentes."""
    client_id     = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    assert client_id is not None, "Falta SPOTIPY_CLIENT_ID en variables de entorno"
    assert client_secret is not None, "Falta SPOTIPY_CLIENT_SECRET en variables de entorno"