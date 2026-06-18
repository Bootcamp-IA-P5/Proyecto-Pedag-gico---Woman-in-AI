"""
backend/app/src/scraper/buscador_letras_dual.py

Motor de búsqueda de letras con doble redundancia.
Intenta primero con LRCLIB (API abierta y ultrarrápida sin límite estricto).
Si falla, hace "fallback" al scraper de Genius creado por el equipo.
"""

import requests
from app.src.scraper.scraping_BeautifSoup_espana import (
    obtener_letra as obtener_letra_genius,
)


def buscar_letra_lrclib(titulo: str, artista: str) -> str | None:
    """Busca letras en la API abierta de LRCLIB."""
    try:
        url = "https://lrclib.net/api/search"
        params = {"track_name": titulo, "artist_name": artista}
        respuesta = requests.get(url, params=params, timeout=10)

        if respuesta.status_code == 200:
            datos = respuesta.json()
            if isinstance(datos, list) and len(datos) > 0:
                # Buscamos el primer resultado que tenga la letra plana (plainLyrics)
                for pista in datos:
                    letra = pista.get("plainLyrics")
                    if letra and letra.strip():
                        return letra.strip()
    except Exception as e:
        print(f"    ⚠️ Error de conexión con LRCLIB: {e}")

    return None


def buscar_letra_global(titulo: str, artista: str) -> tuple[str | None, str]:
    """
    Función maestra para obtener una letra.
    Retorna una tupla: (letra, 'fuente_exitosa')
    para saber quién nos salvó la vida (LRCLIB o Genius).
    """
    # 1. Primer intento: LRCLIB (Rápido y limpio)
    letra_lrclib = buscar_letra_lrclib(titulo, artista)
    if letra_lrclib:
        return letra_lrclib, "LRCLIB"

    # 2. Segundo intento (Fallback): Genius (El gigante)
    print(f"    🔄 LRCLIB no la tiene. Haciendo fallback a Genius para '{titulo}'...")
    try:
        letra_genius = obtener_letra_genius(artista, titulo)
        if letra_genius:
            return letra_genius, "Genius"
    except Exception as e:
        print(f"    ⚠️ Oh no, el scraper de Genius también falló: {e}")

    # Si todo falla
    return None, "Not Found"


# Bloque de prueba local
if __name__ == "__main__":
    print("🎤 Probando Buscador Dual de Letras...\n")

    # Canción famosa global (Debería salir rapidísimo por LRCLIB)
    titulo1, art1 = "La Bachata", "Manuel Turizo"
    letra1, fuente1 = buscar_letra_global(titulo1, art1)

    if letra1:
        print(f"✅ [{fuente1}] Encontrada: {titulo1} - {art1}")
        print(f"   Muestra: {letra1[:60]}...\n")

    # Canción posible nicho o que probaremos forzando Genius
    titulo2, art2 = "La Rompe Corazones", "Daddy Yankee"
    letra2, fuente2 = buscar_letra_global(titulo2, art2)

    if letra2:
        print(f"✅ [{fuente2}] Encontrada: {titulo2} - {art2}")
        print(f"   Muestra: {letra2[:60]}...")
