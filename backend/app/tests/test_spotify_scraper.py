"""
Archivo: backend/app/tests/test_spotify_scraper.py

Prueba rápida para verificar que Spotify responde correctamente.

✅ NO toca Supabase
✅ Necesita SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET en backend/.env

Cómo ejecutarlo (desde backend/):
  uv run python -m app.tests.test_spotify_scraper

Qué verás si funciona:
  - Los primeros 5 tracks del Top 50 Paraguay de Spotify
  - Todos los campos que se guardarían en songs
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Carga el .env de backend/ sin importar desde dónde se ejecute el script
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


# ─── Configuración del test ───────────────────────────────────────────────────

PLAYLIST_ID_PARAGUAY = "37i9dQZEVXbMXbN3EUUhlg"   # Top 50 Paraguay en Spotify
PAIS                 = "PY"
LIMITE_TEST          = 5


def _obtener_token() -> str | None:
    """Obtiene el token de Spotify. Devuelve None si falla."""
    client_id     = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("❌ Faltan SPOTIPY_CLIENT_ID o SPOTIPY_CLIENT_SECRET en backend/.env")
        return None

    try:
        respuesta = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=10
        )
        respuesta.raise_for_status()
        return respuesta.json()["access_token"]
    except Exception as e:
        print(f"❌ Error obteniendo token: {e}")
        return None


def _obtener_tracks(token: str) -> list:
    """Llama a Spotify y devuelve los tracks. Función interna compartida."""
    respuesta = requests.get(
        f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID_PARAGUAY}/tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "limit":  LIMITE_TEST,
            "fields": "items(track(id,name,artists,album,duration_ms,popularity,external_urls))"
        },
        timeout=10
    )
    respuesta.raise_for_status()
    return respuesta.json().get("items", [])


# ─── Test 1: ¿Las credenciales funcionan? ────────────────────────────────────

def test_credenciales_spotify() -> str | None:
    """Comprueba que el CLIENT_ID y CLIENT_SECRET son válidos."""
    print("\n🔑 TEST 1 — Credenciales Spotify")
    print("-" * 40)

    token = _obtener_token()
    if token:
        print(f"✅ Token obtenido correctamente")
        print(f"   Token (primeros 20 chars): {token[:20]}...")
        return token
    return None


# ─── Test 2: ¿Spotify devuelve tracks? ───────────────────────────────────────

def test_conexion_spotify(token: str) -> bool:
    """Comprueba que la playlist de Paraguay es accesible."""
    print("\n🔌 TEST 2 — Conexión con Spotify")
    print("-" * 40)

    try:
        items = _obtener_tracks(token)
        if items:
            print(f"✅ Spotify responde correctamente")
            print(f"   {len(items)} tracks recibidos")
            return True
        else:
            print("❌ Spotify devolvió una lista vacía")
            return False

    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e}")
        return False
    except requests.exceptions.Timeout:
        print("❌ Spotify tardó demasiado en responder")
        return False


# ─── Test 3: ¿Los datos tienen la forma correcta? ────────────────────────────

def test_estructura_tracks(token: str) -> bool:
    """
    Comprueba que los tracks tienen todos los campos
    que necesita la tabla songs en Supabase.
    """
    print("\n📋 TEST 3 — Estructura de los tracks")
    print("-" * 40)

    items = _obtener_tracks(token)

    if not items:
        print("❌ Sin tracks para verificar")
        return False

    campos_requeridos = [
        "ranking_position", "title", "artist",
        "streams", "source", "lyrics_status", "extra_data",
    ]

    errores = 0
    for posicion, item in enumerate(items, start=1):
        track  = item.get("track", {})
        album  = track.get("album", {})
        artist = track["artists"][0] if track.get("artists") else {}
        release_date = album.get("release_date", "")

        fila = {
            "ranking_position": posicion,
            "title":            track.get("name", ""),
            "artist":           artist.get("name", "Desconocido"),
            "streams":          track.get("popularity", 0),
            "genre":            None,
            "lyrics":           None,
            "album":            album.get("title", ""),
            "year":             int(release_date[:4]) if len(release_date) >= 4 else None,
            "duration_seg":     track.get("duration_ms", 0) // 1000,
            "language_variant": None,
            "source":           "spotify",
            "url_source":       track.get("external_urls", {}).get("spotify", ""),
            "lyrics_status":    "pending",
            "extra_data": {
                "spotify_track_id": track.get("id"),
                "pais":             PAIS,
                "posicion":         posicion,
            },
        }

        for campo in campos_requeridos:
            if not fila.get(campo) and fila.get(campo) != 0:
                print(f"  ⚠️  Posición {posicion}: '{campo}' está vacío")
                errores += 1

    if errores == 0:
        print("✅ Todos los campos requeridos tienen datos")
    else:
        print(f"⚠️  {errores} campos vacíos detectados")

    return errores == 0


# ─── Test 4: Mostrar los datos en consola ────────────────────────────────────

def test_mostrar_tracks(token: str):
    """Muestra los primeros 5 tracks tal como se guardarían en Supabase."""
    print(f"\n🎵 TEST 4 — Primeros {LIMITE_TEST} tracks del Top {PAIS}")
    print("-" * 40)

    items = _obtener_tracks(token)

    for posicion, item in enumerate(items, start=1):
        track  = item.get("track", {})
        album  = track.get("album", {})
        artist = track["artists"][0] if track.get("artists") else {}
        release_date = album.get("release_date", "")

        print(f"\n  #{posicion}")
        print(f"  title        : {track.get('name')}")
        print(f"  artist       : {artist.get('name')}")
        print(f"  album        : {album.get('name')}")
        print(f"  year         : {release_date[:4] if release_date else 'N/A'}")
        print(f"  duration_seg : {track.get('duration_ms', 0) // 1000}s")
        print(f"  streams      : {track.get('popularity')}")
        print(f"  source       : spotify")
        print(f"  lyrics_status: pending")
        print(f"  url_source   : {track.get('external_urls', {}).get('spotify', '')}")


# ─── Ejecutar todos los tests ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 40)
    print("🧪 PRUEBA — Spotify Scraper (sin Supabase)")
    print("=" * 40)

    # Test 1 — credenciales
    token = test_credenciales_spotify()

    if token:
        # Test 2 — conexión
        ok2 = test_conexion_spotify(token)

        if ok2:
            # Test 3 — estructura
            ok3 = test_estructura_tracks(token)

            # Test 4 — mostrar datos
            test_mostrar_tracks(token)

            print("\n" + "=" * 40)
            if ok3:
                print("✅ Todo correcto — puedes ejecutar scraping_spoti_paraguay.py")
            else:
                print("⚠️  Revisa los warnings antes de ejecutar el scraper real")
    else:
        print("\n❌ Corrige las credenciales en backend/.env antes de continuar")

    print("=" * 40)