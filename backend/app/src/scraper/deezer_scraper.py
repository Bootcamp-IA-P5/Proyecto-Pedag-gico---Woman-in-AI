
import requests
from app.src.config.deezer_config import LIMITE_TRACKS

BASE_URL = "https://api.deezer.com"


def obtener_tracks_playlist(playlist_id: str, pais: str) -> list[dict]:
    """
    Descarga los tracks del chart de un país desde Deezer.
    No necesita token — la API de Deezer es pública.

    Mapea cada track a los campos exactos de la tabla songs en Supabase:
      ranking_position, title, artist, streams, genre, lyrics,
      album, year, duration_seg, language_variant, source,
      url_source, extra_data, lyrics_status

    Parámetros:
      chart_id → ID del chart (viene de CHARTS_DEEZER en deezer_config.py)
      pais     → código del país, ej: "PY"

    Retorna lista de dicts listos para insertar en songs.
    """
    respuesta = requests.get(
        f"{BASE_URL}/playlist/{playlist_id}/tracks",
        params={"limit": LIMITE_TRACKS},
        timeout=10
    )
    respuesta.raise_for_status()
    items = respuesta.json().get("data", [])

    tracks = []
    for posicion, track in enumerate(items, start=1):
        # Deezer devuelve el álbum en track["album"]
        album  = track.get("album", {})
        artist = track.get("artist", {})

        tracks.append({
            # ── Columnas exactas de la tabla songs ────────────────────────
            "ranking_position": posicion,
            "title":            track.get("title", ""),
            "artist":           artist.get("name", "Desconocido"),
            "streams":          track.get("rank", 0),   # Deezer da un score de popularidad
            "genre":            None,                    # Deezer no da género por track
            "lyrics":           None,                    # lo rellena lyrics_scraper.py
            "album":            album.get("title", ""),
            "year":             None,                    # Deezer no da año en el chart
            "duration_seg":     track.get("duration", 0),
            "language_variant": None,                    # lo detecta lyrics_scraper.py
            "source":           "deezer",
            "url_source":       track.get("link", ""),
            "lyrics_status":    "pending",               # listo para lyrics_scraper.py
            "extra_data": {
                "deezer_track_id":  track.get("id"),
                "deezer_album_id":  album.get("id"),
                "deezer_artist_id": artist.get("id"),
                "pais":             pais,
                "posicion":         posicion,
            },
            # ── Uso interno — NO van a Supabase ───────────────────────────
            "_posicion":   posicion,
            "_title_raw":  track.get("title", ""),
            "_artist_raw": artist.get("name", "Desconocido"),
        })

    print(f"✅ {len(tracks)} tracks obtenidos de Deezer ({pais})")
    return tracks