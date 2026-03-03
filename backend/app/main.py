from fastapi import FastAPI
from app.src.scraper.spotify_scraper import obtener_top_canciones
from app.src.processor.upload_to_supabase import subir_cancion

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Bienvenido al agente de scraping de canciones"}

def iniciar_agente():
    url_objetivo = "https://www.ejemplo-de-ranking.com" # Cambia esto por la URL real
    
    # PASO 1: El scraper busca la info
    lista_canciones = obtener_top_canciones(url_objetivo)
    
    # PASO 2: El procesador sube cada canción a Supabase
    for cancion in lista_canciones:
        subir_cancion(cancion)

if __name__ == "__main__":
    iniciar_agente()