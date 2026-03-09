from datetime import datetime

from app.src.scraper.youtube_scraper import obtener_tracks_region
from app.src.processor.normalizer import normalizar_track, reset_sesion

from app.src.processor.upload_to_supabase import (
    guardar_ranking_raw,
    guardar_ranking_limpio,
    guardar_cancion,
    guardar_posicion_ranking,
)

from app.src.processor.master_tables import guardar_cancion_maestra


def scraper_youtube_peru(pais="PE"):

    print("\n🚀 INICIANDO PIPELINE YOUTUBE\n")

    reset_sesion()

    # ─────────────
    # 1 obtener tracks
    # ─────────────
    tracks = obtener_tracks_region(pais)

    print(f"🎵 Tracks obtenidos: {len(tracks)}")

    if not tracks:
        print("❌ No hay tracks")
        return

    # ─────────────
    # 2 crear ranking
    # ─────────────
    ranking_id = guardar_ranking_limpio(pais, fuente="youtube")

    # ─────────────
    # 3 guardar ranking raw
    # ─────────────
    guardar_ranking_raw(
        pais=pais,
        playlist_id="youtube_trending",
        fecha_scraping=datetime.utcnow().isoformat(),
        fuente="youtube",
        title_raw="Top YouTube Peru",
        artist_raw="Varios",
    )

    total_insertadas = 0

    # ─────────────
    # 4 procesar canciones
    # ─────────────
    for track in tracks:

        track_normalizado = normalizar_track(track)

        if track_normalizado is None:
            continue

        posicion = track["_posicion"]

        # guardar canción
        song_id, es_nueva = guardar_cancion(track_normalizado)

        # guardar posición ranking
        guardar_posicion_ranking(
            ranking_id,
            song_id,
            posicion
        )

        # guardar en tabla maestra
        guardar_cancion_maestra(
            song_id=song_id,
            title=track_normalizado["title"],
            artist=track_normalizado["artist"],
            country=pais,
            position=posicion,
            streams=track_normalizado.get("streams"),
            year=track_normalizado.get("year"),
            genre=track_normalizado.get("genre"),
        )

        total_insertadas += 1

    print("\n✅ PIPELINE FINALIZADO")
    print(f"🎵 Canciones procesadas: {total_insertadas}")


if __name__ == "__main__":
    scraper_youtube_peru("PE")