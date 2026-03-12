"""
backend/app/src/scraper/spotify_scraper.py
Solo descarga tracks de Spotify. No toca Supabase.
"""
import requests

def obtener_tracks_playlist(token: str, playlist_id: str, pais: str) -> list[dict]:
    respuesta = requests.get(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 50, "fields": "items(track(id,name,artists,album,duration_ms,popularity,external_urls))"},
        timeout=10
    )
    respuesta.raise_for_status()
    tracks = []
    for posicion, item in enumerate(respuesta.json().get("items", []), start=1):
        track = item.get("track")
        if not track:
            continue
        artista_principal = track["artists"][0]["name"] if track["artists"] else "Desconocido"
        release_date      = track["album"].get("release_date", "")
        tracks.append({
            "ranking_position": posicion,
            "title":            track["name"],
            "artist":           artista_principal,
            "streams":          track["popularity"],
            "genre":            None,
            "lyrics":           None,
            "album":            track["album"]["name"],
            "year":             int(release_date[:4]) if len(release_date) >= 4 else None,
            "duration_seg":     track["duration_ms"] // 1000,
            "language_variant": None,
            "source":           "spotify",
            "url_source":       track["external_urls"].get("spotify", ""),
            "lyrics_status":    "pending",
            "extra_data":       {"spotify_track_id": track["id"], "todos_artistas": ", ".join([a["name"] for a in track["artists"]]), "pais": pais, "posicion": posicion},
            "_posicion":        posicion,
            "_title_raw":       track["name"],
            "_artist_raw":      artista_principal,
        })
    print(f"✅ {len(tracks)} tracks obtenidos ({pais})")
    return tracks