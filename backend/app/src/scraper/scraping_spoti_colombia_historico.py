import time
import requests
from app.src.config.spotify_config import obtener_token_spotify
from app.src.processor.upload_to_supabase import guardar_cancion
from app.src.processor.normalizer import normalizar_track, reset_sesion

PAIS = "CO"
PAIS_NOMBRE = "Colombia"

def buscar_canciones_colombianas(token: str) -> list[dict]:
    # Estrategia de 'Ataque profundo y ancho': Buscando multiplicidad de géneros hasta offset 400.
    queries = [
        "genre:reggaeton colombia",
        "genre:vallenato",
        "genre:champeta",
        "genre:cumbia",
        "genre:merengue",
        "genre:bachata",
        "genre:salsa colombia",
        "genre:latin pop",
        "genre:latin trap",
        "genre:urbano",
        "colombia viral 2026",
        "colombia viral 2025"
    ]

    tracks_totales = []

    for query in queries:
        print(f"\n🔎 Buscando Tracks (Spotify Search): '{query}'")
        # Extendemos el offset considerablemente para esquivar los duplicados recurrentes
        for offset in range(0, 400, 10):
            intento = 0
            respuesta = None
            while intento < 2:
                respuesta = requests.get(
                    "https://api.spotify.com/v1/search",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"q": query, "type": "track", "limit": 10, "offset": offset, "market": PAIS},
                    timeout=10,
                )
                if respuesta.status_code == 200:
                    break

                try:
                    cuerpo_respuesta = respuesta.text[:200]
                except Exception:
                    cuerpo_respuesta = "<no se pudo leer cuerpo de respuesta>"

                if respuesta.status_code == 401:
                    print("[INFO] Token expirado. Intentando renovarlo...")
                    token = obtener_token_spotify()
                    intento += 1
                    continue

                if respuesta.status_code == 429:
                    retry_after = respuesta.headers.get("Retry-After")
                    espera = int(retry_after) if retry_after else 5
                    print(f"[INFO] Rate limit. Esperando {espera}s...")
                    time.sleep(espera)
                    intento += 1
                    continue

                break

            if respuesta is None or respuesta.status_code != 200:
                continue

            items = respuesta.json().get("tracks", {}).get("items", [])
            # Si en algún offset ya no hay resultados de este género, pasamos al siguiente género.
            if not items:
                break

            for track in items:
                if not track:
                    continue
                
                artista_principal = track["artists"][0]["name"] if track["artists"] else "Desconocido"
                release_date = track["album"].get("release_date", "")

                track_data = {
                    "title": track["name"],
                    "artist": artista_principal,
                    "streams": track.get("popularity", 0),
                    "genre": None, 
                    "album": track["album"]["name"],
                    "year": int(release_date[:4]) if len(release_date) >= 4 else None,
                    "duration_seg": track["duration_ms"] // 1000,
                    "language_variant": None,
                    "source": "spotify_search",
                    "url_source": track["external_urls"].get("spotify", ""),
                    "lyrics_status": "pending",
                    "extra_data": {
                        "spotify_track_id": track["id"],
                        "todos_artistas": ", ".join([a["name"] for a in track["artists"]]),
                        "pais": PAIS
                    },
                    "_title_raw": track["name"],
                    "_artist_raw": artista_principal,
                }
                tracks_totales.append(track_data)
                
            time.sleep(1)  # Respetando Rate Limits de Spotify Search API

    print(f"\n✅ Se recolectaron {len(tracks_totales)} tracks en bruto listos para IA.")
    return tracks_totales


def ejecutar_subida_colombiana():
    print(f"\n🇨🇴  Subida Masiva Multigénero {PAIS_NOMBRE} — Spotify")
    print("=" * 50)

    reset_sesion()
    token = obtener_token_spotify()

    tracks = buscar_canciones_colombianas(token)

    nuevas = existentes = ignoradas = fallidas = 0
    vistos = set()

    for track in tracks:
        key = f"{track['artist']} - {track['title']}".lower()
        if key in vistos:
            continue
        vistos.add(key)

        print(f"\n⚙️  Procesando: {track['artist']} - {track['title']}")

        try:
            track_normalizado = normalizar_track(track)
            if track_normalizado is None:
                print(f"   ⏭️  Ignorado (fuera de regla o duplicado)")
                ignoradas += 1
                continue

            song_id, es_nueva = guardar_cancion(track_normalizado)
            if es_nueva:
                nuevas += 1
            else:
                existentes += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            fallidas += 1

        time.sleep(2.5)

    print("\n" + "=" * 50)
    print(f"✅ Subida {PAIS_NOMBRE} completada")
    print(f"   🆕 Canciones nuevas insertadas : {nuevas}")
    print(f"   🔄 Ya existían (actualizadas)  : {existentes}")
    print(f"   ⚠️  Ignoradas por IA/filtro      : {ignoradas}")
    print(f"   ❌ Fallidas con error          : {fallidas}")
    print("=" * 50)

if __name__ == "__main__":
    ejecutar_subida_colombiana()
