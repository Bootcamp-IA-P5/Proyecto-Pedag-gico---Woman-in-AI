"""
Solo operaciones de escritura en Supabase. No sabe nada de Spotify.
Importa el cliente que ya tienes en config/supabase_client.py
"""
from datetime import date
from app.src.config.supabase_client import supabase   

def guardar_ranking_raw(pais: str, playlist_id: str, fecha_scraping: str) -> int:
    resultado = supabase.table("rankings_raw").insert({
        "source": "spotify", "country": pais, "scraping_date": fecha_scraping,
        "position": 1, "title_raw": f"Top 50 {pais}", "artist_raw": "Varios",
        "url_source": f"https://open.spotify.com/playlist/{playlist_id}",
        "extra_data": {"playlist_id": playlist_id},
    }).execute()
    print(f"💾 rankings_raw → id: {resultado.data[0]['id']}")
    return resultado.data[0]["id"]

def guardar_ranking_limpio(pais: str, fuente: str = "deezer") -> int:
    
    # Primero comprueba si ya existe un ranking de hoy para este país
    existente = supabase.table("rankings") \
        .select("id") \
        .eq("country", pais) \
        .eq("source", fuente) \
        .eq("ranking_date", date.today().isoformat()) \
        .execute()

    if existente.data:
        ranking_id = existente.data[0]["id"]
        print(f"⏭️  Ranking de hoy ya existe → id: {ranking_id}")
        return ranking_id

    # Si no existe, lo crea
    resultado = supabase.table("rankings").insert({
        "source":       fuente,
        "country":      pais,
        "ranking_date": date.today().isoformat(),
    }).execute()
    ranking_id = resultado.data[0]["id"]
    print(f"💾 rankings → id: {ranking_id}")
    return ranking_id

def guardar_cancion(track: dict) -> tuple[int, bool]:
    existente = supabase.table("songs").select("id").eq("title", track["title"]).execute()
    if existente.data:
        print(f"  ⏭️  Ya existe: {track['artist']} — {track['title']}")
        return existente.data[0]["id"], False
    resultado = supabase.table("songs").insert({k: v for k, v in track.items() if not k.startswith("_")}).execute()
    song_id = resultado.data[0]["id"]
    print(f"  ✅ Nueva: {track['artist']} — {track['title']} [{song_id}]")
    return song_id, True

def guardar_posicion_ranking(ranking_id: int, song_id: int, posicion: int):
    supabase.table("ranking_songs").upsert(
        {"ranking_id": ranking_id, "song_id": song_id, "position": posicion},
        on_conflict="ranking_id,song_id"
    ).execute()