"""
Pipeline completo:
  1. Lee canciones pendientes de Supabase (lyrics_status = 'pending')
  2. Busca y extrae la letra con Genius + BeautifulSoup
  3. Normaliza la letra con Groq LLM
  4. Actualiza la canción en Supabase
"""
import time
from app.src.config.supabase_client import supabase
from app.src.scraper.scraping_BeautifSoup_espana import obtener_letra
from app.src.processor.normalize_lyrics import normalizar_letra


def ejecutar_pipeline(pais: str = "ES", limite: int = 50):
    """
    Ejecuta el pipeline de scraping + normalización para canciones pendientes.

    Args:
        pais: código del país a procesar (por defecto "ES" para España)
        limite: número máximo de canciones a procesar por ejecución
    """
    print(f"🚀 Iniciando pipeline de letras para {pais}...")
    print("=" * 60)

    # 1. Obtener canciones pendientes de Supabase
    res = supabase.table("lyrics") \
        .select("id, artist, title") \
        .eq("lyrics_status", "pending") \
        .limit(limite) \
        .execute()

    canciones = res.data

    if not canciones:
        print("✅ No hay canciones pendientes. Todo al día!")
        return

    total = len(canciones)
    exitos = 0
    errores = 0

    print(f"📋 {total} canciones pendientes encontradas\n")

    for i, cancion in enumerate(canciones, start=1):
        song_id = cancion["id"]
        artist = cancion["artist"]
        title = cancion["title"]

        print(f"\n[{i}/{total}] {artist} — {title}")
        print("-" * 40)

        # 2. Scraping de la letra
        lyrics_raw = obtener_letra(artist, title)

        if not lyrics_raw:
            # Marcar como error para no reintentar indefinidamente
            supabase.table("lyrics").update({
                "lyrics_status": "not_found"
            }).eq("id", song_id).execute()
            errores += 1
            print("  📝 Marcada como 'not_found'")
            continue

        # 3. Normalizar con Groq
        print("  🤖 Normalizando con Groq...")
        lyrics_clean = normalizar_letra(lyrics_raw)

        if not lyrics_clean:
            # Si Groq falla, guardar la versión cruda igualmente
            supabase.table("lyrics").update({
                "lyrics": lyrics_raw,
                "lyrics_status": "raw"
            }).eq("id", song_id).execute()
            print("  ⚠️ Groq falló — guardada versión cruda")
            exitos += 1
            continue

        # 4. Guardar en Supabase
        supabase.table("lyrics").update({
            "lyrics": lyrics_clean,
            "lyrics_status": "done"
        }).eq("id", song_id).execute()
        exitos += 1
        print("  ✅ Letra normalizada y guardada")

        # Pausa breve para no saturar las APIs
        time.sleep(2)

    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL PIPELINE")
    print("   Total procesadas: {total}")
    print("   ✅ Éxitos: {exitos}")
    print("   ❌ No encontradas: {errores}")
    print("=" * 60)


if __name__ == "__main__":
    ejecutar_pipeline()
