import time
import requests
from datetime import datetime
from app.src.config.spotify_config import obtener_token_spotify
from app.src.processor.upload_to_supabase import guardar_cancion
from app.src.processor.normalizer import normalizar_track, reset_sesion
from app.src.scraper.spotify_scraper import obtener_tracks_playlist

PAIS = "CO"
PAIS_NOMBRE = "Colombia"


def buscar_canciones_colombianas(token: str) -> list[dict]:
    # Debido a las nuevas políticas de Spotify (Error 403 en Playlists públicas de terceros),
    # debemos buscar las canciones directamente, simulando las playlists mediante queries avanzadas.
    queries = [
        "colombia viral",
        "éxitos colombia 2025",
        "éxitos colombia 2024",
        "genre:vallenato year:2024-2026",
        "genre:champeta year:2024-2026",
        "genre:reggaeton colombia",
    ]

    tracks_totales = []

    for query in queries:
        print(f"\n🔎 Buscando directamente Tracks (simulando playlist): '{query}'")
        # Offset ampliado para no traer siempre los mismos resultados de la primera página
        for offset in [0, 10, 20, 30, 40]:  
            respuesta = requests.get(
                "https://api.spotify.com/v1/search",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": query, "type": "track", "limit": 10, "offset": offset, "market": PAIS},
                timeout=10,
            )
            if respuesta.status_code != 200:
                continue

            items = respuesta.json().get("tracks", {}).get("items", [])
            if not items:
                break

            for index, track in enumerate(items, start=1):
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
                
            time.sleep(1)  # Respetar limites de API

    print(f"\n✅ Se recolectaron {len(tracks_totales)} tracks en bruto usando {len(queries)} consultas virales.")
    return tracks_totales


def ejecutar_subida_colombiana():
    print(f"\n🇨🇴  Subida Histórica/Viral {PAIS_NOMBRE} — Spotify (Por Playlists)")
    print("=" * 50)

    reset_sesion()
    token = obtener_token_spotify()

    tracks = buscar_canciones_colombianas(token)

    nuevas = existentes = ignoradas = fallidas = 0
    vistos = set()

    for track in tracks:
        # Remover duplicados en bruto rápidamente
        key = f"{track['artist']} - {track['title']}".lower()
        if key in vistos:
            continue
        vistos.add(key)

        print(f"\n⚙️  Procesando: {track['artist']} - {track['title']}")

        try:
            # Paso por el embudo de IA
            track_normalizado = normalizar_track(track)

            if track_normalizado is None:
                print(f"   ⏭️  Ignorado por el normalizador (fuera de regla o duplicado)")
                ignoradas += 1
                continue

            # Upsert en DB usando función oficial maestra
            song_id, es_nueva = guardar_cancion(track_normalizado)

            if es_nueva:
                nuevas += 1
            else:
                existentes += 1

        except Exception as e:
            print(f"   ❌ Error guardando: {e}")
            fallidas += 1

        # Respetar Rate limit para IA (2 a 3 segundos)
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
