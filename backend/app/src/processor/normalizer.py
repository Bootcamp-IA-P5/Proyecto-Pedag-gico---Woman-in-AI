"""
normalizer.py
Normaliza los datos de un track antes de subir a Supabase.
- Sin LLM: minusculas, sin tildes, sin espacios dobles, sin caracteres especiales
- Con LLM: primero intenta Gemini Flash, si falla intenta Groq, si falla continua sin normalizar
Ubicacion: backend/app/src/processor/normalizer.py
"""
import os
import re
import json
import time
import unicodedata
import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Configurar Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# Configurar Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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


def quitar_tildes(texto: str) -> str:
    """Quita tildes y caracteres diacriticos."""
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def limpiar_texto(texto: str | None) -> str | None:
    """
    Limpia un texto completamente:
    1.  Espacios al inicio y final
    2.  Quitar emojis
    3.  Quitar bloques entre parentesis: remasters, versiones, lives, ao vivo, feat, etc.
    4.  Quitar bloques entre corchetes
    5.  Quitar feat fuera de parentesis
    6.  Quitar tildes
    7.  Minusculas
    8.  Separadores raros → espacio
    9.  Guiones entre palabras → espacio
    10. Quitar comillas
    11. Quitar exclamaciones e interrogaciones
    12. Quitar caracteres no latinos
    13. Solo letras, numeros y espacios
    14. Quitar numeros aislados tipo 2011 2024
    15. Colapsar espacios multiples
    16. Letras sueltas separadas por espacios → palabra: q u e v a s → quevas
    17. Trim final
    """
    if not texto:
        return None

    # 1. Espacios al inicio y final
    texto = texto.strip()

    # 2. Quitar emojis
    texto = re.sub(r'[\U00010000-\U0010ffff]', '', texto)

    # 3. Quitar bloques entre parentesis
    bloques = [
        r'\(.*?remaster.*?\)',
        r'\(.*?version.*?\)',
        r'\(.*?edit.*?\)',
        r'\(.*?live.*?\)',
        r'\(.*?acoustic.*?\)',
        r'\(.*?instrumental.*?\)',
        r'\(.*?karaoke.*?\)',
        r'\(.*?sped up.*?\)',
        r'\(.*?slowed.*?\)',
        r'\(.*?reverb.*?\)',
        r'\(.*?mono.*?\)',
        r'\(.*?stereo.*?\)',
        r'\(.*?radio edit.*?\)',
        r'\(.*?extended.*?\)',
        r'\(.*?deluxe.*?\)',
        r'\(.*?bonus track.*?\)',
        r'\(.*?official video.*?\)',
        r'\(.*?official audio.*?\)',
        r'\(.*?lyric video.*?\)',
        r'\(.*?visualizer.*?\)',
        r'\(.*?from.*?\)',
        r'\(.*?soundtrack.*?\)',
        r'\(.*?banda sonora.*?\)',
        r'\(.*?tribute.*?\)',
        r'\(.*?cover.*?\)',
        r'\(.*?demo.*?\)',
        r'\(.*?ao vivo.*?\)',
        r'\(.*?en vivo.*?\)',
        r'\(.*?single.*?\)',
        r'\(.*?piano.*?\)',
        r'\(.*?feat.*?\)',
        r'\(.*?ft\..*?\)',
        r'\(.*?remix.*?\)',
        r'\(.*?premium.*?\)',
    ]
    for bloque in bloques:
        texto = re.sub(bloque, '', texto, flags=re.IGNORECASE)

    # 4. Quitar bloques entre corchetes
    texto = re.sub(r'\[.*?\]', '', texto)

    # 5. Quitar feat fuera de parentesis
    texto = re.sub(
        r'\b(feat|ft|featuring|with)\b.*',
        '',
        texto,
        flags=re.IGNORECASE
    )

    # 6. Quitar tildes
    texto = quitar_tildes(texto)

    # 7. Minusculas
    texto = texto.lower()

    # 8. Separadores raros → espacio
    texto = re.sub(r'[\/\|#\\~\^*+=<>@%]', ' ', texto)

    # 9. Guiones entre palabras → espacio
    texto = re.sub(r'(?<=\w)-(?=\w)', ' ', texto)

    # 10. Quitar comillas
    texto = re.sub(r'[\"\'`´\u201c\u201d\u2018\u2019]', '', texto)

    # 11. Quitar exclamaciones e interrogaciones
    texto = re.sub(r'[!¡?¿]', '', texto)

    # 12. Quitar caracteres no latinos: cirílico, árabe, chino, etc.
    texto = re.sub(r'[^\x00-\x7F\u00C0-\u024F]', '', texto)

    # 13. Solo letras, numeros y espacios
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)

    # 14. Quitar numeros aislados tipo 2011, 2024
    texto = re.sub(r'\b\d{2,4}\b', '', texto)

    # 15. Colapsar espacios multiples
    texto = re.sub(r'\s+', ' ', texto)

    # 16. Letras sueltas separadas por espacios → palabra: q u e v a s → quevas
    texto = re.sub(
        r'\b(\w)(\s\w)+\b',
        lambda m: m.group(0).replace(' ', ''),
        texto
    )

    # 17. Trim final
    texto = texto.strip()

    return texto


