import json

from .base_agent import call_model_json


SYSTEM_PROMPT_CRITICO = """Eres un critico tecnico de analisis de sesgos de genero en letras.
Recibiras la letra y una evaluacion por dimension generada por otro modelo.

Tu tarea:
- Validar si la puntuacion (0 a 3) es coherente con los fragmentos y la justificacion.
- Ajustar la puntuacion si detectas sobreestimacion o subestimacion.
- Mantener evidencia estrictamente anclada al texto.

Devuelve solo JSON valido con este formato:
{
  "dimension": "nombre",
  "puntuacion_revisada": 0,
  "hay_ajuste": false,
  "justificacion_critica": "texto breve"
}
"""


class CriticAgent:
    async def revisar(self, letra: str, resultado_dimension: dict) -> dict:
        user_message = (
            "LETRA ORIGINAL:\n"
            f'"""{letra}"""\n\n'
            "DIMENSION:\n"
            f"{resultado_dimension.get('dimension')}\n\n"
            "EVALUACION INICIAL:\n"
            f"{json.dumps(resultado_dimension, ensure_ascii=False, indent=2)}\n\n"
            "Emite tu revision critica."
        )

        try:
            payload, provider_name, model_name = await call_model_json(
                system_prompt=SYSTEM_PROMPT_CRITICO,
                user_message=user_message,
                provider_order=None,
                temperature=0,
                max_tokens=800,
                context_label=f"critico:{resultado_dimension.get('dimension', 'N/A')}",
            )
            puntuacion_revisada = max(
                0, min(3, int(payload.get("puntuacion_revisada", 0)))
            )
            return {
                "dimension": resultado_dimension.get("dimension"),
                "puntuacion_revisada": puntuacion_revisada,
                "hay_ajuste": bool(payload.get("hay_ajuste", False)),
                "justificacion_critica": payload.get("justificacion_critica", ""),
                "proveedor_critico": provider_name,
                "modelo_critico": model_name,
            }
        except Exception as e:
            return {
                "dimension": resultado_dimension.get("dimension"),
                "puntuacion_revisada": max(
                    0, min(3, int(resultado_dimension.get("puntuacion", 0)))
                ),
                "hay_ajuste": False,
                "justificacion_critica": f"Critico no disponible: {e}",
                "error": str(e),
            }
