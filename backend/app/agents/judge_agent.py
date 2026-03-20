# backend/app/agents/judge_agent.py
import json
from langfuse.decorators import observe, langfuse_context
from app.agents.base_agent import call_model_json

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

    @observe(as_type="generation")
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

        messages_payload = [
            {"role": "system", "content": SYSTEM_PROMPT_JUEZ},
            {"role": "user",   "content": user_message},
        ]
        
        langfuse_context.update_current_observation(
            input=messages_payload,
            metadata={"dimension": resultado_modelo.get('dimension')}
        )

        try:
            # Usando la máquina principal de forma resiliente
            veredicto, prov_usado, modelo_usado = await call_model_json(
                system_prompt=SYSTEM_PROMPT_JUEZ,
                user_message=user_message,
                provider_order=["openrouter"],
                temperature=0.0,
                context_label="Juez Final",
            )
            
            langfuse_context.update_current_observation(
                model=modelo_usado,
                output=veredicto
            )
            return veredicto

        except Exception as e:
            # Fallback en caso de que el Juez falle: usamos la puntuacion revisada (o la original si no hay revisada)
            p_revisada = revision_critica.get("puntuacion_revisada", resultado_modelo.get("puntuacion", 0))
            fallback_res  = {
                "dimension":          resultado_modelo.get("dimension"),
                "evaluacion_openrouter":  {
                    "fragmentos_validos": True, 
                    "puntuacion_justificada": True, 
                    "puntuacion_sugerida": None, 
                    "razonamiento": f"Juez no disponible: {str(e)}"
                },                                                                           
                "puntuacion_final":   p_revisada,
                "hay_discrepancia":   False,
                "error":              str(e),
            }
            langfuse_context.update_current_observation(output=fallback_res, level="ERROR", status_message=str(e))
            return fallback_res