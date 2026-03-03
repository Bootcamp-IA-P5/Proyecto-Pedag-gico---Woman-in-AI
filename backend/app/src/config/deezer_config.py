"""

✅ Deezer NO necesita API key — es pública y gratuita.
   No hay nada que añadir al .env para Deezer.

Uso en otros archivos:
  from app.src.config.deezer_config import CHARTS_DEEZER, LIMITE_TRACKS
"""

# Charts Top por país
# URL base: https://api.deezer.com/chart/{id}/tracks
#
# Cómo encontrar el ID de un país nuevo:
#   Entra a https://api.deezer.com/chart y busca el país

PLAYLISTS_DEEZER = {
    "PY": "1362520135",   # Top Paraguay  ← este era el que estaba mal
    "ES": "1362526775",   # Top España
    "MX": "1362526395",   # Top México
    "AR": "1362526555",   # Top Argentina
    "CO": "1362527575",   # Top Colombia
}

# Cuántas canciones pedir (máximo 100 en Deezer)
LIMITE_TRACKS = 100