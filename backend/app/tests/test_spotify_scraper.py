import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde backend/
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# ─── Configuración ────────────────────────────────────────────
# Playlist pública de prueba (accesible con client_credentials)
PLAYLIST_ID_PUBLICA = "37i9dQZF1DX4JAvHpjipBk"  # Ejemplo: Latin Pop
PAIS                = "PY"
LIMITE_TEST         = 5

# ─── Obtener token ─────────────────────────────────────────────
def _obtener_token() -> str | None:
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

# ─── Obtener tracks ───────────────────────────────────────────
def _obtener_tracks(token: str) -> list:
    respuesta = requests.get(
        f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID_PUBLICA}/tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "limit":  LIMITE_TEST,
            "fields": "items(track(id,name,artists,album,duration_ms,popularity,external_urls))"
        },
        timeout=10
    )
    respuesta.raise_for_status()
    return respuesta.json().get("items", [])

# ─── Test 1: Credenciales ─────────────────────────────────────
def test_credenciales_spotify() -> str | None:
    print("\n🔑 TEST 1 — Credenciales Spotify")
    print("-" * 40)
    token = _obtener_token()
    if token:
        print(f"✅ Token obtenido correctamente (primeros 20 chars): {token[:20]}...")
        return token
    return None

# ─── Test 2: Conexión ─────────────────────────────────────────
def test_conexion_spotify(token: str) -> bool:
    print("\n🔌 TEST 2 — Conexión con Spotify")
    print("-" * 40)
    try:
        items = _obtener_tracks(token)
        if items:
            print(f"✅ Spotify responde correctamente, {len(items)} tracks recibidos")
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

# ─── Test 3: Mostrar tracks ───────────────────────────────────
def test_mostrar_tracks(token: str):
    print(f"\n🎵 TEST 3 — Primeros {LIMITE_TEST} tracks del Top {PAIS}")
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
        print("  source       : spotify")
        print(f"  url_source   : {track.get('external_urls', {}).get('spotify', '')}")

# ─── Ejecutar tests ───────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 40)
    print("🧪 PRUEBA — Spotify Scraper Final (sin Supabase)")
    print("=" * 40)

    token = test_credenciales_spotify()
    if token:
        ok2 = test_conexion_spotify(token)
        if ok2:
            test_mostrar_tracks(token)
            print("\n✅ Todo correcto — puedes ejecutar tu scraper real")
        else:
            print("\n⚠️  Problema conectando con Spotify")
    else:
        print("\n❌ Corrige las credenciales en backend/.env antes de continuar")
    print("=" * 40)