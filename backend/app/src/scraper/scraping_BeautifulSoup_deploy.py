"""
Este es el fichero que EJECUTAS para obtener las letras desde letras.com.
Procesa canciones descubiertas desde los charts.

Cómo ejecutarlo:
  python scraping_BeautifulSoup_deploy.py

Qué hace paso a paso:
  1. Inicia sesión HTTP con letras.com                 (BeautifulSoup_config.py)
  2. Extrae candidatas de los charts de letras.com     (scraper_letras.py)
  3. Valida el año de cada canción via MusicBrainz     (scraper_letras.py)
  4. Scraping de la letra desde letras.com             (scraper_letras.py)
  5. Valida que la letra esté en español               (scraper_letras.py)
  6. Limpia la letra (sin espacios, sin onomatopeyas)  (scraper_letras.py)
  7. Guarda en Supabase (artista, titulo, letra, anio, idioma)
"""

import time
import os
import sys


# Añadir la raíz 'Vertice/backend' al path de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import musicbrainzngs
from supabase import create_client

from app.src.config.BeautifulSoup_config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    MUSICBRAINZ_EMAIL,
    CHART_URLS,
    HEADERS,
    obtener_sesion,
)
from app.src.scraper.scraper_letras import (
    obtener_canciones_del_chart,
    obtener_canciones_del_artista,
    validar_anio,
    scrape_lyrics,
    validar_idioma,
    limpiar_letra,
    limpiar_para_url,
    ya_existe,
    guardar_cancion,
    ARTISTAS_EXTRA,
)

# ─── Configuración ─────────────────────────────────────────────────────────────

OBJETIVO              = 600    # letras válidas a recopilar
BATCH_SIZE            = 50     # canciones procesadas por bloque antes de loguear progreso
PAUSA_ENTRE_CANCIONES = 1.5    # segundos — evita bloqueos de letras.com
PAUSA_ENTRE_CHARTS    = 1.0    # segundos — entre peticiones a charts

musicbrainzngs.set_useragent("ScraperLetras", "1.0", MUSICBRAINZ_EMAIL)


# ─── Pipeline ──────────────────────────────────────────────────────────────────

def ejecutar_scraper_letras():

    print("\n🎵 Scraper de letras — letras.com → Supabase")
    print("=" * 50)
    print(f"   🎯 Objetivo      : {OBJETIVO} letras")
    print(f"   🌐 Charts fuente : {len(CHART_URLS)}")
    print("=" * 50)

    # Paso 1 — Iniciar sesión HTTP
    try:
        session  = obtener_sesion()
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except (EnvironmentError, ConnectionError) as e:
        print(f"\n{e}")
        print("   Comprueba tu .env y la conexión a internet.")
        return

    recopiladas = 0
    descartadas = 0
    duplicadas  = 0
    candidatas  = []
    vistas      = set()
    artistas_extra = list(ARTISTAS_EXTRA)  # copia para no mutar el original

    # Paso 2 — Extraer candidatas de todos los charts
    print("\n📋 Extrayendo canciones de los charts...")
    for nombre, url in CHART_URLS.items():
        nuevas = obtener_canciones_del_chart(url, session)
        for c in nuevas:
            if c["url"] not in vistas:
                vistas.add(c["url"])
                candidatas.append(c)
        print(f"   ✔ {nombre:<12} → {len(nuevas):>3} canciones")
        time.sleep(PAUSA_ENTRE_CHARTS)

    print(f"\n📦 Candidatas iniciales: {len(candidatas)}")
    print("─" * 50)

    # Paso 3-7 — Procesar candidatas
    i = 0
    while recopiladas < OBJETIVO:

        # Sin más candidatas → ampliar con artistas extra
        if i >= len(candidatas):
            if not artistas_extra:
                print("\n⚠️  Sin más candidatas disponibles. Terminando.")
                break
            slug   = artistas_extra.pop(0)
            nuevas = obtener_canciones_del_artista(slug, session)
            print(f"\n🔄 Ampliando con '{slug}' → {len(nuevas)} canciones nuevas")
            for nueva in nuevas:
                if nueva["url"] not in vistas:
                    vistas.add(nueva["url"])
                    candidatas.append(nueva)
            time.sleep(PAUSA_ENTRE_CHARTS)
            continue

        c       = candidatas[i]
        i      += 1
        artista = c["artista"]
        titulo  = c["titulo"]
        url     = c["url"]

        print(f"\n🎵 [{recopiladas}/{OBJETIVO}] {artista} — {titulo}")

        # Evitar duplicados en Supabase
        if ya_existe(supabase, artista, titulo):
            print("   ⏭️  Ya existe en Supabase, saltando")
            duplicadas += 1
            continue

        # Paso 3 — Validar año via MusicBrainz
        valido_anio, anio = validar_anio(artista, titulo)
        if not valido_anio:
            motivo = "no encontrado en MusicBrainz" if anio == 0 else f"año {anio} fuera de rango"
            print(f"   ❌ Año inválido — {motivo}")
            descartadas += 1
            time.sleep(0.5)
            continue

        # Paso 4 — Scraping de la letra
        texto_crudo = scrape_lyrics(url, session)
        if not texto_crudo:
            url_alt     = f"https://www.letras.com/{limpiar_para_url(artista)}/{limpiar_para_url(titulo)}/"
            texto_crudo = scrape_lyrics(url_alt, session)

        if not texto_crudo:
            print("   ❌ Letra no encontrada en ninguna URL")
            descartadas += 1
            time.sleep(1)
            continue

        # Paso 5 — Validar idioma
        valido_idioma, idioma = validar_idioma(texto_crudo)
        if not valido_idioma:
            print(f"   ❌ Idioma no español (detectado: '{idioma}')")
            descartadas += 1
            time.sleep(0.5)
            continue

        # Paso 6 — Limpiar letra
        letra_limpia = limpiar_letra(texto_crudo)

        # Paso 7 — Guardar en Supabase
        try:
            guardar_cancion(supabase, artista, titulo, letra_limpia, anio, idioma)
            recopiladas += 1
            print(f"   ✅ Guardada ({recopiladas}/{OBJETIVO}) — año {anio} | idioma: {idioma}")
        except Exception as e:
            print(f"   ❌ Error al guardar en Supabase: {e}")
            descartadas += 1

        # Log de progreso cada BATCH_SIZE canciones
        if recopiladas > 0 and recopiladas % BATCH_SIZE == 0:
            print(f"\n{'─'*50}")
            print(f"   📊 Progreso: {recopiladas}/{OBJETIVO} letras guardadas")
            print(f"   ❌ Descartadas hasta ahora: {descartadas}")
            print(f"{'─'*50}\n")

        time.sleep(PAUSA_ENTRE_CANCIONES)

    # ─── Resumen final ─────────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("✅ Scraper completado")
    print(f"   ✔ Guardadas    : {recopiladas}")
    print(f"   ✖ Descartadas  : {descartadas}")
    print(f"   ⏭  Duplicadas   : {duplicadas}")
    print(f"   📊 Procesadas   : {recopiladas + descartadas + duplicadas}")
    if recopiladas < OBJETIVO:
        print(f"   ⚠️  Objetivo no alcanzado — faltan {OBJETIVO - recopiladas} letras")
        print("      Añade más artistas a ARTISTAS_EXTRA en scraper_letras.py")
    print("=" * 50)


if __name__ == "__main__":
    ejecutar_scraper_letras()