import time
from datetime import datetime
from app.src.config.deezer_config import PLAYLISTS_DEEZER
from app.src.scraper.deezer_scraper import obtener_tracks_playlist
from app.src.processor.upload_to_supabase import (
    guardar_ranking_raw,
    guardar_ranking_limpio,
    guardar_cancion,
    guardar_posicion_ranking,
)
from app.src.processor.master_tables import guardar_cancion_maestra
from app.src.processor.normalizer import normalizar_track, reset_sesion

PAIS = "PY"
PAIS_NOMBRE = "Paraguay"

def ejecutar_scraper_deezer_paraguay():
    reset_sesion()
    print(f"\n🇵🇾 Top 100 {PAIS_NOMBRE} — Deezer")
    print("="*45)
    fecha_scraping = datetime.utcnow().isoformat()

    # Paso 1: Descargar tracks
    tracks = obtener_tracks_playlist(PLAYLISTS_DEEZER[PAIS], PAIS)

    # Paso 2: Guardar ranking
    try:
        guardar_ranking_raw(PAIS, str(PLAYLISTS_DEEZER[PAIS]), fecha_scraping, fuente="deezer", url_source=str(PLAYLISTS_DEEZER[PAIS]))
        ranking_id = guardar_ranking_limpio(PAIS, fuente="deezer")
    except Exception as e:
        print(f"❌ Error guardando ranking: {e}")
        return

    # Paso 3: Guardar canciones
    nuevas = existentes = ignoradas = 0
    for track in tracks:
        track = normalizar_track(track)
        if track is None:
            ignoradas += 1
            continue

        if "_posicion" not in track or track["_posicion"] is None:
            print(f"⚠️ Track sin posicion: {track.get('title')}")
            ignoradas += 1
            continue

        try:
            song_id, es_nueva = guardar_cancion(track)
        except Exception as e:
            print(f"❌ Error guardando track {track.get('title')}: {e}")
            ignoradas += 1
            continue

        try:
            guardar_posicion_ranking(ranking_id, song_id, track["_posicion"])
        except Exception as e:
            print(f"⚠️ Error guardando ranking {track.get('title')}: {e}")
            ignoradas += 1
            continue

        try:
            guardar_cancion_maestra(
                song_id=song_id,
                title=track["title"],
                artist=track["artist"],
                country=PAIS,
                position=track.get("ranking_position"),
                streams=track.get("streams"),
                year=track.get("year"),
                genre=track.get("genre"),
            )
        except Exception as e:
            print(f"⚠️ Error guardando canción maestra {track.get('title')}: {e}")
            ignoradas += 1
            continue

        nuevas += es_nueva
        existentes += not es_nueva
        time.sleep(0.1)

    print("\n" + "="*45)
    print(f"✅ {PAIS_NOMBRE} completado")
    print(f"   🆕 Canciones nuevas : {nuevas}")
    print(f"   ⏭️ Ya existían      : {existentes}")
    print(f"   ⚠️ Ignoradas       : {ignoradas}")
    print(f"   📊 ranking_id       : {ranking_id}")
    print("   ⏳ Siguiente        : lyrics_scraper.py")
    print("="*45)

if __name__ == "__main__":
    ejecutar_scraper_deezer_paraguay()