# backend/app/agents/base_agent.py
import os
import json
import httpx
from abc import ABC
from dotenv import load_dotenv


load_dotenv()

PROVEEDORES = {
    "groq": {
        "url":   "https://api.groq.com/openai/v1/chat/completions",
        "key":   os.getenv("GROQ_API_KEY"),
        "model": "llama-3.3-70b-versatile",
    },
    "openrouter": {
        "url":   os.getenv("OPEN_ROUTER_URL"),
        "key":   os.getenv("OPEN_ROUTER_KEY"),
        "model": os.getenv("OPEN_ROUTER_MODEL", "google/gemini-2.5-flash"),
    },
}


class BaseAgent(ABC):

    dimension: str = ""
    system_prompt: str = ""

    async def analizar(self, letra: str, proveedor: str = "groq") -> dict:
        config = PROVEEDORES.get(proveedor)
        if not config:
            raise ValueError(f"Proveedor desconocido: {proveedor}")

        user_message = f"""Analiza la siguiente letra de canción en español \
y devuelve ÚNICAMENTE un JSON válido, sin texto adicional ni bloques markdown.

LETRA:
\"\"\"{letra}\"\"\"

El JSON debe seguir exactamente este formato:
{{
  "dimension": "{self.dimension}",
  "puntuacion": <entero entre 0 y 3>,
  "fragmentos": ["fragmento 1 de la letra", "fragmento 2 de la letra"],
  "justificacion": "explicación breve en español"
}}

Recuerda:
- puntuacion 0 = no se detecta nada
- puntuacion 1 = leve, insinuación o lenguaje ambiguo
- puntuacion 2 = moderado, patrón claro pero no explícito
- puntuacion 3 = grave, explícito, reiterativo o normalizador
- fragmentos debe estar vacío ([]) si puntuacion es 0
- Cita los fragmentos exactamente como aparecen en la letra"""

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                config["url"],
                headers={
                    "Authorization": f"Bearer {config['key']}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model":       config["model"],
                    "temperature": 0.1,
                    "max_tokens":  1024,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user",   "content": user_message},
                    ],
                }
            )
            response.raise_for_status()

        raw = response.json()["choices"][0]["message"]["content"].strip()

        try:
            resultado = json.loads(raw)
        except json.JSONDecodeError:
            raw_clean = raw.replace("```json", "").replace("```", "").strip()
            resultado = json.loads(raw_clean)

        validado = self._validar(resultado)
        validado["modelo"] = f"{proveedor}/{config['model']}"
        return validado

    def _validar(self, resultado: dict) -> dict:
        return {
            "dimension":     resultado.get("dimension",     self.dimension),
            "puntuacion":    max(0, min(3, int(resultado.get("puntuacion", 0)))),
            "fragmentos":    resultado.get("fragmentos",    []),
            "justificacion": resultado.get("justificacion", ""),
        }