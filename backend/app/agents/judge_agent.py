# backend/app/agents/judge_agent.py
import os
import json
import httpx

OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

SYSTEM_PROMPT_JUEZ = """Eres un juez experto en análisis de sesgos de género \
en canciones en español.

Recibirás:
1. La letra original de una canción
2. Dos evaluaciones de la misma dimensión hechas por modelos distintos

Tu trabajo es:
- Comprobar que los fragmentos citados realmente aparecen en la letra
- Decidir si la puntuación del 0 al 3 está bien justificada
- Si no estás de acuerdo, sugerir la puntuación correcta

ESCALA: 0=no presente, 1=leve, 2=claro, 3=extremo

Devuelve ÚNICAMENTE este JSON:
{
  "dimension": "nombre de la dimensión",
  "evaluacion_groq": {
    "fragmentos_validos": true,
    "puntuacion_justificada": true,
    "puntuacion_sugerida": null,
    "razonamiento": "explicación breve"
  },
  "evaluacion_github": {
    "fragmentos_validos": true,
    "puntuacion_justificada": true,
    "puntuacion_sugerida": null,
    "razonamiento": "explicación breve"
  },
  "puntuacion_final": 0,
  "hay_discrepancia": false
}

REGLA: puntuacion_sugerida es null si la puntuación está bien."""


class JudgeAgent:

    async def juzgar(
        self,
        letra: str,
        resultado_groq: dict,
        resultado_github: dict,
    ) -> dict:
        user_message = f"""LETRA ORIGINAL:
\"\"\"{letra}\"\"\"

DIMENSIÓN: {resultado_groq.get('dimension')}

EVALUACIÓN DE GROQ:
{json.dumps(resultado_groq, ensure_ascii=False, indent=2)}

EVALUACIÓN DE GITHUB MODELS:
{json.dumps(resultado_github, ensure_ascii=False, indent=2)}

Emite tu veredicto."""

        payload = {
            "model":   OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_JUEZ},
                {"role": "user",   "content": user_message},
            ],
            "stream":  False,
            "options": {"temperature": 0},
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(OLLAMA_URL, json=payload)
                response.raise_for_status()

            raw = response.json()["message"]["content"].strip()

            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                raw_clean = raw.replace("```json", "").replace("```", "").strip()
                return json.loads(raw_clean)

        except Exception as e:
            # Ollama no disponible → usar media como fallback
            p_groq   = resultado_groq.get("puntuacion", 0)
            p_github = resultado_github.get("puntuacion", 0)
            return {
                "dimension":     resultado_groq.get("dimension"),
                "evaluacion_groq":   {"fragmentos_validos": True, "puntuacion_justificada": True, "puntuacion_sugerida": None, "razonamiento": "Ollama no disponible"},
                "evaluacion_github": {"fragmentos_validos": True, "puntuacion_justificada": True, "puntuacion_sugerida": None, "razonamiento": "Ollama no disponible"},
                "puntuacion_final":  round((p_groq + p_github) / 2),
                "hay_discrepancia":  abs(p_groq - p_github) >= 2,
                "error":             str(e),
            }