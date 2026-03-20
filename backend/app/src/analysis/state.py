# La "mochila" que viaja por el grafo.
# Empieza con la letra y va acumulando resultados.
from typing_extensions import TypedDict
from typing import Optional


class AnalysisState(TypedDict):
    # ── Lo que entra ───────────────────────────────
    song_id:        str
    titulo:         str
    artista:        str
    genero_musical: str
    letra:          str

    # ── Lo que produce el nodo de análisis ─────────
    dimensiones:               Optional[list[dict]]
    puntuacion_global:         Optional[float]
    puntuacion_global_preliminar: Optional[float]
    nivel_global:              Optional[str]
    sin_sesgo:                 Optional[list[str]]
    dimensiones_inconclusas:   Optional[list[str]]
    cobertura_dimensiones:     Optional[float]
    dimensiones_discrepantes:  Optional[list[str]]
    requiere_revision_humana:  Optional[bool]
    errores:                   Optional[list[dict]]

    # ── El resultado final ─────────────────────────
    resultado_final:           Optional[dict]