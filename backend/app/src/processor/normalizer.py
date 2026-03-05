import os
import re
import json
import time
import unicodedata
from dotenv import load_dotenv
import google.generativeai as genai
from groq import Groq

load_dotenv()

# LLMs
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-2.0-flash")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Países
PAISES_ISO = {
    "PY": "PY", "PARAGUAY": "PY",
    "ES": "ES", "ESPANA": "ES", "SPAIN": "ES",
    "MX": "MX", "MEXICO": "MX",
    "AR": "AR", "ARGENTINA": "AR",
    "CO": "CO", "COLOMBIA": "CO",
    "CL": "CL", "CHILE": "CL",
    "PE": "PE", "PERU": "PE",
    "US": "US", "USA": "US", "ESTADOS UNIDOS": "US",
}

# Sesión de títulos procesados
_titulos_sesion: set[str] = set()

# ─── Limpieza de texto ─────────────────────────────────────────────
def quitar_tildes(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))

def limpiar_texto(texto: str | None) -> str | None:
    if not texto:
        return None

    texto = texto.strip()
    # Quitar emojis
    texto = re.sub(r'[\U00010000-\U0010ffff]', '', texto)
    # Quitar paréntesis y corchetes problemáticos
    texto = re.sub(r'\(.*?\)|\[.*?\]', '', texto)
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
    texto = re.sub(r'\b(\w)(\s\w)+\b', lambda m: m.group(0).replace(' ', ''), texto)
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

# ─── Detección de duplicados ──────────────────────────────────────
def es_duplicado(title_limpio: str) -> bool:
    from app.src.config.supabase_client import supabase
    if title_limpio in _titulos_sesion:
        print(f"  🚫 Duplicado en sesión: {title_limpio}")
        return True
    try:
        resultado = supabase.table("songs").select("id, genre").ilike("title", title_limpio).limit(1).execute()
        if resultado.data:
            _titulos_sesion.add(title_limpio)
            if resultado.data[0].get("genre") is None:
                return False
            print(f"  ⏭️ Ya existe en Supabase: {title_limpio}")
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

def llamar_gemini(prompt: str) -> dict:
    respuesta = gemini_model.generate_content(prompt)
    return parsear_respuesta_llm(respuesta.text.strip())

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
        datos = llamar_gemini(prompt)
        print(f"  🟢 Gemini: {title} → {datos.get('genero')} | {datos.get('idioma')}")
        time.sleep(1)
    except Exception as e_gemini:
        print(f"  ⚠️ Gemini falló: {e_gemini}")
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