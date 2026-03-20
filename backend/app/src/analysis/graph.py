# backend/app/src/analysis/graph.py
import os
import re

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from app.src.analysis.state import AnalysisState
from app.agents.reporter_agent import ReporterAgent

load_dotenv()

reporter = ReporterAgent()
MAX_LYRIC_CHARS = int(os.getenv("ANALYSIS_MAX_LYRIC_CHARS", "12000"))
ENABLE_LYRIC_SANITIZATION = os.getenv("ANALYSIS_SANITIZE_LYRICS", "false").lower() == "true"

SENSITIVE_TERMS = [
    r"\bputa\b",
    r"\bputo\b",
    r"\bzorra\b",
    r"\bperra\b",
    r"\bloca\b",
    r"\bsexo\b",
    r"\bcoger\b",
    r"\bfollar\b",
    r"\bviolar\b",
    r"\bmatar\b",
    r"\bdisparar\b",
]


def _truncate_lyric(text: str) -> str:
    if len(text) <= MAX_LYRIC_CHARS:
        return text
    head = MAX_LYRIC_CHARS // 2
    tail = MAX_LYRIC_CHARS - head
    return text[:head] + "\n... [letra truncada para analisis] ...\n" + text[-tail:]


def _sanitize_lyric(text: str) -> str:
    if not ENABLE_LYRIC_SANITIZATION:
        return text
    sanitized = text
    for pattern in SENSITIVE_TERMS:
        sanitized = re.sub(pattern, "[censurado]", sanitized, flags=re.IGNORECASE)
    return sanitized


async def nodo_analizar(state: AnalysisState) -> dict:
    try:
        letra = state.get("letra", "")
        if not letra:
            return {
                "dimensiones":              [],
                "puntuacion_global":        None,
                "puntuacion_global_preliminar": 0.0,
                "nivel_global":             "Error",
                "sin_sesgo":                [],
                "dimensiones_inconclusas":  None,
                "cobertura_dimensiones":    0.0,
                "dimensiones_discrepantes": [],
                "requiere_revision_humana": False,
                "errores":                  [{"error": "No se proporcionó letra"}],
            }
        
        payload = _sanitize_lyric(_truncate_lyric(letra))
        resultado = await reporter.analizar(payload)
        return {
            "dimensiones":              resultado.get("dimensiones", []),
            "puntuacion_global":        resultado.get("puntuacion_global"),
            "puntuacion_global_preliminar": resultado.get("puntuacion_global_preliminar", 0.0),
            "nivel_global":             resultado.get("nivel_global", ""),
            "sin_sesgo":                resultado.get("sin_sesgo", []),
            "dimensiones_inconclusas":  resultado.get("dimensiones_inconclusas"),
            "cobertura_dimensiones":    resultado.get("cobertura_dimensiones"),
            "dimensiones_discrepantes": resultado.get("dimensiones_discrepantes", []),
            "requiere_revision_humana": resultado.get("requiere_revision_humana", False),
            "errores":                  resultado.get("errores"),
        }
    except Exception as e:
        return {
            "dimensiones":              [],
            "puntuacion_global":        None,
            "puntuacion_global_preliminar": 0.0,
            "nivel_global":             "Error",
            "sin_sesgo":                [],
            "dimensiones_inconclusas":  None,
            "cobertura_dimensiones":    0.0,
            "dimensiones_discrepantes": [],
            "requiere_revision_humana": False,
            "errores":                  [{"error": str(e)}],
        }
async def nodo_consolidar(state: AnalysisState) -> dict:
    return {
        "resultado_final": {
            "song_id":                   state.get("song_id", "manual"),
            "titulo":                    state.get("titulo", ""),
            "artista":                   state.get("artista", ""),
            "genero_musical":            state.get("genero_musical", ""),
            "puntuacion_global":         state.get("puntuacion_global"),
            "puntuacion_global_preliminar": state.get("puntuacion_global_preliminar", 0.0),
            "nivel_global":              state.get("nivel_global", ""),
            "dimensiones":               state.get("dimensiones", []),
            "sin_sesgo":                 state.get("sin_sesgo", []),
            "dimensiones_inconclusas":   state.get("dimensiones_inconclusas"),
            "cobertura_dimensiones":     state.get("cobertura_dimensiones"),
            "dimensiones_discrepantes":  state.get("dimensiones_discrepantes", []),
            "requiere_revision_humana":  state.get("requiere_revision_humana", False),
            "prompt_version":            "v1.0",
            "errores":                   state.get("errores"),
        }
    }


def construir_grafo() -> StateGraph:
    grafo = StateGraph(AnalysisState)
    grafo.add_node("analizar",   nodo_analizar)
    grafo.add_node("consolidar", nodo_consolidar)
    grafo.set_entry_point("analizar")
    grafo.add_edge("analizar",   "consolidar")
    grafo.add_edge("consolidar", END)
    return grafo.compile()


grafo_vertice = construir_grafo()


async def analizar_cancion(
    song_id:        str,
    titulo:         str,
    artista:        str,
    genero_musical: str,
    letra:          str,
) -> dict:
    estado_inicial: AnalysisState = {
        "song_id":                  song_id,
        "titulo":                   titulo,
        "artista":                  artista,
        "genero_musical":           genero_musical,
        "letra":                    letra,
        "dimensiones":              None,
        "puntuacion_global":        None,
        "puntuacion_global_preliminar": None,
        "nivel_global":             None,
        "sin_sesgo":                None,
        "dimensiones_inconclusas":  None,
        "cobertura_dimensiones":    None,
        "dimensiones_discrepantes": None,
        "requiere_revision_humana": None,
        "errores":                  None,
        "resultado_final":          None,
    }
    estado_final = await grafo_vertice.ainvoke(estado_inicial)
    return estado_final["resultado_final"]