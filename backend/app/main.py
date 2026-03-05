from fastapi import FastAPI
from app.src.processor.upload_to_supabase import (
    guardar_ranking_raw,
    guardar_ranking_limpio,
    guardar_cancion,
    guardar_posicion_ranking,
)
from app.src.processor.master_tables import guardar_cancion_maestra

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Bienvenido al agente de scraping de canciones"}


def procesar_track(track: dict, country: str):
    """
    Flujo completo para un track:
    1. Guarda en songs
    2. Guarda en top_songs
    """
    # PASO 1: guardar en songs
    song_id, es_nueva = guardar_cancion(track)

    # PASO 2: guardar en top_songs
    guardar_cancion_maestra(
        song_id=song_id,
        title=track["title"],
        artist=track["artist"],
        country=country,
        position=track.get("ranking_position"),
        streams=track.get("streams"),
        year=track.get("year"),
        genre=track.get("genre"),
    )
EOF