def normalizar_pais(pais: str | None) -> str | None:
    """Convierte cualquier nombre de pais a su ISO correcto."""
    if not pais:
        return None
    pais_limpio = quitar_tildes(pais.upper().strip())
    return PAISES_ISO.get(pais_limpio, pais_limpio)


def normalizar_track_sin_llm(track: dict) -> dict:
    """Normalizacion rapida sin LLM."""
    track["title"]  = limpiar_texto(track.get("title"))
    track["artist"] = limpiar_texto(track.get("artist"))
    track["album"]  = limpiar_texto(track.get("album"))

    if track.get("extra_data") is None:
        track["extra_data"] = {}

    pais = track["extra_data"].get("pais") or track.get("country")
    track["extra_data"]["pais"] = normalizar_pais(pais)

    return track


# ← NUEVO: evita gastar tokens si el titulo ya existe en Supabase
def titulo_ya_existe_en_supabase(title_limpio: str) -> bool:
    """
    Comprueba si el titulo ya existe EN Supabase Y ya tiene genre.
    Si existe pero no tiene genre, devuelve False para que el LLM lo procese.
    """
    from app.src.config.supabase_client import supabase
    try:
        resultado = supabase.table("songs") \
            .select("id, genre") \
            .ilike("title", title_limpio) \
            .limit(1) \
            .execute()
        if not resultado.data:
            return False
        # Solo salta el LLM si ya tiene genre relleno
        return resultado.data[0].get("genre") is not None
    except Exception:
        return False


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
    """Limpia y parsea el JSON que devuelve el LLM."""
    contenido = re.sub(r'^```json|^```|```$', '', contenido, flags=re.MULTILINE).strip()
    return json.loads(contenido)


def llamar_gemini(prompt: str) -> dict:
    """Llama a Gemini Flash y devuelve el JSON parseado."""
    respuesta = gemini_model.generate_content(prompt)
    return parsear_respuesta_llm(respuesta.text.strip())


def llamar_groq(prompt: str) -> dict:
    """Llama a Groq llama-3.1-8b-instant y devuelve el JSON parseado."""
    respuesta = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=300,
    )
    return parsear_respuesta_llm(respuesta.choices[0].message.content.strip())


def normalizar_track_con_llm(track: dict) -> dict:
    """
    Normalizacion con LLM.
    1. Intenta con Gemini Flash
    2. Si Gemini falla intenta con Groq
    3. Si los dos fallan continua sin normalizar
    """
    title  = track.get("title", "")
    artist = track.get("artist", "")
    prompt = PROMPT_TEMPLATE.format(title=title, artist=artist)
    datos  = None

    # Intento 1 — Gemini
    try:
        datos = llamar_gemini(prompt)
        print(f"  🟢 Gemini: {track['title']} → {datos.get('genero')} | {datos.get('idioma')}")
        time.sleep(1)
    except Exception as e_gemini:
        print(f"  ⚠️  Gemini fallo para '{title}': {e_gemini}")

        # Intento 2 — Groq
        try:
            datos = llamar_groq(prompt)
            print(f"  🟡 Groq: {track['title']} → {datos.get('genero')} | {datos.get('idioma')}")
            time.sleep(1)
        except Exception as e_groq:
            print(f"  🔴 Groq fallo para '{title}': {e_groq} — continuando sin normalizar")

    # Aplicar datos si alguno de los dos respondio
    if datos:
        track["language_variant"] = datos.get("idioma")
        track["genre"]            = datos.get("genero")
        track["artist"]           = limpiar_texto(datos.get("artista_principal", track["artist"]))
        track["title"]            = limpiar_texto(datos.get("title_limpio", track["title"]))

        if track.get("extra_data") is None:
            track["extra_data"] = {}
        track["extra_data"]["artistas_secundarios"] = datos.get("artistas_secundarios", [])
        track["extra_data"]["es_infantil"]          = datos.get("es_infantil", False)

    return track


def normalizar_track(track: dict) -> dict:
    """
    Funcion principal que llaman los scrapers.
    1. Limpia sin LLM (rapido)
    2. Comprueba si el titulo ya existe — si existe no gasta tokens  ← NUEVO
    3. Enriquece con LLM solo si es cancion nueva                    ← NUEVO
    """
    track = normalizar_track_sin_llm(track)

    # ← NUEVO: si ya existe en Supabase no llama al LLM
    if titulo_ya_existe_en_supabase(track["title"]):
        print(f"  ⏭️  Ya existe en Supabase, sin LLM: {track['title']}")
        return track

    track = normalizar_track_con_llm(track)
    return track