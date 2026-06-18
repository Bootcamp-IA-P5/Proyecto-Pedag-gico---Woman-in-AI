"""
backend/app/src/processor/enriquecer_letras_bd.py

Script Maestro paralelo para rellenar las Letras (Lyrics) de las canciones
en la Base de Datos. Utiliza el buscador dual (LRCLIB + Genius) y
limpia el texto con el normalizador del equipo.
"""

import time
from app.src.config.supabase_client import supabase
from app.src.scraper.buscador_letras_dual import buscar_letra_global
from app.src.processor.normalize_lyrics import normalizar_letra


def enriquecer_letras_base_de_datos():
    print("🚀 Iniciando Misión de Enriquecimiento de Letras en la BD...")

    # Descargamos solo las canciones que NO tienen letra (ahorramos tiempo)
    print("📥 Descargando catálogo de canciones sin letra...")
    # Buscamos donde 'lyrics' sea estrictamente null
    respuesta = (
        supabase.table("songs")
        .select("id, title, artist")
        .is_("lyrics", "null")
        .execute()
    )
    canciones_sin_letra = respuesta.data

    if not canciones_sin_letra:
        print("✅ ¡Increíble! Todas las canciones ya tienen letras asignadas.")
        return

    total = len(canciones_sin_letra)
    print(f"📊 {total} canciones necesitan letras.\n")

    exitos = 0
    errores = 0

    for i, cancion in enumerate(canciones_sin_letra, start=1):
        c_id = cancion["id"]
        titulo = cancion["title"]
        artista = cancion["artist"]

        print(f"[{i}/{total}] Buscando: '{titulo}' — {artista}")

        # 1. Buscar Letra Cruda (Buscador Dual)
        letra_raw, fuente = buscar_letra_global(titulo, artista)

        if not letra_raw:
            print("  ❌ No encontrada en ninguna base de datos.")
            # Marcamos como no encontrada para saber que ya la intentamos buscar
            supabase.table("songs").update({"lyrics_status": "not_found"}).eq(
                "id", c_id
            ).execute()
            errores += 1
            time.sleep(1)  # Pausita corta
            continue

        print(f"  ✅ Letra encontrada en {fuente}!")

        # 2. Normalizar Letra (Usando el script puro de Regex)
        print("  🤖 Limpiando y normalizando con Regex...")
        letra_limpia = normalizar_letra(letra_raw)

        # 3. Guardar en Base de Datos
        if letra_limpia:
            supabase.table("songs").update(
                {"lyrics": letra_limpia, "lyrics_status": "completed"}
            ).eq("id", c_id).execute()
            print("  💾 Guardada (Limpia) en Supabase.")
        else:
            # Si el modelo falla, guardamos la versión cruda al menos
            supabase.table("songs").update(
                {"lyrics": letra_raw, "lyrics_status": "raw"}
            ).eq("id", c_id).execute()
            print("  ⚠️ Guardada (Cruda) en Supabase por fallo del LLM.")

        exitos += 1

        # Pausa para no sobrecargar el límite de peticiones (Rate Limit de LLM y APIs)
        time.sleep(1.5)

    print("\n==================================")
    print("🎉 Misión Letras Cumplida")
    print(f"Rescatadas y Normalizadas: {exitos}")
    print(f"Letras Inexistentes en internet: {errores}")
    print("==================================")


if __name__ == "__main__":
    enriquecer_letras_base_de_datos()
