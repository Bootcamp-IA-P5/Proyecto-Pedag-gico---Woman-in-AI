"""
master_tables.py
Gestiona la tabla maestra top_songs.
Ubicacion: backend/app/src/processor/master_tables.py
"""
from app.src.config.supabase_client import supabase


def guardar_cancion_maestra(
    song_id: int,
    title: str,
    artist: str,
    country: str | None = None,
    position: int | None = None,
    streams: int | None = None,
    year: int | None = None,
    genre: str | None = None,
) -> int:
    # Busca por title Y por song_id para evitar duplicados
    # Busca primero por song_id
    existente = supabase.table("top_songs") \
        .select("id, times_in_ranking, best_position, streams_max") \
        .eq("song_id", song_id) \
        .execute()

    # Si no encuentra por song_id busca por title
    if not existente.data:
        existente = supabase.table("top_songs") \
            .select("id, times_in_ranking, best_position, streams_max") \
            .eq("title", title) \
            .execute()

    if existente.data:
        fila   = existente.data[0]
        top_id = fila["id"]

        best = fila["best_position"]
        if position is not None and (best is None or position < best):
            best = position

        streams_max = fila["streams_max"]
        if streams is not None and (streams_max is None or streams > streams_max):
            streams_max = streams

        supabase.table("top_songs").update({
            "song_id":          song_id,
            "times_in_ranking": fila["times_in_ranking"] + 1,
            "best_position":    best,
            "streams_max":      streams_max,
            "genre":            genre,
            "updated_at":       "now()",
        }).eq("id", top_id).execute()

        print(f"  🔄 top_songs actualizado: {title} [{top_id}]")
        return top_id

    resultado = supabase.table("top_songs").insert({
        "song_id":       song_id,
        "title":         title,
        "artist":        artist,
        "country":       country,
        "best_position": position,
        "streams_max":   streams,
        "year":          year,
        "genre":         genre,
        "has_lyrics":    False,
    }).execute()

    top_id = resultado.data[0]["id"]
    print(f"  ✅ top_songs nueva: {title} [{top_id}]")
    return top_id

def marcar_lyrics_en_top(song_id: int, lyrics_id: int):
    supabase.table("top_songs") \
        .update({
            "has_lyrics": True,
            "lyrics_id":  lyrics_id,
        }) \
        .eq("song_id", song_id) \
        .execute()
    print(f"  🎵 top_songs → has_lyrics=True para song_id [{song_id}]")