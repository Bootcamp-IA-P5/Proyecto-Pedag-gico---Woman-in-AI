# backend/app/agents/reporter_agent.py
import asyncio
from .base_agent            import BaseAgent
from .jelous_agent          import CelosAgent
from .strong_language_agent import InsultosAgent
from .sumision_agent        import SumisionAgent
from .object_agent          import ObjetificacionAgent
from .judge_agent           import JudgeAgent


class ReporterAgent:

    def __init__(self):
        self.agentes: list[BaseAgent] = [
            CelosAgent(),
            InsultosAgent(),
            SumisionAgent(),
            ObjetificacionAgent(),
        ]
        self.juez = JudgeAgent()

    async def analizar(self, letra: str) -> dict:
        # PASO 1: 4 agentes × 2 modelos = 8 llamadas en paralelo
        tareas_groq   = [a.analizar(letra, proveedor="groq")   for a in self.agentes]
        tareas_openrouter = [a.analizar(letra, proveedor="openrouter") for a in self.agentes]

        resultados_groq, resultados_openrouter = await asyncio.gather(
            asyncio.gather(*tareas_groq,   return_exceptions=True),
            asyncio.gather(*tareas_openrouter, return_exceptions=True),
        )

        # PASO 2: juez revisa cada par
        dimensiones_finales = []
        errores = []

        for agente, res_groq, res_openrouter in zip(
            self.agentes, resultados_groq, resultados_openrouter
        ):
            if isinstance(res_groq, Exception):
                errores.append({"dimension": agente.dimension, "error": f"groq: {str(res_groq)}"})
                continue
            if isinstance(res_openrouter, Exception):
                errores.append({"dimension": agente.dimension, "error": f"openrouter: {str(res_openrouter)}"})
                continue

            try:
                veredicto = await self.juez.juzgar(letra, res_groq, res_openrouter)
            except Exception as e:
                errores.append({"dimension": agente.dimension, "error": f"juez: {str(e)}"})
                veredicto = {
                    "puntuacion_final":  round((res_groq["puntuacion"] + res_openrouter["puntuacion"]) / 2),
                    "hay_discrepancia":  abs(res_groq["puntuacion"] - res_openrouter["puntuacion"]) >= 2,
                }

            dimensiones_finales.append({
                "dimension":         agente.dimension,
                "puntuacion_groq":   res_groq["puntuacion"],
                "puntuacion_openrouter": res_openrouter["puntuacion"],
                "fragmentos_groq":   res_groq["fragmentos"],
                "fragmentos_openrouter": res_openrouter["fragmentos"],
                "puntuacion_final":  veredicto.get("puntuacion_final", 0),
                "hay_discrepancia":  veredicto.get("hay_discrepancia", False),
                "juez_groq":         veredicto.get("evaluacion_groq", {}),
                "juez_openrouter":   veredicto.get("evaluacion_openrouter", {}),
            })

        # PASO 3: consolidar
        puntuaciones = [d["puntuacion_final"] for d in dimensiones_finales]
        puntuacion_global = round(sum(puntuaciones) / len(puntuaciones), 1) if puntuaciones else 0.0

        return {
            "puntuacion_global":        puntuacion_global,
            "nivel_global":             self._nivel(puntuacion_global),
            "dimensiones":              [d for d in dimensiones_finales if d["puntuacion_final"] > 0],
            "sin_sesgo":                [d["dimension"] for d in dimensiones_finales if d["puntuacion_final"] == 0],
            "dimensiones_discrepantes": [d["dimension"] for d in dimensiones_finales if d["hay_discrepancia"]],
            "requiere_revision_humana": len([d for d in dimensiones_finales if d["hay_discrepancia"]]) > 1,
            "errores":                  errores if errores else None,
        }

    @staticmethod
    def _nivel(puntuacion: float) -> str:
        if puntuacion == 0:   return "Sin sesgo detectado"
        elif puntuacion < 1.5: return "Leve"
        elif puntuacion < 2.5: return "Moderado"
        else:                  return "Grave"