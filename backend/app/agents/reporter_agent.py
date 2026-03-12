"""
Agente: Reporter
Recibe los resultados de los 4 agentes de dimensión,
los consolida y devuelve la respuesta final estructurada al usuario.
"""

import asyncio
from .base_agent       import BaseAgent
from .celos_agent      import CelosAgent
from .insultos_agent   import InsultosAgent
from .sumision_agent   import SumisionAgent
from .object_agent import ObjetificacionAgent


class ReporterAgent:

    def __init__(self):
        self.agentes = [
            CelosAgent(),
            InsultosAgent(),
            SumisionAgent(),
            ObjetificacionAgent(),
        ]

    async def analizar(self, letra: str) -> dict:
        """
        Lanza los 4 agentes en paralelo con asyncio.gather
        y consolida los resultados en la respuesta final.
        """

        # ── Ejecución paralela de todos los agentes ────────
        resultados = await asyncio.gather(
            *[agente.analizar(letra) for agente in self.agentes],
            return_exceptions=True
        )

        # ── Procesamos resultados y capturamos errores ─────
        dimensiones = []
        errores     = []

        for agente, resultado in zip(self.agentes, resultados):
            if isinstance(resultado, Exception):
                errores.append({
                    "dimension": agente.dimension,
                    "error":     str(resultado)
                })
            else:
                dimensiones.append(resultado)

        # ── Puntuación global (media de dimensiones > 0) ───
        puntuaciones = [d["puntuacion"] for d in dimensiones]
        puntuacion_global = (
            round(sum(puntuaciones) / len(puntuaciones), 1)
            if puntuaciones else 0.0
        )

        # ── Dimensiones detectadas (puntuacion > 0) ────────
        detectadas = [d for d in dimensiones if d["puntuacion"] > 0]
        no_detectadas = [
            d["dimension"] for d in dimensiones if d["puntuacion"] == 0
        ]

        return {
            "puntuacion_global": puntuacion_global,
            "nivel_global":      self._nivel(puntuacion_global),
            "dimensiones":       detectadas,
            "sin_sesgo":         no_detectadas,
            "errores":           errores if errores else None,
        }

    @staticmethod
    def _nivel(puntuacion: float) -> str:
        if puntuacion == 0:
            return "Sin sesgo detectado"
        elif puntuacion < 1.5:
            return "Leve"
        elif puntuacion < 2.5:
            return "Moderado"
        else:
            return "Grave"