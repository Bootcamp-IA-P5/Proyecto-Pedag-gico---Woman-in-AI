# backend/app/agents/judge_agent.py
import json
from .base_agent import call_model_json

SYSTEM_PROMPT_JUEZ = """Eres un juez experto en análisis de sesgos de género 
en canciones en español.

Recibirás:
1. La letra original de una canción
2. Una evaluación inicial por dimensión
3. Una revisión crítica de esa evaluación

Tu trabajo es:
- Comprobar que los fragmentos citados realmente aparecen en la letra
- Validar si la revisión crítica tiene sentido
- Entregar una puntuación final robusta del 0 al 3

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
    async def juzgar(
        self, letra: str, resultado_modelo: dict, revision_critica: dict
    ) -> dict:
        user_message = f"""LETRA ORIGINAL:
\"\"\"{letra}\"\"\"

DIMENSIÓN: {resultado_modelo.get("dimension")}

EVALUACIÓN INICIAL DEL MODELO:
{json.dumps(resultado_modelo, ensure_ascii=False, indent=2)}

REVISION CRITICA:
{json.dumps(revision_critica, ensure_ascii=False, indent=2)}

Emite tu veredicto."""

        try:
            payload, provider_name, model_name = await call_model_json(
                system_prompt=SYSTEM_PROMPT_JUEZ,
                user_message=user_message,
                provider_order=None,
                temperature=0,
                max_tokens=900,
                context_label=f"juez:{resultado_modelo.get('dimension', 'N/A')}",
            )
            payload["proveedor_juez"] = provider_name
            payload["modelo_juez"] = model_name
            return payload

        except Exception as e:
            p_critica = revision_critica.get(
                "puntuacion_revisada", resultado_modelo.get("puntuacion", 0)
            )
            return {
                "dimension": resultado_modelo.get("dimension"),
                "evaluacion_openrouter": {
                    "fragmentos_validos": True,
                    "puntuacion_justificada": True,
                    "puntuacion_sugerida": None,
                    "razonamiento": f"Juez no disponible: {str(e)}",
                },
                "puntuacion_final": p_critica,
                "hay_discrepancia": False,
                "error": str(e),
            }
