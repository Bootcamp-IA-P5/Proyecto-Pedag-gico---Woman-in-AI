"""
Credenciales y configuración de YouTube Data API v3.

✅ Requiere YOUTUBE_API_KEY en el .env
   Obtén una clave en: https://console.developers.google.com/

Uso en otros archivos:
  from app.src.config.youtube_config import YOUTUBE_API_KEY, REGION_CODES, LIMITE_TRACKS
"""
import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

REGION_CODES = {
    "PE": "PE"
}

LIMITE_TRACKS = 50

YOUTUBE_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"