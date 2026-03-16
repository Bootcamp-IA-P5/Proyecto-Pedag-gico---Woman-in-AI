import os
import re
import json
import time
import unicodedata
import requests as http_requests
from dotenv import load_dotenv
from groq import Groq
from difflib import SequenceMatcher

load_dotenv()

# LLMs
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
groq_client  = Groq(api_key=os.getenv("GROQ_API_KEY"))
# Países
PAISES_ISO = {
    # Existentes y corregidos
    "PY": "PY", "PARAGUAY": "PY",
    "ES": "ES", "ESPANA": "ES", "ESPAÑA": "ES", "SPAIN": "ES",
    "MX": "MX", "MEXICO": "MX",
    "AR": "AR", "ARGENTINA": "AR",
    "CO": "CO", "COLOMBIA": "CO",
    "CL": "CL", "CHILE": "CL",
    "PE": "PE", "PERU": "PE",
    "US": "US", "USA": "US", "ESTADOS UNIDOS": "US", "UNITED STATES": "US",

    # Cono Sur
    "UY": "UY", "URUGUAY": "UY",
    "BR": "BR", "BRASIL": "BR", "BRAZIL": "BR",

    # Región Andina
    "VE": "VE", "VENEZUELA": "VE",
    "EC": "EC", "ECUADOR": "EC",
    "BO": "BO", "BOLIVIA": "BO",

    # Centroamérica
    "CR": "CR", "COSTA RICA": "CR",
    "PA": "PA", "PANAMA": "PA",
    "GT": "GT", "GUATEMALA": "GT",
    "HN": "HN", "HONDURAS": "HN",
    "SV": "SV", "EL SALVADOR": "SV",
    "NI": "NI", "NICARAGUA": "NI",

    # Caribe
    "DO": "DO", "REPUBLICA DOMINICANA": "DO", "DOMINICAN REPUBLIC": "DO",
    "PR": "PR", "PUERTO RICO": "PR",
    "CU": "CU", "CUBA": "CU",
}

# Sesión de títulos procesados
_titulos_sesion: set[str] = set()


def quitar_tildes(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

# ─── Limpieza de texto ─────────────────────────────────────────────
def limpiar_texto(texto: str | None) -> str | None:
    if not texto:
        return None

    texto = texto.strip()

    # Quitar emojis
    texto = re.sub(r'[\U00010000-\U0010ffff]', '', texto)

    # 🔧 CAMBIO 1
    # Antes eliminabas todo dentro del paréntesis.
    # Ahora mantenemos "remix" si aparece.

    def _procesar_parentesis(match):
        contenido = match.group(1)

        if re.search(r'\bremix\b', contenido, re.IGNORECASE):
            return " remix "

        return " "

    texto = re.sub(r'\((.*?)\)', _procesar_parentesis, texto)

    # eliminar corchetes completamente
    texto = re.sub(r'\[.*?\]', ' ', texto)

    # Quitar feat, ft, featuring, with
    texto = re.sub(r'\b(feat|ft|featuring|with)\b.*', '', texto, flags=re.IGNORECASE)

    # Quitar tildes y poner minúsculas
    texto = quitar_tildes(texto).lower()

    # Separadores y guiones → espacio
    texto = re.sub(r'[\/\|#\\~\^*+=<>@%]', ' ', texto)
    texto = re.sub(r'(?<=\w)-(?=\w)', ' ', texto)

    # Quitar comillas y signos
    texto = re.sub(r'[\"\'`´\u201c\u201d\u2018\u2019!¡?¿]', '', texto)

    # Quitar caracteres no latinos
    texto = re.sub(r'[^\x00-\x7F\u00C0-\u024F]', '', texto)

    # Solo letras, números y espacios
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)

    # Quitar números aislados 2-4 dígitos
    texto = re.sub(r'\b\d{2,4}\b', '', texto)

    # Colapsar espacios
    texto = re.sub(r'\s+', ' ', texto)

    # Unir letras separadas: q u e v a s → quevas
    texto = re.sub(
        r'\b(?:[a-z]\s){2,}[a-z]\b',
        lambda m: m.group(0).replace(' ', ''),
        texto
    )

    # 🔧 CAMBIO 2
    # eliminar letras repetidas (despacitooo → despacito)
    texto = re.sub(r'(.)\1{2,}', r'\1', texto)

    # 🔧 CAMBIO 3
    # corregir error común despasito → despacito
    texto = texto.replace("pasito", "pacito")

    # 🔧 CAMBIO 4
    # normalizar remix para evitar duplicados
    if re.search(r'\bremix\b', texto):
        texto = re.sub(r'\bremix\b', '', texto)
        texto = texto.strip() + " remix"

    return texto.strip()

def normalizar_pais(pais: str | None) -> str | None:
    if not pais:
        return None
    pais_limpio = quitar_tildes(pais.upper().strip())
    return PAISES_ISO.get(pais_limpio, pais_limpio)

