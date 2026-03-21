import asyncio
import logging
import os

from .base_agent import BaseAgent
from .critic_agent import CriticAgent
from .guardian_agent import GuardianAgent
from .jelous_agent import CelosAgent
from .judge_agent import JudgeAgent
from .object_agent import ObjetificacionAgent
from .strong_language_agent import InsultosAgent
from .sumision_agent import SumisionAgent

log = logging.getLogger(__name__)

MENSAJES_ERROR = {
    "es_letra_cancion": "El texto introducido no parece una letra de canción. Vértice solo analiza letras de canciones.",
    "es_español": "El texto no está en español. Vértice solo analiza letras de canciones en español.",
    "es_biografia": "El texto parece una biografía. Vértice solo analiza letras de canciones.",
    "contiene_insultos_sistema": "El texto contiene contenido inapropiado dirigido al sistema.",
    "es_spam": "El texto parece spam o contenido sin sentido.",
    "es_codigo": "El texto parece código de programación. Vértice solo analiza letras de canciones.",
    "contiene_datos_personales": "El texto contiene datos personales. Por seguridad no podemos procesarlo.",
    "es_prompt_injection": "El texto contiene instrucciones no permitidas. Solo se aceptan letras de canciones.",
}


def _build_recommended_timeout_seconds() -> int:
    """Estimate a safe timeout for one dimension considering retries and provider fallback."""
    try:
        llm_timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "25"))
    except ValueError:
        llm_timeout = 25.0

    try:
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
    except ValueError:
        max_retries = 3

    try:
        retry_base = float(os.getenv("LLM_RETRY_BASE", "2.0"))
    except ValueError:
        retry_base = 2.0

    max_retries = max(1, max_retries)
    provider_order = [
        p.strip()
        for p in os.getenv(
            "LLM_PROVIDER_ORDER",
            "groq,gemini,mistral,github,openrouter,together,compat",
        ).split(",")
        if p.strip()
    ]
    provider_count = max(1, len(provider_order))

    backoff_total = sum(retry_base**i for i in range(1, max_retries))
    single_provider_budget = (llm_timeout * max_retries) + backoff_total
    full_fallback_budget = (single_provider_budget * provider_count) + 5

    return int(max(30, min(300, full_fallback_budget)))


