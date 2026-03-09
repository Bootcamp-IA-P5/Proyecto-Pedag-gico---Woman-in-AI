"""
backend/app/src/processor/normalize_lyrics.py

Normalización de letras usando Groq LLM.
Limpia el texto crudo extraído para dejarlo listo para análisis.
"""
from app.src.config.groq_config import obtener_cliente_groq, GROQ_MODEL

PROMPT_NORMALIZACION = """Eres un asistente que normaliza letras de canciones en español para análisis de texto.

Reglas estrictas — aplica TODAS:
1. Convierte todo el texto a minúsculas.
2. Elimina todas las etiquetas de sección: CORO, VERSO, BRIDGE, INTRO, OUTRO, PRE-CORO, POST-CORO, ESTRIBILLO, HOOK, y cualquier variación entre corchetes o paréntesis como [Coro], (Verso 1), etc.
3. Elimina onomatopeyas y vocalizaciones sin significado: eh, oh, ah, uh, yeah, yeh, la la la, na na na, pa pa pa, ra ta ta, mmm, hmm, wow, ey, hey, ooh, uuh, y similares.
4. Elimina signos de exclamación (¡!), interrogación (¿?), y otros caracteres especiales como *, #, ~, —, –, pero MANTÉN la ñ, las tildes (á, é, í, ó, ú) y la ü porque son parte del español.
5. Elimina líneas vacías y espacios extra. Cada verso debe estar en su propia línea.
6. Elimina textos descriptivos como "(x2)", "(bis)", "(repite)", o indicaciones musicales.
7. NO añadas explicaciones, comentarios ni texto adicional. Devuelve SOLO la letra limpia.

Letra a normalizar:
{lyrics}"""


def normalizar_letra(lyrics_raw: str) -> str | None:
    """
    Envía la letra cruda al LLM Groq para normalizarla.
    Retorna la letra limpia o None si hay error.
    """
    if not lyrics_raw or not lyrics_raw.strip():
        return None

    client = obtener_cliente_groq()

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": PROMPT_NORMALIZACION.format(lyrics=lyrics_raw),
                }
            ],
            temperature=0.0,  # Determinístico — no queremos creatividad aquí
            max_tokens=4000,
        )

        letra_limpia = response.choices[0].message.content.strip()

        if not letra_limpia:
            print("  ⚠️ Groq devolvió una respuesta vacía")
            return None

        return letra_limpia

    except Exception as e:
        print(f"  ⚠️ Error al normalizar con Groq: {e}")
        return None
