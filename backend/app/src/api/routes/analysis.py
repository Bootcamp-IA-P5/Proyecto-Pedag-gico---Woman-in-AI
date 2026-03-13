# backend/app/src/api/routes/analysis.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.src.analysis.graph import analizar_cancion
from app.src.config.supabase_client import supabase

router = APIRouter(prefix="/analysis", tags=["Análisis de sesgos"])


# ── Función auxiliar para guardar en Supabase ─────────────────────────────────

def guardar_en_supabase(song_id: int, lyrics_id: int, resultado: dict):
    """
    Guarda el resultado del análisis en las tablas existentes.
    No crea tablas nuevas.
    """
    dimensiones = {d["dimension"]: d for d in resultado.get("dimensiones", [])}

    def get_score(nombre_dimension: str, modelo: str) -> int:
        """Busca la puntuación de una dimensión y modelo concreto."""
        dim = dimensiones.get(nombre_dimension, {})
        if modelo == "groq":
            return dim.get("puntuacion_groq", 0)
        return dim.get("puntuacion_github", 0)

    def get_fragmentos(nombre_dimension: str, modelo: str) -> str:
        """Devuelve los fragmentos como texto."""
        dim = dimensiones.get(nombre_dimension, {})
        key = "fragmentos_groq" if modelo == "groq" else "fragmentos_github"
        fragmentos = dim.get(key, [])
        return " | ".join(fragmentos) if fragmentos else None

    # ── Guardar evaluación de Groq ────────────────────────────────────────────
    eval_groq = supabase.table("llm_evaluations").insert({
        "song_id":               song_id,
        "lyrics_id":             lyrics_id,
        "model_name":            "groq/llama-3.3-70b-versatile",
        "prompt_version":        resultado.get("prompt_version", "v1.0"),
        "temperature":           0.1,
        "score_objectification": get_score("Objetificación Sexual", "groq"),
        "score_agency":          get_score("Agencia y Autonomía", "groq"),
        "score_roles":           get_score("Sumisión / Roles de Género", "groq"),
        "score_possession":      get_score("Celos / Control", "groq"),
        "score_degrading":       get_score("Insultos / Lenguaje Degradante", "groq"),
        "score_inclusive_lang":  0,   # no tenemos este agente aún
        "score_relational":      0,   # no tenemos este agente aún
        "evidence_objectification": get_fragmentos("Objetificación Sexual", "groq"),
        "evidence_agency":          get_fragmentos("Agencia y Autonomía", "groq"),
        "evidence_roles":           get_fragmentos("Sumisión / Roles de Género", "groq"),
        "evidence_possession":      get_fragmentos("Celos / Control", "groq"),
        "evidence_degrading":       get_fragmentos("Insultos / Lenguaje Degradante", "groq"),
        "llm_raw_response":      resultado,
    }).execute()

    # ── Guardar evaluación de GitHub ──────────────────────────────────────────
    eval_github = supabase.table("llm_evaluations").insert({
        "song_id":               song_id,
        "lyrics_id":             lyrics_id,
        "model_name":            "github/gpt-4o-mini",
        "prompt_version":        resultado.get("prompt_version", "v1.0"),
        "temperature":           0.1,
        "score_objectification": get_score("Objetificación Sexual", "github"),
        "score_agency":          get_score("Agencia y Autonomía", "github"),
        "score_roles":           get_score("Sumisión / Roles de Género", "github"),
        "score_possession":      get_score("Celos / Control", "github"),
        "score_degrading":       get_score("Insultos / Lenguaje Degradante", "github"),
        "score_inclusive_lang":  0,
        "score_relational":      0,
        "evidence_objectification": get_fragmentos("Objetificación Sexual", "github"),
        "evidence_agency":          get_fragmentos("Agencia y Autonomía", "github"),
        "evidence_roles":           get_fragmentos("Sumisión / Roles de Género", "github"),
        "evidence_possession":      get_fragmentos("Celos / Control", "github"),
        "evidence_degrading":       get_fragmentos("Insultos / Lenguaje Degradante", "github"),
        "llm_raw_response":      resultado,
    }).execute()

    id_groq   = eval_groq.data[0]["id"]
    id_github = eval_github.data[0]["id"]

    # ── Guardar comparación entre modelos ─────────────────────────────────────
    def diff(dim_nombre: str) -> int:
        return abs(
            get_score(dim_nombre, "groq") -
            get_score(dim_nombre, "github")
        )

    supabase.table("model_comparison").insert({
        "song_id":                    song_id,
        "evaluation_model_a_id":      id_groq,
        "evaluation_model_b_id":      id_github,
        "diff_score_objectification": diff("Objetificación Sexual"),
        "diff_score_agency":          diff("Agencia y Autonomía"),
        "diff_score_roles":           diff("Sumisión / Roles de Género"),
        "diff_score_possession":      diff("Celos / Control"),
        "diff_score_degrading":       diff("Insultos / Lenguaje Degradante"),
        "diff_score_inclusive_lang":  0,
        "diff_score_relational":      0,
        "full_agreement":             len(resultado.get("dimensiones_discrepantes", [])) == 0,
        "cohen_kappa":                resultado.get("acuerdo_kendall_tau"),
    }).execute()


# ── ENDPOINT 1: letra nueva desde la web ─────────────────────────────────────

class LyricInput(BaseModel):
    titulo:         str
    artista:        str
    genero_musical: str
    letra:          str

@router.post("/lyrics")
async def analizar_letra_nueva(input: LyricInput):
    """
    El usuario pega una letra desde la web.
    No se guarda en Supabase (es un análisis temporal).
    """
    if len(input.letra.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="La letra es demasiado corta para analizarla"
        )
    return await analizar_cancion(
        song_id="manual",
        titulo=input.titulo,
        artista=input.artista,
        genero_musical=input.genero_musical,
        letra=input.letra,
    )


# ── ENDPOINT 2: canción que ya está en Supabase ───────────────────────────────

@router.post("/song/{song_id}")
async def analizar_por_id(song_id: int):
    """
    Busca la letra en Supabase, analiza y guarda en llm_evaluations
    y model_comparison.
    """
    # 1. Buscar canción
    cancion = (
        supabase.table("songs")
        .select("*")
        .eq("id", song_id)
        .single()
        .execute()
    )
    if not cancion.data:
        raise HTTPException(status_code=404, detail="Canción no encontrada")

    # 2. Buscar letra limpia
    letra_row = (
        supabase.table("lyrics")
        .select("*")
        .eq("song_id", song_id)
        .single()
        .execute()
    )
    if not letra_row.data:
        raise HTTPException(
            status_code=404,
            detail="Esta canción aún no tiene letra"
        )

    # 3. Analizar con el grafo LangGraph
    resultado = await analizar_cancion(
        song_id=str(song_id),
        titulo=cancion.data["title"],
        artista=cancion.data["artist"],
        genero_musical=cancion.data["genre"] or "desconocido",
        letra=letra_row.data["lyrics_text"],
    )

    # 4. Guardar en las tablas existentes
    guardar_en_supabase(
        song_id=song_id,
        lyrics_id=letra_row.data["id"],
        resultado=resultado,
    )

    return resultado
