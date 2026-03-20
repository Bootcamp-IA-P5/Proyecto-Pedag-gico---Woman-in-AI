import re
import hashlib
import musicbrainzngs
from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException


from app.src.config.BeautifulSoup_config import HEADERS, MUSICBRAINZ_EMAIL

try:
    from app.src.processor.normalizer_letras import normalizar_letra_super_analitica as normalizar_letra
except ImportError:
    # Fallback temporal por si hubiera algun problema con la importación
    def normalizar_letra(texto):
        return {
            "letra_limpia": texto.strip(),
            "num_versos": len([line for line in texto.split('\n') if line.strip()]),
            "num_exclamaciones": texto.count('!'),
            "num_interrogaciones": texto.count('?'),
            "num_coros": 0,
            "num_estrofas": 0,
            "num_ruidos": 0,
            "versos": [],
            "frases_clave": []
        }

musicbrainzngs.set_useragent("ScraperLetras", "1.0", str(MUSICBRAINZ_EMAIL or "bot@ejemplo.com"))
# Lista de artistas para cuando se nos acaben los charts
ARTISTAS_EXTRA = [
    "rosalia", "c-tangana", "bad-bunny", "quevedo", "rauw-alejandro",
    "bizarrap", "feid", "karol-g", "ozuna", "anuel-aa", "j-balvin",
    "shakira", "maluma", "duki"
]

ANIOS_PERMITIDOS = {2023, 2024, 2025, 2026}
IDIOMAS_ESPANOL_VALIDOS = {"es", "españa", "latam"}


