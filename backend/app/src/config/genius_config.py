"""
backend/app/src/config/genius_config.py
Credenciales y cliente de Genius. Todo lo de letras arranca aquí.
"""
import os
import lyricsgenius
from dotenv import load_dotenv

load_dotenv()

GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")

def obtener_cliente_genius() -> lyricsgenius.Genius:
    if not GENIUS_ACCESS_TOKEN:
        raise EnvironmentError("❌ Falta GENIUS_ACCESS_TOKEN en .env")
    return lyricsgenius.Genius(
        GENIUS_ACCESS_TOKEN,
        verbose=False,
        remove_section_headers=True,
        skip_non_songs=True,
        excluded_terms=["(Remix)", "(Live)"],
    )