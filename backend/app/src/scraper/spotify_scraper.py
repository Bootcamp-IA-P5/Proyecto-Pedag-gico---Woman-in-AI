
import requests
from bs4 import BeautifulSoup

def obtener_top_canciones(url_lista):
    """
    Entra a una web y saca una lista de canciones.
    """
    print(f"🕵️ Buscando canciones en: {url_lista}")
    
    # 1. Pedimos permiso a la página
    headers = {"User-Agent": "Mozilla/5.0"}
    respuesta = requests.get(url_lista, headers=headers)
    
    if respuesta.status_code != 200:
        print("❌ No pude entrar a la web")
        return []

    # 2. Empezamos a "limpiar" el HTML
    sopa = BeautifulSoup(respuesta.text, 'html.parser')
    canciones_encontradas = []

    # --- NOTA PARA EL EQUIPO ---
    # Aquí es donde cada una ajustará según la página que elijan.
    # Ejemplo genérico (esto varía según la web):
    filas = sopa.find_all('tr') # Supongamos que están en una tabla

    for fila in filas:
        try:
            titulo = fila.find('h3').text.strip()
            artista = fila.find('span', class_='artist').text.strip()
            
            canciones_encontradas.append({
                "title": titulo,
                "artist": artista,
                "ranking_position": 1, # Esto se puede autoincrementar
                "streams": 0,
                "genre": "Desconocido",
                "lyrics": ""
            })
        except:
            continue

    return canciones_encontradas