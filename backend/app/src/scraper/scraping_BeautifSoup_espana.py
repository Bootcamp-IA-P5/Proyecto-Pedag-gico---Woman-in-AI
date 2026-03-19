"""
Scraper de letras de canciones con filtros estrictos:
- Solo letras en español

Dependencias:
    pip install requests beautifulsoup4 langdetect musicbrainzngs
"""

import re
import time


import musicbrainzngs
import requests
from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException
from supabase import create_client
from app.src.config.BeautifulSoup_config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    MUSICBRAINZ_EMAIL,
    obtener_sesion
)
from app.src.config.BeautifulSoup_config import HEADERS  # Evita error F401 de Ruff (importado pero no usado)


# Configuración de MusicBrainz (obligatorio identificarse)
musicbrainzngs.set_useragent("ScraperLetras", "1.0", str(MUSICBRAINZ_EMAIL or "bot@ejemplo.com"))

# ──────────────────────────────────────────────
# CONFIGURACIÓN SUPABASE
# ──────────────────────────────────────────────

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# ──────────────────────────────────────────────
# VALIDACIONES
# ──────────────────────────────────────────────

def obtener_anio_cancion(artist: str, title: str) -> int | None:
    """Consulta MusicBrainz para obtener el año de lanzamiento de la canción."""
    try:
        resultado = musicbrainzngs.search_recordings(
            recording=title,
            artist=artist,
            limit=5
        )
        recordings = resultado.get("recording-list", [])
        for rec in recordings:
            for release in rec.get("release-list", []):
                fecha = release.get("date", "")
                if fecha and len(fecha) >= 4:
                    anio = int(fecha[:4])
                    return anio
    except Exception as e:
        print(f"  ⚠️ Error consultando MusicBrainz: {e}")
    return None


def validar_anio(artist: str, title: str) -> tuple[bool, str]:
    """Informativo: siempre devuelve True, pero informa del año encontrado."""
    anio = obtener_anio_cancion(artist, title)
    if anio is None:
        return True, "❓ Año no encontrado en MusicBrainz."
    return True, f"📅 Año: {anio}"


def validar_idioma(texto: str, artist: str, title: str) -> tuple[bool, str]:
    """Devuelve (True, '') si la letra está en español, o (False, mensaje) si no."""
    try:
        # Usamos los primeros 500 caracteres para la detección (más rápido y suficiente)
        idioma = detect(texto[:500])
        if idioma != "es":
            return False, f"❌ La letra de '{title}' ({artist}) no está en español (detectado: '{idioma}')."
        return True, ""
    except LangDetectException:
        return False, f"❌ No se pudo detectar el idioma de '{title}'."


# ──────────────────────────────────────────────
# LIMPIEZA DE TEXTO
# ──────────────────────────────────────────────

def limpiar_para_url(texto: str) -> str:
    """Limpia el texto para que encaje en una URL de letras.com"""
    texto = texto.lower().strip()
    texto = re.sub(r'[áäâà]', 'a', texto)
    texto = re.sub(r'[éëêè]', 'e', texto)
    texto = re.sub(r'[íïîì]', 'i', texto)
    texto = re.sub(r'[óöôò]', 'o', texto)
    texto = re.sub(r'[úüûù]', 'u', texto)
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    return texto.replace(" ", "-")


def limpiar_letra(texto: str) -> str:
    """Elimina onomatopeyas y colapsa espacios del texto de la letra."""
    texto = re.sub(
        r'\b(eh|ah|oh|uh|mm+|hm+|na+|la+|ra+|ta+|pa+|ba+|ja+|ha+|ye+|wo+|ay+|ey+)\b',
        '',
        texto,
        flags=re.IGNORECASE
    )
    # Colapsar saltos y espacios múltiples en uno solo
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()


# ──────────────────────────────────────────────
# SCRAPING
# ──────────────────────────────────────────────

