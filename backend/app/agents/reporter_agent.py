import asyncio
import os

from .base_agent import BaseAgent
from .critic_agent import CriticAgent
from .jelous_agent import CelosAgent
from .judge_agent import JudgeAgent
from .object_agent import ObjetificacionAgent
from .strong_language_agent import InsultosAgent
from .sumision_agent import SumisionAgent


class ReporterAgent:
    def __init__(self):
        self.pipeline_mode = os.getenv("ANALYSIS_PIPELINE_MODE", "simple").lower()
        self.min_coverage_for_conclusive = float(
            os.getenv("ANALYSIS_MIN_COVERAGE_FOR_CONCLUSIVE", "0.75")
        )
        self.timeout_per_dimension_seconds = int(
            os.getenv("ANALYSIS_TIMEOUT_PER_DIMENSION_SECONDS", "12")
        )
        self.timeout_per_juror_seconds = int(
            os.getenv("ANALYSIS_TIMEOUT_PER_JUROR_SECONDS", "20")
        )
        self.agentes: list[BaseAgent] = [
            CelosAgent(),
            InsultosAgent(),
            SumisionAgent(),
            ObjetificacionAgent(),
        ]
        self.critico = CriticAgent()
        self.juez = JudgeAgent()

    async def analizar(self, letra: str) -> dict:
        errores = []
        dimensiones_finales = []
        inconclusas: list[str] = []

        # Etapa 1: analisis por dimension (GitHub Models principal + fallback OpenRouter)
        for agente in self.agentes:
            dimension_nombre = agente.dimension
            resultado_dimension = None
            try:
                resultado_dimension = await asyncio.wait_for(
                    agente.analizar(letra),
                    timeout=self.timeout_per_dimension_seconds,
                )
            except Exception as e:
                errores.append(
                    {"dimension": agente.dimension, "error": f"dimension: {e}"}
                )
                resultado_dimension = {
                    "dimension": agente.dimension,
                    "puntuacion": 0,
                    "fragmentos": [],
                    "justificacion": "",
                    "proveedor": "fallback",
                    "modelo": "fallback",
                }

            stage1_fallback = (
                (resultado_dimension.get("proveedor") or "").lower() == "fallback"
            )
            if stage1_fallback:
                inconclusas.append(dimension_nombre)

            # Modo liviano para evitar 429: usa resultado de dimension como salida final.
            if self.pipeline_mode == "simple":
                dimensiones_finales.append(
                    {
                        "dimension": dimension_nombre,
                        "puntuacion_openrouter": resultado_dimension.get("puntuacion", 0),
                        "fragmentos_openrouter": resultado_dimension.get("fragmentos", []),
                        "puntuacion_final": resultado_dimension.get("puntuacion", 0),
                        "hay_discrepancia": False,
                        "juez_openrouter": {},
                        "justificacion_openrouter": resultado_dimension.get("justificacion", ""),
                        "proveedor_openrouter": resultado_dimension.get("proveedor", "desconocido"),
                        "modelo_openrouter": resultado_dimension.get("modelo", "desconocido"),
                        "revision_critica": None,
                        "confiable": not stage1_fallback,
                        "motivo_inconcluso": "stage1_fallback" if stage1_fallback else None,
                    }
                )
                continue

            if stage1_fallback:
                dimensiones_finales.append(
                    {
                        "dimension": dimension_nombre,
                        "puntuacion_openrouter": resultado_dimension.get("puntuacion", 0),
                        "fragmentos_openrouter": resultado_dimension.get("fragmentos", []),
                        "puntuacion_final": resultado_dimension.get("puntuacion", 0),
                        "hay_discrepancia": False,
                        "juez_openrouter": {},
                        "justificacion_openrouter": resultado_dimension.get("justificacion", ""),
                        "proveedor_openrouter": resultado_dimension.get("proveedor", "desconocido"),
                        "modelo_openrouter": resultado_dimension.get("modelo", "desconocido"),
                        "revision_critica": None,
                        "confiable": False,
                        "motivo_inconcluso": "stage1_fallback",
                    }
                )
                continue

            # Etapa 2: critico
            try:
                revision_critica = await asyncio.wait_for(
                    self.critico.revisar(letra, resultado_dimension),
                    timeout=self.timeout_per_juror_seconds,
                )
            except Exception as e:
                errores.append(
                    {"dimension": agente.dimension, "error": f"critico: {e}"}
                )
                inconclusas.append(dimension_nombre)
                dimensiones_finales.append(
                    {
                        "dimension": dimension_nombre,
                        "puntuacion_openrouter": resultado_dimension.get("puntuacion", 0),
                        "fragmentos_openrouter": resultado_dimension.get("fragmentos", []),
                        "puntuacion_final": resultado_dimension.get("puntuacion", 0),
                        "hay_discrepancia": False,
                        "juez_openrouter": {},
                        "justificacion_openrouter": resultado_dimension.get(
                            "justificacion", ""
                        ),
                        "proveedor_openrouter": resultado_dimension.get(
                            "proveedor", "desconocido"
                        ),
                        "modelo_openrouter": resultado_dimension.get(
                            "modelo", "desconocido"
                        ),
                        "revision_critica": None,
                        "confiable": False,
                        "motivo_inconcluso": "stage2_critic_error",
                    }
                )
                continue

            # Etapa 3: juez final
            try:
                veredicto = await asyncio.wait_for(
                    self.juez.juzgar(letra, resultado_dimension, revision_critica),
                    timeout=self.timeout_per_juror_seconds,
                )
            except Exception as e:
                errores.append({"dimension": agente.dimension, "error": f"juez: {e}"})
                inconclusas.append(dimension_nombre)
                dimensiones_finales.append(
                    {
                        "dimension": dimension_nombre,
                        "puntuacion_openrouter": revision_critica.get(
                            "puntuacion_revisada", resultado_dimension.get("puntuacion", 0)
                        ),
                        "fragmentos_openrouter": resultado_dimension.get("fragmentos", []),
                        "puntuacion_final": revision_critica.get(
                            "puntuacion_revisada", resultado_dimension.get("puntuacion", 0)
                        ),
                        "hay_discrepancia": False,
                        "juez_openrouter": {},
                        "justificacion_openrouter": resultado_dimension.get(
                            "justificacion", ""
                        ),
                        "proveedor_openrouter": resultado_dimension.get(
                            "proveedor", "desconocido"
                        ),
                        "modelo_openrouter": resultado_dimension.get(
                            "modelo", "desconocido"
                        ),
                        "revision_critica": revision_critica,
                        "confiable": False,
                        "motivo_inconcluso": "stage2_judge_error",
                    }
                )
                continue

            dimensiones_finales.append(
                {
                    "dimension": agente.dimension,
                    "puntuacion_openrouter": revision_critica.get(
                        "puntuacion_revisada", resultado_dimension.get("puntuacion", 0)
                    ),
                    "fragmentos_openrouter": resultado_dimension.get("fragmentos", []),
                    "puntuacion_final": veredicto.get("puntuacion_final", 0),
                    "hay_discrepancia": veredicto.get("hay_discrepancia", False),
                    "juez_openrouter": veredicto.get("evaluacion_openrouter", {}),
                    "justificacion_openrouter": resultado_dimension.get(
                        "justificacion", ""
                    ),
                    "proveedor_openrouter": resultado_dimension.get(
                        "proveedor", "desconocido"
                    ),
                    "modelo_openrouter": resultado_dimension.get(
                        "modelo", "desconocido"
                    ),
                    "revision_critica": revision_critica,
                    "confiable": True,
                    "motivo_inconcluso": None,
                }
            )

        puntuaciones = [d["puntuacion_final"] for d in dimensiones_finales]
        puntuacion_preliminar = (
            round(sum(puntuaciones) / len(puntuaciones), 1) if puntuaciones else 0.0
        )
        confiables = [d for d in dimensiones_finales if d.get("confiable", False)]
        cobertura = (
            round(len(confiables) / len(dimensiones_finales), 2)
            if dimensiones_finales
            else 0.0
        )
        es_conclusivo = cobertura >= self.min_coverage_for_conclusive
        puntuacion_global = puntuacion_preliminar if es_conclusivo else None
        nivel_global = (
            self._nivel(puntuacion_preliminar)
            if es_conclusivo
            else "Inconcluso (cobertura insuficiente)"
        )
        dimensiones_discrepantes = [
            d["dimension"] for d in dimensiones_finales if d["hay_discrepancia"]
        ]

        return {
            "puntuacion_global": puntuacion_global,
            "puntuacion_global_preliminar": puntuacion_preliminar,
            "nivel_global": nivel_global,
            "dimensiones": [
                d
                for d in dimensiones_finales
                if d.get("confiable", False) and d["puntuacion_final"] > 0
            ],
            "sin_sesgo": [
                d["dimension"]
                for d in confiables
                if d["puntuacion_final"] == 0
            ],
            "dimensiones_inconclusas": sorted(set(inconclusas)) or None,
            "cobertura_dimensiones": cobertura,
            "dimensiones_discrepantes": dimensiones_discrepantes,
            "requiere_revision_humana": (
                len(dimensiones_discrepantes) > 1
                or not es_conclusivo
                or bool(errores)
            ),
            "errores": errores if errores else None,
            "modelo_principal": "github/openrouter-fallback",
            "pipeline_mode": self.pipeline_mode,
        }

    @staticmethod
    def _nivel(puntuacion: float) -> str:
        if puntuacion == 0:
            return "Sin sesgo detectado"
        if puntuacion < 1.5:
            return "Leve"
        if puntuacion < 2.5:
            return "Moderado"
        return "Grave"
