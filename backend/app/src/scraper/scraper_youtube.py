from datetime import date

from app.src.scraper.youtube_scraper import obtener_tracks_region
from app.src.config.youtube_config import REGION_CODES

from app.src.processor.normalizer import normalizar_track
from app.src.processor.upload_to_supabase import (
    guardar_cancion,
    guardar_posicion_ranking,
    guardar_ranking_limpio
)

from app.src.processor.master_tables import guardar_cancion_maestra


def ejecutar_scraper_youtube():

    for pais, region_code in REGION_CODES.items():

        print(f"\n🎵 Scraping YouTube {pais}")

        ranking_id = guardar_ranking_limpio(pais, "youtube")

        tracks = obtener_tracks_region(region_code)

        for track in tracks:

            track_normalizado = normalizar_track(track)

            if not track_normalizado:
                continue

            song_id, nueva = guardar_cancion(track_normalizado)

            guardar_posicion_ranking(
                ranking_id,
                song_id,
                track["ranking_position"]
            )

            guardar_cancion_maestra(
                song_id,
                track_normalizado["title"],
                track_normalizado["artist"],
                country=pais,
                position=track["ranking_position"],
                streams=track_normalizado["streams"],
                year=track_normalizado["year"],
                genre=track_normalizado["genre"],
            )

        print("✅ Ranking completado")