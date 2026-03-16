"""
backend/app/src/processor/normalize_lyrics.py

Normalización de letras usando Expresiones Regulares (Regex).
Limpia el texto crudo extraído para dejarlo listo para análisis
sin gastar tokens de IA y de forma instantánea.
"""

import re


def normalizar_letra(lyrics_raw: str) -> str | None:
    """
    Limpia la letra usando expresiones regulares (Regex).
    Retorna la letra limpia o None si hay error.
    """
    if not lyrics_raw or not lyrics_raw.strip():
        return None

    try:
        # 1. Todo a minúsculas
        texto = lyrics_raw.lower()

        # 2. Eliminar etiquetas entre corchetes o paréntesis (Ej: [Intro], (Coro), [Verse 1])
        texto = re.sub(r"\[.*?\]", "", texto)
        texto = re.sub(r"\(.*?\)", "", texto)

        # 3. Eliminar signos de puntuación no deseados, manteniendo vocales con tilde y la ñ
        # Mantenemos: a-z, espacios, saltos de línea, áéíóú, ü y ñ.
        texto = re.sub(r"[^\w\s\n\nñáéíóúü]", "", texto)

        # 4. Eliminar lineas de onomatopeyas repetitivas (opcional grueso)
        lineas = texto.split("\n")
        lineas_limpias = []
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue
            # Ignorar lineas que sean puro "oh oh oh" o "yeah" repetido
            if re.match(r"^(oh\s*|ah\s*|uh\s*|yeah\s*|la\s*|na\s*)+$", linea):
                continue
            lineas_limpias.append(linea)

        letra_final = "\n".join(lineas_limpias)

        return letra_final if letra_final else None

    except Exception as e:
        print(f"  ⚠️ Error al normalizar con Regex: {e}")
        return None
