# backend/app/agents/judge_agent.py
import os
import json
import httpx
from langfuse.decorators import observe, langfuse_context

JUEZ_URL   = "https://openrouter.ai/api/v1/chat/completions"
JUEZ_KEY   = os.getenv("OPEN_ROUTER_KEY")
JUEZ_MODEL = "x-ai/grok-4.20-multi-agent-beta"  # o "google/gemini-2.5-flash"

SYSTEM_PROMPT_JUEZ = """Eres un juez experto en análisis de sesgos de género 
en canciones en español.

Recibirás:
1. La letra original de una canción
2. Dos evaluaciones de la misma dimensión hechas por modelos distintos

Tu trabajo es:
- Comprobar que los fragmentos citados realmente aparecen en la letra
- Decidir si la puntuación del 0 al 3 está bien justificada
- Si no estás de acuerdo, sugerir la puntuación correcta

ESCALA: 0=no presente, 1=leve, 2=claro, 3=extremo

Devuelve ÚNICAMENTE este JSON válido, sin texto adicional ni markdown:
{
  "dimension": "nombre de la dimensión",
  "evaluacion_groq": {
    "fragmentos_validos": true,
    "puntuacion_justificada": true,
    "puntuacion_sugerida": null,
    "razonamiento": "explicación breve"
  },
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

    @observe(as_type="generation")
    async def juzgar(
        self,
        letra: str,
        resultado_groq: dict,
        resultado_openrouter: dict,
    ) -> dict:
        user_message = f"""LETRA ORIGINAL:
\"\"\"{letra}\"\"\"

DIMENSIÓN: {resultado_groq.get('dimension')}

EVALUACIÓN DE GROQ:
{json.dumps(resultado_groq, ensure_ascii=False, indent=2)}

EVALUACIÓN DE OPENROUTER:
{json.dumps(resultado_openrouter, ensure_ascii=False, indent=2)}

Emite tu veredicto."""

        messages_payload = [
            {"role": "system", "content": SYSTEM_PROMPT_JUEZ},
            {"role": "user",   "content": user_message},
        ]
        
        langfuse_context.update_current_observation(
            model=JUEZ_MODEL,
            input=messages_payload,
            metadata={"dimension": resultado_groq.get('dimension')}
        )

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
                        "messages": messages_payload,
                    }
                )
                response.raise_for_status()

            resp_json = response.json()
            raw = resp_json["choices"][0]["message"]["content"].strip()
            usage_data = resp_json.get("usage", {})
            usage = {
                "input": usage_data.get("prompt_tokens", 0),
                "output": usage_data.get("completion_tokens", 0)
            }

            try:
                veredicto = json.loads(raw)
            except json.JSONDecodeError:
                raw_clean = raw.replace("```json", "").replace("```", "").strip()
                veredicto = json.loads(raw_clean)
                
            langfuse_context.update_current_observation(
                usage_details=usage,
                output=veredicto
            )
            return veredicto

        except Exception as e:
            # Fallback: media de los dos modelos
            p_groq        = resultado_groq.get("puntuacion", 0)
            p_openrouter  = resultado_openrouter.get("puntuacion", 0)
            fallback_res  = {
                "dimension":          resultado_groq.get("dimension"),
                "evaluacion_groq":        {"fragmentos_validos": True, "puntuacion_justificada": True, "puntuacion_sugerida": None, "razonamiento": f"Juez no disponible: {str(e)}"},
                "evaluacion_openrouter":  {"fragmentos_validos": True, "puntuacion_justificada": True, "puntuacion_sugerida": None, "razonamiento": f"Juez no disponible: {str(e)}"},
                "puntuacion_final":   round((p_groq + p_openrouter) / 2),
                "hay_discrepancia":   abs(p_groq - p_openrouter) >= 2,
                "error":              str(e),
            }
            langfuse_context.update_current_observation(output=fallback_res, level="ERROR", status_message=str(e))
            return fallback_res