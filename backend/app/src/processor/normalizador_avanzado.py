"""
backend/app/src/processor/normalizador_avanzado.py

Cerebro Global para la clasificación precisa de géneros musicales en Hispanoamérica.
Diseñado para eliminar el sesgo de "Todo es Reggaetón" al contextualizar a la IA
con los géneros oficiales del artista extraídos de Spotify (cuando están disponibles).
"""

import json
from pydantic import BaseModel, Field
from app.src.config.groq_config import obtener_cliente_groq, GROQ_MODEL


class MetadatosCancion(BaseModel):
    genero_musical: str = Field(
        description="El género musical estructurado. Ej: Pop, Vallenato, Cumbia, Salsa, Reggaeton, Musica Popular, Regional Mexicano, Rock, etc."
    )


PROMPT_SISTEMA_GLOBAL = """Eres un musicólogo experto y un analista de datos especializado en la música de toda Latinoamérica y España.
Tu tarea es clasificar el 'género musical' principal de una canción de forma extremadamente precisa.

REGLAS ESTRICTAS CONTRA EL SESGO:
1. NO ASUMAS QUE TODO ES 'REGGAETON' O 'URBANO'. Este es un sesgo común que debes evitar activamente.
2. Analiza el nombre del artista y, sobre todo, su contexto (Géneros de Spotify). 
3. Si el artista es representante de 'Música Popular Colombiana', 'Vallenato', 'Salsa', 'Cumbia', 'Regional Mexicano' o 'Bachata', categoriza en consecuencia. Ej: Jessi Uribe es 'Musica Popular', Diomedes Diaz es 'Vallenato'.
4. Normaliza el nombre del género de forma limpia e inicial mayúscula (Ej: 'Vallenato', no 'vallenato colombiano tradicional').
5. Responde estrictamente con un objeto JSON válido usando la clave "genero_musical". No agregues texto adicional.
"""


def normalizar_genero_global(
    titulo: str, artista: str, generos_spotify: str = "", genero_actual: str = ""
) -> str:
    """
    Toma el título, el artista y (opcionalmente) los géneros directos de Spotify
    para usar la IA y determinar el verdadero género general de la canción, sin sesgos.
    """
    cliente = obtener_cliente_groq()

    prompt_usuario = f"Título de la canción: {titulo}\nArtista: {artista}\n"
    if generos_spotify:
        prompt_usuario += f"Contexto - Géneros listados en Spotify para este artista: {generos_spotify}\n"

    prompt_usuario += "\nGenera el JSON con el género musical principal corregido."

    try:
        # Cambiamos intencionalmente al modelo rapido para evitar límites
        response = cliente.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA_GLOBAL},
                {"role": "user", "content": prompt_usuario},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        contenido = response.choices[0].message.content
        datos = json.loads(contenido)
        genero_limpio = datos.get("genero_musical", "Indefinido").strip().title()

        # Evitar guardar si la IA devuelve basura
        if genero_limpio == "Indefinido":
            return None

        return genero_limpio

    except Exception as e:
        print(f"❌ Error en normalizador_avanzado para '{titulo}': {e}")
        return None


# Bloque de prueba local para verificar que funciona
if __name__ == "__main__":
    print("🧪 Probando Cerebro Global Anti-Sesgo...\n")

    # Prueba 1: Un Vallenato (que antes seguro caía en Reggaeton si el modelo alucinaba)
    res1 = normalizar_genero_global(
        "El Cóndor Herido", "Diomedes Diaz", "vallenato, cumbia"
    )
    print(f"🎶 Diomedes Diaz - El Cóndor Herido -> {res1}")

    # Prueba 2: Música Popular (El mayor caso de sesgo actual)
    res2 = normalizar_genero_global(
        "Dulce Pecado", "Jessi Uribe", "cantautor colombiano, musica popular colombiana"
    )
    print(f"🎶 Jessi Uribe - Dulce Pecado -> {res2}")

    # Prueba 3: Reggaetón real
    res3 = normalizar_genero_global("Provenza", "Karol G", "reggaeton, pop urbano")
    print(f"🎶 Karol G - Provenza -> {res3}")
