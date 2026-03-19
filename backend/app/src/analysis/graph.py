# backend/app/src/analysis/graph.py
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langfuse.decorators import observe
from app.src.analysis.state import AnalysisState
from app.agents.reporter_agent import ReporterAgent

load_dotenv()

reporter = ReporterAgent()


@observe(as_type="span")
async def nodo_analizar(state: AnalysisState) -> dict:
    try:
        letra = state.get("letra", "")
        if not letra:
            return {
                "dimensiones":              [],
                "puntuacion_global":        0.0,
                "nivel_global":             "Error",
                "sin_sesgo":                [],
                "dimensiones_discrepantes": [],
                "requiere_revision_humana": False,
                "errores":                  [{"error": "No se proporcionó letra"}],
            }
        
        resultado = await reporter.analizar(letra)
        return {
            "dimensiones":              resultado.get("dimensiones", []),
            "puntuacion_global":        resultado.get("puntuacion_global", 0.0),
            "nivel_global":             resultado.get("nivel_global", ""),
            "sin_sesgo":                resultado.get("sin_sesgo", []),
            "dimensiones_discrepantes": resultado.get("dimensiones_discrepantes", []),
            "requiere_revision_humana": resultado.get("requiere_revision_humana", False),
            "errores":                  resultado.get("errores"),
        }
    except Exception as e:
        return {
            "dimensiones":              [],
            "puntuacion_global":        0.0,
            "nivel_global":             "Error",
            "sin_sesgo":                [],
            "dimensiones_discrepantes": [],
            "requiere_revision_humana": False,
            "errores":                  [{"error": str(e)}],
        }

@observe(as_type="span")
async def nodo_consolidar(state: AnalysisState) -> dict:
    return {
        "resultado_final": {
            "song_id":                   state.get("song_id", "manual"),
            "titulo":                    state.get("titulo", ""),
            "artista":                   state.get("artista", ""),
            "genero_musical":            state.get("genero_musical", ""),
            "puntuacion_global":         state.get("puntuacion_global", 0.0),
            "nivel_global":              state.get("nivel_global", ""),
            "dimensiones":               state.get("dimensiones", []),
            "sin_sesgo":                 state.get("sin_sesgo", []),
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
        "nivel_global":             None,
        "sin_sesgo":                None,
        "dimensiones_discrepantes": None,
        "requiere_revision_humana": None,
        "errores":                  None,
        "resultado_final":          None,
    }
    estado_final = await grafo_vertice.ainvoke(estado_inicial)
    return estado_final["resultado_final"]