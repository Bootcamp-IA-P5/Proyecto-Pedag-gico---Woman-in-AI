import requests
import isodate

from app.src.config.youtube_config import (
    YOUTUBE_API_KEY,
    LIMITE_TRACKS,
    YOUTUBE_ENDPOINT
)


def convertir_duracion(duration_iso):

    try:
        return int(isodate.parse_duration(duration_iso).total_seconds())
    except(TypeError, ValueError, Exception): 
        return None
       


def separar_artista_titulo(titulo):

    if "-" in titulo:
        partes = titulo.split("-", 1)
        artista = partes[0].strip()
        titulo = partes[1].strip()
    else:
        artista = "desconocido"

    return artista, titulo


def obtener_tracks_region(region_code: str):

    params = {
        "part": "snippet,statistics,contentDetails",
        "chart": "mostPopular",
        "videoCategoryId": "10",
        "regionCode": region_code,
        "maxResults": LIMITE_TRACKS,
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(YOUTUBE_ENDPOINT, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    tracks = []

    for posicion, item in enumerate(data.get("items", []), start=1):

        snippet = item["snippet"]
        stats = item["statistics"]

        titulo_raw = snippet["title"]

        artista, titulo = separar_artista_titulo(titulo_raw)

        duracion = convertir_duracion(item["contentDetails"]["duration"])

        video_id = item["id"]

        tracks.append({

            "ranking_position": posicion,

            "title": titulo,
            "artist": artista,

            "streams": int(stats.get("viewCount", 0)),

            "genre": None,
            "lyrics": None,
            "album": None,
            "year": None,

            "duration_seg": duracion,

            "language_variant": None,

            "source": "youtube",

            "url_source": f"https://youtube.com/watch?v={video_id}",

            "lyrics_status": "pending",

            "extra_data": {
                "youtube_video_id": video_id,
                "youtube_channel": snippet["channelTitle"],
                "like_count": stats.get("likeCount"),
                "comment_count": stats.get("commentCount"),
                "thumbnail": snippet["thumbnails"]["high"]["url"],
                "pais": region_code,
                "posicion": posicion
            },

            "_posicion": posicion,
            "_title_raw": titulo_raw,
            "_artist_raw": artista

        })

    print(f"✅ {len(tracks)} tracks YouTube ({region_code})")

    return tracks