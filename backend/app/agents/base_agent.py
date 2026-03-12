"""
Clase base para todos los agentes de detección de sesgo.
Cada agente de dimensión hereda de esta clase.
Usa Groq API con el modelo llama-3.3-70b-versatile.
"""

import os
import json
import httpx
from abc import ABC
from dotenv import load_dotenv

load_dotenv()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL        = "llama-3.3-70b-versatile"


class BaseAgent(ABC):

    # Cada subclase define su dimensión y su system prompt
    dimension: str = ""
    system_prompt: str = ""

    async def analizar(self, letra: str) -> dict:
        """
        Envía la letra a Groq con el system prompt de esta dimensión.
        Devuelve un dict validado con fragmentos, puntuación y justificación.
        """
        user_message = f"""Analiza la siguiente letra de canción en español y devuelve ÚNICAMENTE un JSON válido, sin texto adicional ni bloques de código markdown.

LETRA:
\"\"\"
{letra}
\"\"\"

El JSON debe seguir exactamente este formato:
{{
  "dimension": "{self.dimension}",
  "puntuacion": <entero entre 0 y 3>,
  "fragmentos": ["fragmento 1 de la letra", "fragmento 2 de la letra"],
  "justificacion": "explicación breve en español de por qué se asigna esa puntuación"
}}

"""Recuerda:
- puntuacion 0 = no se detecta nada
- puntuacion 1 = leve, insinuación o lenguaje ambiguo
- puntuacion 2 = moderado, patrón claro pero no explícito
- puntuacion 3 = grave, explícito, reiterativo o normalizador
- fragmentos debe estar vacío ([]) si puntuacion es 0
- Cita los fragmentos exactamente como aparecen en la letra"""

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model":       MODEL,
                    "temperature": 0.1,   # bajo para respuestas consistentes
                    "max_tokens":  1024,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user",   "content": user_message},
                    ],
                }
            )
            response.raise_for_status()

        raw = response.json()["choices"][0]["message"]["content"].strip()

        # Parseamos y validamos el JSON de respuesta
        try:
            resultado = json.loads(raw)
        except json.JSONDecodeError:
            # Si el modelo devuelve bloques markdown los limpiamos
            raw_clean = raw.replace("```json", "").replace("```", "").strip()
            resultado = json.loads(raw_clean)

        return self._validar(resultado)

    def _validar(self, resultado: dict) -> dict:
        """Garantiza que el resultado tiene la estructura correcta."""
        return {
            "dimension":     resultado.get("dimension",     self.dimension),
            "puntuacion":    max(0, min(3, int(resultado.get("puntuacion", 0)))),
            "fragmentos":    resultado.get("fragmentos",    []),
            "justificacion": resultado.get("justificacion", ""),
        }
