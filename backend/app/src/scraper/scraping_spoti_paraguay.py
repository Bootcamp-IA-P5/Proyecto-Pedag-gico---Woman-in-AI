import time
from datetime import datetime
from app.src.config.spotify_config import obtener_token_spotify, PLAYLISTS
from app.src.scraper.spotify_scraper import obtener_tracks_playlist
from app.src.processor.upload_to_supabase import (
    guardar_ranking_raw,
    guardar_ranking_limpio,
    guardar_cancion,
    guardar_posicion_ranking,
)
from app.src.processor.normalizer import normalizar_track, reset_sesion

PAIS        = "PY"
PAIS_NOMBRE = "Paraguay"

def ejecutar_scraper_paraguay_top100():
    print(f"\n🇵🇾  Top 100 {PAIS_NOMBRE} — Spotify")
    print("=" * 50)

    # 🔹 Reset títulos de sesión para evitar duplicados
    reset_sesion()

    fecha_scraping = datetime.utcnow().isoformat()

    # 🔹 Paso 1 — Token de Spotify
    token = obtener_token_spotify()

    # 🔹 Paso 2 — Descargar las 100 canciones del Top 100 Paraguay
    tracks = obtener_tracks_playlist(token, PLAYLISTS[PAIS], PAIS)
    if not tracks:
        print(f"⚠️ No se encontraron tracks para {PAIS_NOMBRE}")
        return

    # 🔹 Paso 3 — Guardar ranking
    guardar_ranking_raw(PAIS, PLAYLISTS[PAIS], fecha_scraping, fuente="spotify")
    ranking_id = guardar_ranking_limpio(PAIS, fuente="spotify")

    # 🔹 Paso 4 — Guardar canciones normalizadas
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
            guardar_posicion_ranking(ranking_id, song_id, track["_posicion"])
        except Exception as e:
            print(f"❌ Error guardando track {track.get('title')}: {e}")
            ignoradas += 1
            continue

        nuevas     += es_nueva
        existentes += not es_nueva
        time.sleep(0.1)

    # 🔹 Resumen final
    print("\n" + "=" * 50)
    print(f"✅ {PAIS_NOMBRE} completado")
    print(f"   🆕 Canciones nuevas : {nuevas}")
    print(f"   ⏭️  Ya existían      : {existentes}")
    print(f"   ⚠️  Ignoradas       : {ignoradas}")
    print(f"   📊 ranking_id       : {ranking_id}")
    print("=" * 50)


if __name__ == "__main__":
    ejecutar_scraper_paraguay_top100()