class ReporterAgent:
    def __init__(self):
        self.guardian = GuardianAgent()
        self.guardian_strict = (
            os.getenv("ANALYSIS_GUARDIAN_STRICT", "false").lower() == "true"
        )
        self.pipeline_mode = os.getenv("ANALYSIS_PIPELINE_MODE", "simple").lower()
        self.min_coverage_for_conclusive = float(
            os.getenv("ANALYSIS_MIN_COVERAGE_FOR_CONCLUSIVE", "0.75")
        )

        recommended_timeout = _build_recommended_timeout_seconds()
        self.timeout_per_dimension_seconds = int(
            os.getenv(
                "ANALYSIS_TIMEOUT_PER_DIMENSION_SECONDS",
                str(recommended_timeout),
            )
        )
        self.timeout_per_juror_seconds = int(
            os.getenv(
                "ANALYSIS_TIMEOUT_PER_JUROR_SECONDS",
                str(recommended_timeout),
            )
        )

        self.agentes: list[BaseAgent] = [
            CelosAgent(),
            InsultosAgent(),
            SumisionAgent(),
            ObjetificacionAgent(),
        ]
        self.critico = CriticAgent()
        self.juez = JudgeAgent()

        log.info(
            "ReporterAgent config | mode=%s | guardian_strict=%s | timeout_dim=%ss | timeout_juror=%ss | min_coverage=%.2f",
            self.pipeline_mode,
            self.guardian_strict,
            self.timeout_per_dimension_seconds,
            self.timeout_per_juror_seconds,
            self.min_coverage_for_conclusive,
        )

    async def analizar(self, letra: str) -> dict:
        validacion = await self.guardian.validar(letra)
        if not validacion.get("valido", False) and self.guardian_strict:
            return self._respuesta_invalida(validacion)

        errores = []
        dimensiones_finales = []
        inconclusas: list[str] = []

        if not validacion.get("valido", False):
            motivo = self._resolver_motivo_invalidacion(validacion)
            errores.append(
                {
                    "dimension": "Guardian",
                    "error": f"guardrails_soft_fail: {motivo}",
                }
            )

        for agente in self.agentes:
            dimension_nombre = agente.dimension
            resultado_dimension = None
            try:
                resultado_dimension = await asyncio.wait_for(
                    agente.analizar(letra),
                    timeout=self.timeout_per_dimension_seconds,
                )
            except Exception as e:
                err_msg = str(e).strip() or e.__class__.__name__
                errores.append(
                    {"dimension": agente.dimension, "error": f"dimension: {err_msg}"}
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
                resultado_dimension.get("proveedor") or ""
            ).lower() == "fallback"
            if stage1_fallback:
                inconclusas.append(dimension_nombre)

            if self.pipeline_mode == "simple":
                dimensiones_finales.append(
                    {
                        "dimension": dimension_nombre,
                        "puntuacion_openrouter": resultado_dimension.get(
                            "puntuacion", 0
                        ),
                        "fragmentos_openrouter": resultado_dimension.get(
                            "fragmentos", []
                        ),
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
                        "confiable": not stage1_fallback,
                        "motivo_inconcluso": "stage1_fallback"
                        if stage1_fallback
                        else None,
                    }
                )
                continue

            if stage1_fallback:
                dimensiones_finales.append(
                    {
                        "dimension": dimension_nombre,
                        "puntuacion_openrouter": resultado_dimension.get(
                            "puntuacion", 0
                        ),
                        "fragmentos_openrouter": resultado_dimension.get(
                            "fragmentos", []
                        ),
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
                        "motivo_inconcluso": "stage1_fallback",
                    }
                )
                continue

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
                        "puntuacion_openrouter": resultado_dimension.get(
                            "puntuacion", 0
                        ),
                        "fragmentos_openrouter": resultado_dimension.get(
                            "fragmentos", []
                        ),
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
                            "puntuacion_revisada",
                            resultado_dimension.get("puntuacion", 0),
                        ),
                        "fragmentos_openrouter": resultado_dimension.get(
                            "fragmentos", []
                        ),
                        "puntuacion_final": revision_critica.get(
                            "puntuacion_revisada",
                            resultado_dimension.get("puntuacion", 0),
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
            "valido": True,
            "motivo": None,
            "puntuacion_global": puntuacion_global,
            "puntuacion_global_preliminar": puntuacion_preliminar,
            "nivel_global": nivel_global,
            "dimensiones": [
                d
                for d in dimensiones_finales
                if d.get("confiable", False) and d["puntuacion_final"] > 0
            ],
            "sin_sesgo": [
                d["dimension"] for d in confiables if d["puntuacion_final"] == 0
            ],
            "dimensiones_inconclusas": sorted(set(inconclusas)) or None,
            "cobertura_dimensiones": cobertura,
            "dimensiones_discrepantes": dimensiones_discrepantes,
            "requiere_revision_humana": (
                len(dimensiones_discrepantes) > 1 or not es_conclusivo or bool(errores)
            ),
            "errores": errores if errores else None,
            "modelo_principal": "github/openrouter-fallback",
            "pipeline_mode": self.pipeline_mode,
        }

    @staticmethod
    def _respuesta_invalida(validacion: dict) -> dict:
        motivo = ReporterAgent._resolver_motivo_invalidacion(validacion)

        if not motivo:
            for campo, mensaje in MENSAJES_ERROR.items():
                if campo in [
                    "es_biografia",
                    "contiene_insultos_sistema",
                    "es_spam",
                    "es_codigo",
                    "contiene_datos_personales",
                    "es_prompt_injection",
                ]:
                    if validacion.get(campo):
                        motivo = mensaje
                        break
                elif campo in ["es_letra_cancion", "es_español"]:
                    if validacion.get(campo) is False:
                        motivo = mensaje
                        break

        if not motivo:
            motivo = "El texto no cumple los requisitos para ser analizado."

        return {
            "valido": False,
            "motivo": motivo,
            "puntuacion_global": None,
            "puntuacion_global_preliminar": 0.0,
            "nivel_global": "Error",
            "dimensiones": [],
            "sin_sesgo": [],
            "dimensiones_inconclusas": None,
            "cobertura_dimensiones": 0.0,
            "dimensiones_discrepantes": [],
            "requiere_revision_humana": False,
            "errores": None,
        }

    @staticmethod
    def _resolver_motivo_invalidacion(validacion: dict) -> str:
        motivo = validacion.get("motivo") or ""

        if not motivo:
            for campo, mensaje in MENSAJES_ERROR.items():
                if campo in [
                    "es_biografia",
                    "contiene_insultos_sistema",
                    "es_spam",
                    "es_codigo",
                    "contiene_datos_personales",
                    "es_prompt_injection",
                ]:
                    if validacion.get(campo):
                        motivo = mensaje
                        break
                elif campo in ["es_letra_cancion", "es_español"]:
                    if validacion.get(campo) is False:
                        motivo = mensaje
                        break

        if not motivo:
            motivo = "El texto no cumple los requisitos para ser analizado."
        return motivo

    @staticmethod
    def _nivel(puntuacion: float) -> str:
        if puntuacion == 0:
            return "Sin sesgo detectado"
        if puntuacion < 1.5:
            return "Leve"
        if puntuacion < 2.5:
            return "Moderado"
        return "Grave"
