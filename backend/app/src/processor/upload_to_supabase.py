
from datetime import date, datetime
from app.src.config.supabase_client import supabase


# ─── Guardar ranking raw ──────────────────────────────────────────────
def guardar_ranking_raw(
    pais: str,
    playlist_id: str,
    fecha_scraping: str,
    fuente: str = "spotify",
    url_source: str | None = None,
    title_raw: str | None = None,
    artist_raw: str = "Varios",
    extra_data: dict | None = None,
) -> int:
    if url_source is None:
        if fuente == "spotify":
            url_source = f"https://open.spotify.com/playlist/{playlist_id}"
        elif fuente == "deezer":
            url_source = f"https://www.deezer.com/playlist/{playlist_id}"
        else:
            url_source = str(playlist_id)

    if title_raw is None:
        title_raw = f"Top {pais}" if fuente != "spotify" else f"Top 50 {pais}"

    if extra_data is None:
        extra_data = {"playlist_id": playlist_id}

    try:
        resultado = supabase.table("rankings_raw").insert({
            "source":        fuente,
            "country":       pais,
            "scraping_date": fecha_scraping,
            "position":      1,
            "title_raw":     title_raw,
            "artist_raw":    artist_raw,
            "url_source":    url_source,
            "extra_data":    extra_data,
        }).execute()
        print(f"💾 rankings_raw → id: {resultado.data[0]['id']}")
        return resultado.data[0]["id"]
    except Exception as e:
        print(f"❌ Error guardando ranking_raw: {e}")
        raise


# ─── Guardar ranking limpio ───────────────────────────────────────────
def guardar_ranking_limpio(pais: str, fuente: str = "deezer") -> int:
    try:
        existente = supabase.table("rankings") \
            .select("id") \
            .eq("country", pais) \
            .eq("source", fuente) \
            .eq("ranking_date", date.today().isoformat()) \
            .execute()

        if existente.data:
            ranking_id = existente.data[0]["id"]
            print(f"⏭️ Ranking de hoy ya existe → id: {ranking_id}")
            return ranking_id

        resultado = supabase.table("rankings").insert({
            "source":       fuente,
            "country":      pais,
            "ranking_date": date.today().isoformat(),
        }).execute()
        ranking_id = resultado.data[0]["id"]
        print(f"💾 rankings → id: {ranking_id}")
        return ranking_id

    except Exception as e:
        print(f"❌ Error guardando ranking limpio: {e}")
        raise


# ─── Guardar canción ─────────────────────────────────────────────────
def guardar_cancion(track: dict) -> tuple[int, bool]:
    """
    Detecta duplicados por title + artist (normalizados) y actualiza o inserta.
    Devuelve (song_id, es_nueva: bool)
    """
    try:
        existente = supabase.table("songs") \
            .select("id") \
            .ilike("title", track["title"]) \
            .limit(1) \
            .execute()

        if existente.data:
            song_id = existente.data[0]["id"]
            supabase.table("songs").update({
                "title":            track.get("title"),
                "artist":           track.get("artist"),
                "album":            track.get("album"),
                "genre":            track.get("genre"),
                "language_variant": track.get("language_variant"),
                "extra_data":       track.get("extra_data"),
            }).eq("id", song_id).execute()
            print(f"🔄 Actualizado: {track['artist']} — {track['title']}")
            return song_id, False

        campos = {k: v for k, v in track.items() if not k.startswith("_")}
        resultado = supabase.table("songs").insert(campos).execute()
        song_id = resultado.data[0]["id"]
        print(f"✅ Nueva: {track['artist']} — {track['title']} [{song_id}]")
        return song_id, True

    except Exception as e:
        print(f"❌ Error guardando canción {track.get('title')}: {e}")
        raise


# ─── Guardar posición en ranking ──────────────────────────────────────
def guardar_posicion_ranking(ranking_id: int, song_id: int, posicion: int):
    try:
        supabase.table("ranking_songs").upsert(
            {"ranking_id": ranking_id, "song_id": song_id, "position": posicion},
            on_conflict="ranking_id,song_id"
        ).execute()
    except Exception as e:
        print(f"⚠️ Error insertando en ranking_songs: ranking_id={ranking_id}, song_id={song_id}: {e}")


# ─── Funciones para letras ────────────────────────────────────────────
def obtener_canciones_pendientes(limite: int = 50) -> list[dict]:
    resultado = supabase.table("songs") \
        .select("id, title, artist") \
        .eq("lyrics_status", "pending") \
        .limit(limite) \
        .execute()
    print(f"📋 {len(resultado.data)} canciones pendientes de letra")
    return resultado.data


def letra_ya_existe(song_id: int) -> bool:
    resultado = supabase.table("lyrics") \
        .select("id") \
        .eq("song_id", song_id) \
        .execute()
    return len(resultado.data) > 0


def guardar_letra_raw(song_id: int, letra: dict) -> int:
    resultado = supabase.table("lyrics_raw").insert({
        "song_id":           song_id,
        "lyrics_text":       letra["lyrics_text"],
        "language_detected": letra["language_detected"],
        "source":            letra["source"],
        "url_source":        letra["url_source"],
        "scraping_date":     datetime.utcnow().isoformat(),
        "extra_data":        letra.get("extra_data", {}),
    }).execute()
    return resultado.data[0]["id"]


def guardar_letra(song_id: int, letra: dict) -> int:
    resultado = supabase.table("lyrics").insert({
        "song_id":           song_id,
        "lyrics_text":       letra["lyrics_text"],
        "lyrics_hash":       letra["lyrics_hash"],
        "word_count":        letra["word_count"],
        "verse_count":       letra["verse_count"],
        "language_detected": letra["language_detected"],
        "source":            letra["source"],
    }).execute()
    return resultado.data[0]["id"]


def marcar_completado(song_id: int):
    supabase.table("songs").update({"lyrics_status": "completed"}).eq("id", song_id).execute()


def marcar_error(song_id: int, motivo: str):
    try:
        resultado = supabase.table("songs").select("extra_data").eq("id", song_id).execute()
        extra = resultado.data[0].get("extra_data", {}) if resultado.data else {}
        extra["error_letra"] = motivo
        supabase.table("songs").update({
            "lyrics_status": "error",
            "extra_data": extra
        }).eq("id", song_id).execute()
    except Exception as e:
        print(f"⚠️ Error marcando error para song_id={song_id}: {e}")


def guardar_letra_completa(song_id: int, letra: dict) -> int:
    """
    Guarda raw + limpio + marca completado y avisa a top_songs.
    Devuelve lyrics_id
    """
    from app.src.processor.master_tables import marcar_lyrics_en_top

    guardar_letra_raw(song_id, letra)
    lyrics_id = guardar_letra(song_id, letra)
    marcar_completado(song_id)
    marcar_lyrics_en_top(song_id, lyrics_id)
    return lyrics_id