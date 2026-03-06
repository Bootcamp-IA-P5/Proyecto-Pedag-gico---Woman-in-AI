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
    # Cono Sur
    "PY": "1362520135",  # Paraguay
    "AR": "1362526555",  # Argentina
    "CL": "1362527395",  # Chile
    "UY": "1362528395",  # Uruguay
    "BR": "1116190441",  # Brasil

    # Región Andina
    "CO": "1362527575",  # Colombia
    "PE": "1362527835",  # Perú
    "EC": "1362528095",  # Ecuador
    "VE": "1362528255",  # Venezuela
    "BO": "1362528535",  # Bolivia

    # Centroamérica
    "CR": "1362528755",  # Costa Rica
    "PA": "1362528995",  # Panamá
    "GT": "1362529235",  # Guatemala
    "HN": "1362529455",  # Honduras
    "SV": "1362529635",  # El Salvador
    "NI": "1362529815",  # Nicaragua

    # Norteamérica y Caribe
    "MX": "1362526395",  # México
    "US": "1116189071",  # USA (Enfoque Latino)
    "DO": "1362530035",  # República Dominicana
    "PR": "1362530275",  # Puerto Rico

    # Europa
    "ES": "1362526775",  # España
}

# Cuántas canciones pedir (máximo 100 en Deezer)
LIMITE_TRACKS = 100