# ─── Normalización básica ─────────────────────────────────────────
def normalizar_track_sin_llm(track: dict) -> dict:
    track["title"]  = limpiar_texto(track.get("title"))
    track["artist"] = limpiar_texto(track.get("artist"))
    track["album"]  = limpiar_texto(track.get("album"))
    if track.get("extra_data") is None:
        track["extra_data"] = {}
    pais = track["extra_data"].get("pais") or track.get("country")
    track["extra_data"]["pais"] = normalizar_pais(pais)
    return track

def similitud(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

# ─── Detección de duplicados ──────────────────────────────────────
def es_duplicado(title_limpio: str) -> bool:
    from app.src.config.supabase_client import supabase

    if title_limpio in _titulos_sesion:
        print(f"  🚫 Duplicado en sesión: {title_limpio}")
        return True

    try:
        # buscar títulos parecidos
        resultado = (
            supabase
            .table("lyrics")
            .select("id,title,genre")
            .ilike("title", f"%{title_limpio[:6]}%")
            .limit(20)
            .execute()
        )

        for row in resultado.data:

            titulo_db = row["title"]

            # comparar similitud
            if similitud(title_limpio, titulo_db) > 0.92:
                _titulos_sesion.add(title_limpio)

                if row.get("genre") is None:
                    return False

                print(f"  ⏭️ Similar encontrado: {titulo_db}")
                return True

    except Exception:
        pass

    _titulos_sesion.add(title_limpio)
    return False

def reset_sesion():
    _titulos_sesion.clear()

# ─── LLM ─────────────────────────────────────────────────────────
PROMPT_TEMPLATE = """Analiza este track musical y responde SOLO con JSON valido, sin texto extra.
Track:
- Titulo: {title}
- Artista: {artist}
Responde exactamente con este formato:
{{
  "idioma": "es|en|pt|other",
  "genero": "reggaeton|pop|trap|bachata|cumbia|rock|electronica|infantil|other",
  "es_infantil": false,
  "artista_principal": "nombre del artista principal en minusculas sin tildes",
  "artistas_secundarios": [],
  "title_limpio": "titulo en minusculas sin tildes sin caracteres especiales"
}}
Reglas:
- idioma: detecta el idioma principal por titulo y artista
- genero: elige el mas probable segun artista y titulo
- es_infantil: true si parece cancion para ninos
- artistas_secundarios: extrae los feat. si los hay en minusculas
- title_limpio: todo en minusculas sin tildes sin caracteres especiales
"""

def parsear_respuesta_llm(contenido: str) -> dict:
    contenido = re.sub(r'^```json|^```|```$', '', contenido, flags=re.MULTILINE).strip()
    return json.loads(contenido)

def llamar_ollama(prompt: str) -> dict:
    respuesta = http_requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model":    OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream":   False,
            "options":  {"temperature": 0},
        },
        timeout=1,
    )
    respuesta.raise_for_status()
    contenido = respuesta.json()["message"]["content"]
    return parsear_respuesta_llm(contenido.strip())

def llamar_groq(prompt: str) -> dict:
    respuesta = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=300,
    )
    return parsear_respuesta_llm(respuesta.choices[0].message.content.strip())

def normalizar_track_con_llm(track: dict) -> dict:
    title, artist = track.get("title", ""), track.get("artist", "")
    prompt = PROMPT_TEMPLATE.format(title=title, artist=artist)
    datos = None
    try:
        datos = llamar_ollama(prompt)
        print(f"  🟣 Ollama: {title} → {datos.get('genero')} | {datos.get('idioma')}")
    except Exception as e_ollama:
        print(f"  ⚠️ Ollama falló: {e_ollama}")
        try:
            datos = llamar_groq(prompt)
            print(f"  🟡 Groq: {title} → {datos.get('genero')} | {datos.get('idioma')}")
            time.sleep(1)
        except Exception as e_groq:
            print(f"  🔴 Groq falló: {e_groq} — continuando sin LLM")
    if datos:
        track["language_variant"] = datos.get("idioma")
        track["genre"] = datos.get("genero")
        track["artist"] = limpiar_texto(datos.get("artista_principal", track["artist"]))
        track["title"] = limpiar_texto(datos.get("title_limpio", track["title"]))
        if track.get("extra_data") is None:
            track["extra_data"] = {}
        track["extra_data"]["artistas_secundarios"] = datos.get("artistas_secundarios", [])
        track["extra_data"]["es_infantil"] = datos.get("es_infantil", False)
    return track

# ─── Normalización principal ───────────────────────────────────────
def normalizar_track(track: dict) -> dict:
    track = normalizar_track_sin_llm(track)
    if es_duplicado(track["title"]):
        return None
    track = normalizar_track_con_llm(track)
    return track