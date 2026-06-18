"""
backend/app/src/processor/enriquecer_generos_bd.py

Script Maestro para recorrer la Base de Datos y corregir/enriquecer
los géneros musicales usando nuestro Cerebro Global y los datos de Spotify.
"""

import time
import requests
from app.src.config.supabase_client import supabase
from app.src.config.spotify_config import obtener_token_spotify
from app.src.processor.normalizador_avanzado import normalizar_genero_global

LOTE_CANCIONES = 50


def buscar_generos_artista_spotify(nombre_artista: str, token: str) -> str:
    """Busca al artista en Spotify y devuelve sus géneros unidos por comas."""
    try:
        respuesta = requests.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": nombre_artista, "type": "artist", "limit": 1},
            timeout=5,
        )
        if respuesta.status_code == 200:
            datos = respuesta.json()
            artistas = datos.get("artists", {}).get("items", [])
            if artistas:
                generos = artistas[0].get("genres", [])
                return ", ".join(generos)
    except Exception as e:
        print(f"    ⚠️ Retry/Error Spotify con {nombre_artista}: {e}")

    return ""


def enriquecer_base_de_datos():
    print("🚀 Iniciando Misión de Enriquecimiento de Géneros en la BD...")

    # 1. Autenticar con Spotify
    print("🔑 Obteniendo token de Spotify...")
    token_spotify = obtener_token_spotify()
    if not token_spotify:
        print("❌ Error: No se pudo obtener el token de Spotify.")
        return

    # 2. Descargar canciones a revisar (Para no gastar API en balde, podemos filtrar)
    # Por ahora traemos todas las canciones ordenadas por ID o podemos elegir atacar a un género sobre-representado
    print("📥 Descargando catálogo de canciones desde Supabase...")
    respuesta = supabase.table("songs").select("id, title, artist, genre").execute()
    canciones = respuesta.data

    if not canciones:
        print("❌ No hay canciones en la base de datos.")
        return

    total = len(canciones)
    print(f"📊 {total} canciones encontradas en el catálogo.")

    # Caché en memoria para no buscar al mismo artista 100 veces en Spotify
    cache_artistas_spotify = {}

    exitos = 0
    actualizados = 0

    # 3. Procesar iterativamente
    for i, cancion in enumerate(canciones, start=1):
        c_id = cancion["id"]
        titulo = cancion["title"]
        artista = cancion["artist"]
        genero_antiguo = cancion["genre"]

        print(f"\n[{i}/{total}] Analizando: '{titulo}' — {artista}")
        print(f"  └─ Género Actual: {genero_antiguo}")

        # Opcion: si quisiéramos omitir los que ya están perfectos (Opcional, pero corramos todos si quieres perfección)

        # 3.1 Revisar Cache del Artista
        if artista not in cache_artistas_spotify:
            generos_sp = buscar_generos_artista_spotify(artista, token_spotify)
            cache_artistas_spotify[artista] = generos_sp
            # Pequeña pausa para respetar rate-limits de Spotify
            time.sleep(0.3)
        else:
            generos_sp = cache_artistas_spotify[artista]

        if generos_sp:
            print(f"  └─ Pistas Spotify: {generos_sp}")
        else:
            print("  └─ Pistas Spotify: (Sin datos oficiales)")

        # 3.2 Pasar por el Cerebro Global IA
        nuevo_genero = normalizar_genero_global(titulo, artista, generos_sp, genero_antiguo)
        print(f"  🧠 Cerebro Global dice -> {nuevo_genero}")

        # 3.3 Actualizar si es diferente o si es necesario
        # También actualizaremos si el antiguo decía 'reggaeton' (minúscula) y el nuevo 'Reggaeton' (mayúscula) para estandarizar
        if nuevo_genero and (nuevo_genero != genero_antiguo):
            supabase.table("songs").update({"genre": nuevo_genero}).eq(
                "id", c_id
            ).execute()
            print("  ✅ BD Actualizada!")
            actualizados += 1
        else:
            print("  ⏭️ Se mantiene igual.")

        exitos += 1

        # Ligera pausa para evitar saturar Groq (LLM)
        time.sleep(0.5)

    print("\n==================================")
    print("🎉 Misión Cumplida")
    print(f"Canciones analizadas: {total}")
    print(f"Registros corregidos en BD: {actualizados}")
    print("==================================")


if __name__ == "__main__":
    enriquecer_base_de_datos()
