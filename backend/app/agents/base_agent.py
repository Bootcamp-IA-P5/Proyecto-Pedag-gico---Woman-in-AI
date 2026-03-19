# backend/app/agents/base_agent.py
import os
import json
import httpx
from abc import ABC
from dotenv import load_dotenv
from langfuse.decorators import observe, langfuse_context


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

    @observe(as_type="generation")
    async def analizar(self, letra: str, proveedor: str = "groq") -> dict:
        config = PROVEEDORES.get(proveedor)
        if not config:
            raise ValueError(f"Proveedor desconocido: {proveedor}")
        required_keys = ("url", "key", "model")
        missing = [k for k in required_keys if not config.get(k)]
        if missing:
            raise ValueError(
                f"Configuración incompleta para el proveedor '{proveedor}': "
                f"faltan {', '.join(missing)}. Revisa las variables de entorno correspondientes."
            )

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

        messages_payload = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user",   "content": user_message},
        ]
        langfuse_context.update_current_observation(
            model=config["model"],
            input=messages_payload,
            metadata={"proveedor": proveedor, "dimension": self.dimension}
        )

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
                    "messages": messages_payload,
                }
            )
            response.raise_for_status()

        resp_json = response.json()
        raw = resp_json["choices"][0]["message"]["content"].strip()
        usage_data = resp_json.get("usage", {})
        usage = {
            "input": int(usage_data.get("prompt_tokens", 0) or 0),
            "output": int(usage_data.get("completion_tokens", 0) or 0),
            "total": int(usage_data.get("total_tokens", 0) or 0)
        }

        try:
            resultado = json.loads(raw)
        except json.JSONDecodeError:
            raw_clean = raw.replace("```json", "").replace("```", "").strip()
            resultado = json.loads(raw_clean)

        validado = self._validar(resultado)
        validado["modelo"] = f"{proveedor}/{config['model']}"
        
        langfuse_context.update_current_observation(
            usage_details=usage,
            output=validado
        )
        
        return validado

    def _validar(self, resultado: dict) -> dict:
        return {
            "dimension":     resultado.get("dimension",     self.dimension),
            "puntuacion":    max(0, min(3, int(resultado.get("puntuacion", 0)))),
            "fragmentos":    resultado.get("fragmentos",    []),
            "justificacion": resultado.get("justificacion", ""),
        }