def generar_hash(texto: str) -> str:
    """Genera hash único de la letra para evitar guardar duplicados."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def detectar_variante_idioma(texto: str) -> str:
    """Detecta si la letra tira a españa, latam, etc."""
    texto_lower = texto.lower()
    marcadores_españa = ["vosotros", "tío", "tía", "joder", "venga", "chavala", "mola", "guay"]
    marcadores_latam = ["ustedes", "chévere", "bacano", "ándale", "órale", "pana", "parcero"]
    marcadores_ingles = ["yeah", "baby", "love", "gang", "okay", "money", "flow", "swag"]

    puntos_españa = sum(1 for m in marcadores_españa if m in texto_lower)
    puntos_latam = sum(1 for m in marcadores_latam if m in texto_lower)
    puntos_ingles = sum(1 for m in marcadores_ingles if m in texto_lower)

    if puntos_ingles >= 3 and (puntos_españa > 0 or puntos_latam > 0):
        return "spanglish"
    elif puntos_españa > puntos_latam:
        return "españa"
    elif puntos_latam > 0:
        return "latam"
    else:
        return "es"


def limpiar_para_url(texto: str) -> str:
    """Adecúa el nombre del artista/canción para formar las URLs de letras.com."""
    texto = texto.lower().strip()
    texto = re.sub(r'[áäâà]', 'a', texto)
    texto = re.sub(r'[éëêè]', 'e', texto)
    texto = re.sub(r'[íïîì]', 'i', texto)
    texto = re.sub(r'[óöôò]', 'o', texto)
    texto = re.sub(r'[úüûù]', 'u', texto)
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    return texto.replace(" ", "-")


def obtener_canciones_del_chart(url: str, session) -> list:
    """Extrae las canciones de la lista Top de Letras.com."""
    canciones = []
    try:
        r = session.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            lista = soup.find("ol", class_="top-list_mus")
            if lista:
                items = lista.find_all("li")
                for item in items:
                    a_tag = item.find("a")
                    if a_tag:
                        # formato esperado href: /artista/cancion/
                        href = a_tag.get("href", "")
                        if href.startswith("/"):
                            partes = [p for p in href.split("/") if p]
                            if len(partes) >= 2:
                                artista = partes[0].replace("-", " ").title()
                                titulo = partes[1].replace("-", " ").title()
                                canciones.append({
                                    "artista": artista,
                                    "titulo": titulo,
                                    "url": f"https://www.letras.com{href}"
                                })
    except Exception as e:
        print(f"Error al parsear el chart {url}: {e}")
    return canciones


def obtener_canciones_del_artista(slug: str, session) -> list:
    """Extrae canciones de un artista específico (ampliación)."""
    canciones = []
    url = f"https://www.letras.com/{slug}/mais_acessadas.html"
    try:
        r = session.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            ol = soup.find("ol", class_="cnt-list")
            if ol:
                items = ol.find_all("li")
                for item in items:
                    a_tag = item.find("a")
                    if a_tag:
                        href = a_tag.get("href", "")
                        titulo = item.get_text().strip()
                        canciones.append({
                            "artista": slug.replace("-", " ").title(),
                            "titulo": titulo,
                            "url": f"https://www.letras.com{href}"
                        })
    except Exception:
        pass
    return canciones


def validar_anio(artist: str, title: str) -> tuple[bool, int]:
    """Solo permite canciones con año 2023-2026 según MusicBrainz."""
    try:
        resultado = musicbrainzngs.search_recordings(recording=title, artist=artist, limit=5)
        recordings = resultado.get("recording-list", [])
        for rec in recordings:
            for release in rec.get("release-list", []):
                fecha = release.get("date", "")
                if fecha and len(fecha) >= 4:
                    anio = int(fecha[:4])
                    if anio in ANIOS_PERMITIDOS:
                        return True, anio
                    return False, anio
    except Exception:
        pass
    return False, 0


def scrape_lyrics(url: str, session) -> str | None:
    """Obtiene el texto de la letra dada la URL."""
    try:
        response = session.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
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
                # Limpiar la basura extraña del HTML
                for tag in container(["script", "style", "aside", "button", "a"]):
                    tag.decompose()
                texto = container.get_text(separator="\n").strip()
                lineas = [linea.strip() for linea in texto.splitlines()]
                texto_limpio = "\n".join(linea for linea in lineas if linea)
                return texto_limpio if len(texto_limpio) > 50 else None
    except Exception:
        pass
    return None


def validar_idioma(texto: str) -> tuple[bool, str]:
    """Solo acepta español (es/españa/latam)."""
    try:
        idioma = detect(texto[:500]).lower()
        if idioma in IDIOMAS_ESPANOL_VALIDOS:
            return True, idioma
        return False, idioma
    except LangDetectException:
        return False, "unknown"


def limpiar_letra(texto: str) -> str:
    """Pasa por una limpieza en crudo rápido."""
    texto = re.sub(
        r'\b(eh|ah|oh|uh|mm+|hm+|na+|la+|ra+|ta+|pa+|ba+|ja+|ha+|ye+|wo+|ay+|ey+)\b',
        '',
        texto,
        flags=re.IGNORECASE
    )
    texto = re.sub(r'\s+', ' ', texto) # colapsar saltos y espacios múltiples
    return texto.strip()


def ya_existe(supabase, artista: str, titulo: str) -> bool:
    """Verifica en Supabase si esta canción ya fue guardada en la tabla lyrics."""
    # 1. Buscamos el ID de la canción en la tabla songs
    res_song = supabase.table("songs").select("id").eq("artist", artista).eq("title", titulo).execute()
    if not res_song.data:
        return False
    
    song_id = res_song.data[0]["id"]
    
    # 2. Verificamos si ya existe una entrada en la tabla lyrics para ese song_id
    res_lyrics = supabase.table("lyrics").select("id").eq("song_id", song_id).execute()
    return len(res_lyrics.data) > 0


def guardar_cancion(supabase, artista: str, titulo: str, letra_cruda: str, anio: int, idioma: str) -> None:
    """Aplica normalización analítica y la guarda en la tabla lyrics, vinculada a songs."""
    
    # 1. Aseguramos que la canción exista en la tabla 'songs'
    res_song = supabase.table("songs").select("id, year").eq("artist", artista).eq("title", titulo).execute()
    
    if res_song.data:
        song_id = res_song.data[0]["id"]
        year_actual = res_song.data[0].get("year")
        if anio in ANIOS_PERMITIDOS and anio != year_actual:
            supabase.table("songs").update({"year": anio}).eq("id", song_id).execute()
    else:
        # Creamos la canción si no existe
        res_insert = supabase.table("songs").insert({
            "artist": artista,
            "title": titulo,
            "year": anio if anio in ANIOS_PERMITIDOS else None,
            "lyrics_status": "pending"
        }).execute()
        if not res_insert.data:
            print(f"❌ Error al crear la canción '{titulo}' en songs.")
            return
        song_id = res_insert.data[0]["id"]

    # 2. Normalizamos la letra
    resultado_norm = normalizar_letra(letra_cruda)
    letra_norm = resultado_norm.get("letra_limpia", letra_cruda)
    
    # 3. Preparamos los datos para la tabla 'lyrics'
    datos_lyrics = {
        "song_id": song_id,
        "lyrics_text": letra_norm,
        "lyrics_hash": generar_hash(letra_norm),
        "word_count": len(letra_norm.split()),
        "verse_count": resultado_norm.get("num_versos", 0),
        "language_detected": detectar_variante_idioma(letra_norm),
        "source": "letras.com"
    }
    
    # Extra data opcional: si quieres guardarlo, tendrías que ver si la tabla lyrics tiene esa columna
    # Por ahora nos ceñimos a las columnas confirmadas por el usuario.
    
    # 4. Guardamos en la tabla 'lyrics'
    # Verificamos si ya existe para este song_id
    res_check = supabase.table("lyrics").select("id").eq("song_id", song_id).execute()
    
    if res_check.data:
        # Update
        supabase.table("lyrics").update(datos_lyrics).eq("song_id", song_id).execute()
        print(f"✅ Letra actualizada en tabla 'lyrics' para ID {song_id}")
    else:
        # Insert
        supabase.table("lyrics").insert(datos_lyrics).execute()
        print(f"✅ Letra insertada en tabla 'lyrics' para ID {song_id}")
    
    # 5. Marcamos la canción como completada en la tabla songs
    supabase.table("songs").update({"lyrics_status": "completed"}).eq("id", song_id).execute()