def scrape_lyrics(url: str, session=None) -> str | None:
    """Extrae la letra de una URL usando BeautifulSoup."""
    try:
        # Si no nos pasan sesión, creamos una rápida (menos eficiente)
        if session is None:
            session = requests.Session()
            session.headers.update(HEADERS)
        
        response = session.get(url, timeout=10)
        
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        container = (
            soup.find("div", class_="lyric-original") or
            soup.find("div", class_="lyric__container") or
            soup.find("div", id="js-lyric") or
            soup.find("div", class_="letra") or
            soup.find("div", class_="lyric") or
            soup.find("article") or
            soup.find("pre")
        )

        if container:
            for tag in container(["script", "style", "aside", "button", "a"]):
                tag.decompose()

            texto = container.get_text(separator="\n").strip()
            lineas = [linea.strip() for linea in texto.splitlines()]
            texto_limpio = "\n".join(linea for linea in lineas if linea)

            return texto_limpio if len(texto_limpio) > 50 else None

    except requests.exceptions.ConnectionError:
        print("  ⚠️ Sin conexión o web bloqueada")
    except Exception as e:
        print(f"  ⚠️ Error: {e}")
    return None


# ──────────────────────────────────────────────
# URL GENERATION
# ──────────────────────────────────────────────

def buscar_url_letra(artist: str, title: str) -> str | None:
    """Genera la URL candidata principal en letras.com para una canción."""
    artist_url = limpiar_para_url(artist)
    title_url = limpiar_para_url(title)
    return f"https://www.letras.com/{artist_url}/{title_url}/"


# ──────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ──────────────────────────────────────────────

def obtener_letra(artist: str, title: str) -> str:
    """
    Obtiene la letra de una canción aplicando los filtros obligatorios:
      1. Se identifica el año de la canción (informativo).
      2. La letra debe estar en español.

    Devuelve la letra limpia o un mensaje de error si no cumple las reglas.
    """

    # ── FILTRO 1: Año ──────────────────────────
    ok, error = validar_anio(artist, title)
    if not ok:
        return error

    # ── SCRAPING ───────────────────────────────
    artist_url = limpiar_para_url(artist)
    title_url = limpiar_para_url(title)

    urls = [
        f"https://www.letras.com/{artist_url}/{title_url}/",
        f"https://www.letras.com/{artist_url}/{title_url}-lyrics/",
        f"https://www.letras.com/{artist_url.replace('c-', '')}/{title_url}/",
    ]

    texto_crudo = None
    try:
        session = obtener_sesion()
        for url in urls:
            print(f"  🌐 Probando: {url}")
            texto_crudo = scrape_lyrics(url, session=session)
            if texto_crudo:
                break
            time.sleep(1.5)
    except Exception as e:
        print(f"  ⚠️ Error de sesión: {e}")

    if not texto_crudo:
        return f"❌ No se encontró la letra de '{title}' en ninguna URL."

    # ── FILTRO 2: Idioma ───────────────────────
    ok, error = validar_idioma(texto_crudo, artist, title)
    if not ok:
        return error

    # ── LIMPIEZA FINAL ─────────────────────────
    return limpiar_letra(texto_crudo)


# ──────────────────────────────────────────────
# EJECUCIÓN
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("Iniciando scraping automático de letras...")

    # 1. Traer canciones desde Supabase que no tengan letra
    respuesta = supabase.table("songs").select("id, artist, title").is_("lyrics", "null").execute()
    canciones_pendientes = respuesta.data

    if not canciones_pendientes:
        print("✅ No hay canciones pendientes por procesar.")
    else:
        print(f"🔄 Se encontraron {len(canciones_pendientes)} canciones sin letra. Comenzando scraping...\n")

        for c in canciones_pendientes:
            artista = c["artist"]
            titulo = c["title"]
            cancion_id = c["id"]
            
            print(f"🎵 Procesando: {artista} - {titulo}")
            resultado = obtener_letra(artista, titulo)
            
            if resultado.startswith("❌"):
                print(resultado)
                # Opcional: Marcar en base de datos que falló para no volver a intentarlo pronto
            else:
                # 2. Actualizar la base de datos con la nueva letra
                try:
                    supabase.table("songs").update({"lyrics": resultado}).eq("id", cancion_id).execute()
                    print("✅ LOGRADO y guardado en BD.")
                except Exception as e:
                    print(f"⚠️ Error al guardar en Supabase: {e}")
            
            print("-" * 50)
            
            # Pausa de seguridad para evitar bloqueos de la web o de la API
            time.sleep(2)
