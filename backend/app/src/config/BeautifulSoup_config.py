"""
Configuración y validación de BeautifulSoup. Todo lo del scraping arranca aquí.
"""

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# VARIABLES DE ENTORNO
# ──────────────────────────────────────────────

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
MUSICBRAINZ_EMAIL = os.getenv("MUSICBRAINZ_EMAIL")

# ──────────────────────────────────────────────
# HEADERS GLOBALES
# Simula un navegador real para evitar bloqueos.
# Importa desde aquí en cualquier módulo que necesite hacer requests.
# ──────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://www.letras.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# ──────────────────────────────────────────────
# URLS DE CHARTS
# Fuentes de descubrimiento de canciones en letras.com.
# ──────────────────────────────────────────────

CHART_URLS = {
    "espanol":   "https://www.letras.com/mais-acessadas/espanhol/",
    "general":   "https://www.letras.com/mais-acessadas/",
    "novedades": "https://www.letras.com/novidades/",
    "pop":       "https://www.letras.com/mais-acessadas/pop/",
    "reggaeton": "https://www.letras.com/mais-acessadas/reggaeton/",
    "rap":       "https://www.letras.com/mais-acessadas/rap/",
    "flamenco":  "https://www.letras.com/mais-acessadas/flamenco/",
}

# ──────────────────────────────────────────────
# SELECTORES CSS
# Selectores de BeautifulSoup para encontrar el contenedor de la letra.
# Están ordenados de más a menos específico.
# ──────────────────────────────────────────────

SELECTORES_LETRA = [
    {"tag": "div",  "attrs": {"class": "lyric__container"}},
    {"tag": "div",  "attrs": {"id": "js-lyric"}},
    {"tag": "article", "attrs": {}},
    {"tag": "div",  "attrs": {"class": "letra"}},
    {"tag": "pre",  "attrs": {}},
]

# ──────────────────────────────────────────────
# VALIDACIÓN DE SESIÓN
# ──────────────────────────────────────────────

def obtener_sesion() -> requests.Session:
    """
    Crea y valida una sesión HTTP con letras.com.
    Visita la home primero para recoger cookies y simular navegación real.
    Lanza EnvironmentError si no se puede conectar.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise EnvironmentError("❌ Faltan SUPABASE_URL o SUPABASE_KEY en .env")
    if not MUSICBRAINZ_EMAIL:
        raise EnvironmentError("❌ Falta MUSICBRAINZ_EMAIL en .env")

    session = requests.Session()
    respuesta = session.get("https://www.letras.com/", headers=HEADERS, timeout=10)

    if respuesta.status_code != 200:
        raise ConnectionError(f"❌ No se pudo conectar con letras.com (status {respuesta.status_code})")

    # Comprobamos que el HTML tiene estructura esperada
    soup = BeautifulSoup(respuesta.text, "html.parser")
    if not soup.find("body"):
        raise ValueError("❌ La respuesta de letras.com no parece HTML válido")

    print("✅ Sesión con letras.com iniciada correctamente")
    return session


if __name__ == "__main__":
    sesion = obtener_sesion()
    print("HEADERS activos:", list(HEADERS.keys()))
    print("Charts configurados:", list(CHART_URLS.keys()))
    print("Selectores configurados:", len(SELECTORES_LETRA))