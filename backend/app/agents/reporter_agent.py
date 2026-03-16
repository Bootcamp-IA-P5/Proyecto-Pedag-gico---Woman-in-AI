# backend/app/agents/reporter_agent.py
from .base_agent            import BaseAgent
from .jelous_agent          import CelosAgent
from .strong_language_agent import InsultosAgent
from .sumision_agent        import SumisionAgent
from .object_agent          import ObjetificacionAgent
from .judge_agent           import JudgeAgent


class ReporterAgent:

    def __init__(self):
        # Todos los agentes usan OpenRouter
        self.agentes: list[BaseAgent] = [
            CelosAgent(),
            InsultosAgent(),
            SumisionAgent(),
            ObjetificacionAgent(),
        ]
        self.juez = JudgeAgent()

    async def analizar(self, letra: str) -> dict:
        resultados = []
        errores = []

        # ── Ejecutar cada agente secuencialmente ────────────────
        for agente in self.agentes:
            try:
                res = await agente.analizar(letra, proveedor="openrouter")
                resultados.append(res)
            except Exception as e:
                errores.append({"dimension": agente.dimension, "error": f"openrouter: {str(e)}"})
                resultados.append({"puntuacion": 0, "fragmentos": []})

        # ── Paso 2: juez revisa cada resultado ──────────────────
        dimensiones_finales = []
        for agente, res in zip(self.agentes, resultados):
            try:
                veredicto = await self.juez.juzgar(letra, res, res)
            except Exception as e:
                errores.append({"dimension": agente.dimension, "error": f"juez: {str(e)}"})
                veredicto = {
                    "puntuacion_final": res.get("puntuacion", 0),
                    "hay_discrepancia": False,
                }

            dimensiones_finales.append({
                "dimension":             agente.dimension,
                "puntuacion_openrouter": res.get("puntuacion", 0),
                "fragmentos_openrouter": res.get("fragmentos", []),
                "puntuacion_final":      veredicto.get("puntuacion_final", 0),
                "hay_discrepancia":      veredicto.get("hay_discrepancia", False),
                "juez_openrouter":       veredicto.get("evaluacion_openrouter", {}),
            })

        # ── Paso 3: consolidar ─────────────────────────────────
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
        if puntuacion == 0:      return "Sin sesgo detectado"
        elif puntuacion < 1.5:   return "Leve"
        elif puntuacion < 2.5:   return "Moderado"
        else:                     return "Grave"