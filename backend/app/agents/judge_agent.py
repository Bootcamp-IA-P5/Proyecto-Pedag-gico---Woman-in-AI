# backend/app/agents/judge_agent.py
import os
import json
import httpx

# ── Configuración OpenRouter ─────────────────────────────
JUEZ_URL   = "https://openrouter.ai/api/v1/chat/completions"
JUEZ_KEY   = os.getenv("OPEN_ROUTER_KEY")
JUEZ_MODEL = "openrouter/hunter-alpha"  # modelo OpenRouter unificado

SYSTEM_PROMPT_JUEZ = """Eres un juez experto en análisis de sesgos de género 
en canciones en español.

Recibirás:
1. La letra original de una canción
2. Una evaluación de la misma dimensión hecha por un modelo

Tu trabajo es:
- Comprobar que los fragmentos citados realmente aparecen en la letra
- Decidir si la puntuación del 0 al 3 está bien justificada
- Si no estás de acuerdo, sugerir la puntuación correcta

ESCALA: 0=no presente, 1=leve, 2=claro, 3=extremo

Devuelve ÚNICAMENTE este JSON válido, sin texto adicional ni markdown:
{
  "dimension": "nombre de la dimensión",
  "evaluacion_openrouter": {
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

    async def juzgar(self, letra: str, resultado_openrouter: dict) -> dict:
        user_message = f"""LETRA ORIGINAL:
\"\"\"{letra}\"\"\"

DIMENSIÓN: {resultado_openrouter.get('dimension')}

EVALUACIÓN DEL MODELO:
{json.dumps(resultado_openrouter, ensure_ascii=False, indent=2)}

Emite tu veredicto."""

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    JUEZ_URL,
                    headers={
                        "Authorization": f"Bearer {JUEZ_KEY}",
                        "Content-Type":  "application/json",
                    },
                    json={
                        "model":       JUEZ_MODEL,
                        "temperature": 0,
                        "max_tokens":  1024,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT_JUEZ},
                            {"role": "user",   "content": user_message},
                        ],
                    }
                )
                response.raise_for_status()

            raw = response.json()["choices"][0]["message"]["content"].strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                raw_clean = raw.replace("```json", "").replace("```", "").strip()
                return json.loads(raw_clean)

        except Exception as e:
            # Fallback: usa directamente la puntuación del modelo
            p_openrouter = resultado_openrouter.get("puntuacion", 0)
            return {
                "dimension": resultado_openrouter.get("dimension"),
                "evaluacion_openrouter": {
                    "fragmentos_validos": True,
                    "puntuacion_justificada": True,
                    "puntuacion_sugerida": None,
                    "razonamiento": f"Juez no disponible: {str(e)}"
                },
                "puntuacion_final": p_openrouter,
                "hay_discrepancia": False,
                "error": str(e),
            }