from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from app.src.analysis.graph import analizar_cancion
from app.src.config.supabase_client import supabase
import os

router = APIRouter(prefix="/analysis", tags=["Análisis de sesgos"])


# ── Función auxiliar para guardar en Supabase ─────────────────────────────────

def guardar_en_supabase(song_id: int, lyrics_id: int, resultado: dict):
    dimensiones = {d["dimension"]: d for d in resultado.get("dimensiones", [])}

    def get_score(nombre_dimension: str) -> int:
        dimensiones = {d["dimension"]: d for d in resultado.get("dimensiones", [])}
        dim = dimensiones.get(nombre_dimension, {})
        return dim.get("puntuacion_openrouter", 0)

    def get_fragmentos(nombre_dimension: str):
        dimensiones = {d["dimension"]: d for d in resultado.get("dimensiones", [])}
        dim = dimensiones.get(nombre_dimension, {})
        fragmentos = dim.get("fragmentos_openrouter", [])
        return " | ".join(fragmentos) if fragmentos else None

    def scores() -> dict:
        return {
        "score_objectification": get_score("Objetificación Sexual"),
        "score_roles":           get_score("Sumisión / Roles de Género"),
        "score_possession":      get_score("Celos / Control"),
        "score_degrading":       get_score("Insultos / Lenguaje Degradante"),
        "total_score":           sum([
            get_score("Objetificación Sexual"),
            get_score("Sumisión / Roles de Género"),
            get_score("Celos / Control"),
            get_score("Insultos / Lenguaje Degradante"),
        ]),
    }
    # ── Guardar evaluación de OpenRouter ─────────────────────────────────────
    eval_openrouter = supabase.table("llm_evaluations").insert({
        "song_id":               song_id,
        "lyrics_id":             lyrics_id,
        "model_name":            os.getenv("OPEN_ROUTER_MODEL", "openrouter/gemini-2.5-flash"),
        "prompt_version":        resultado.get("prompt_version", "v1.0"),
        "temperature":           0.1,
        **scores(),
        "evidence_objectification": get_fragmentos("Objetificación Sexual",          "openrouter"),
        "evidence_roles":           get_fragmentos("Sumisión / Roles de Género",     "openrouter"),
        "evidence_possession":      get_fragmentos("Celos / Control",                "openrouter"),
        "evidence_degrading":       get_fragmentos("Insultos / Lenguaje Degradante", "openrouter"),
        "dominant_narrative":       nivel_global,
        "gender_representation":    gender_representation,
        "symbolic_roles":           symbolic_roles,
        "explanation":              explanation,
        "llm_raw_response":         resultado,
    }).execute()

    id_openrouter = eval_openrouter.data[0]["id"]

    # ── Guardar comparación entre modelos ─────────────────────────────────────
    def diff(dim_nombre: str) -> int:
        return abs(get_score(dim_nombre, "openrouter"))

    supabase.table("model_comparison").insert({
        "song_id":                    song_id,
        "evaluation_model_b_id":      id_openrouter,
        "diff_score_objectification": diff("Objetificación Sexual"),
        "diff_score_roles":           diff("Sumisión / Roles de Género"),
        "diff_score_possession":      diff("Celos / Control"),
        "diff_score_degrading":       diff("Insultos / Lenguaje Degradante"),
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

    # 2. Buscar letra
    letra_row = (
        supabase.table("lyrics")
        .select("*")
        .eq("song_id", song_id)
        .single()
        .execute()
    )
    if not letra_row.data:
        raise HTTPException(status_code=404, detail="Esta canción aún no tiene letra")

    # 3. Analizar
    resultado = await analizar_cancion(
        song_id=str(song_id),
        titulo=cancion.data["title"],
        artista=cancion.data["artist"],
        genero_musical=cancion.data["genre"] or "desconocido",
        letra=letra_row.data["lyrics_text"],
    )

    # 4. Guardar (ejecutar escritura síncrona en un threadpool para no bloquear el event loop)
    await run_in_threadpool(
        guardar_en_supabase,
        song_id=song_id,
        lyrics_id=letra_row.data["id"],
        resultado=resultado,
    )

    return resultado