import os
import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.src.analysis.graph import analizar_cancion
from app.src.config.supabase_client import supabase

router = APIRouter(prefix="/analysis", tags=["Analisis de sesgos"])


def limpiar_evaluaciones_previas(song_id: int) -> dict:
    evals_deleted = (
        supabase.table("llm_evaluations").delete().eq("song_id", song_id).execute()
    )
    comps_deleted = (
        supabase.table("model_comparison").delete().eq("song_id", song_id).execute()
    )
    return {
        "llm_evaluations": len(evals_deleted.data) if evals_deleted.data else 0,
        "model_comparison": len(comps_deleted.data) if comps_deleted.data else 0,
    }


def obtener_song(song_id: int):
    return supabase.table("songs").select("*").eq("id", song_id).single().execute()


def obtener_lyrics(song_id: int):
    return supabase.table("lyrics").select("*").eq("song_id", song_id).single().execute()


def listar_targets(limit: int):
    return supabase.table("lyrics").select("song_id").limit(limit).execute()


def guardar_en_supabase(song_id: int, lyrics_id: int, resultado: dict):
    dimensiones = {d["dimension"]: d for d in resultado.get("dimensiones", [])}

    def get_score(nombre_dimension: str) -> int:
        dim = dimensiones.get(nombre_dimension, {})
        return int(
            dim.get(
                "puntuacion_final",
                dim.get("puntuacion_openrouter", dim.get("puntuacion_groq", 0)),
            )
            or 0
        )

    def get_fragmentos(nombre_dimension: str):
        dim = dimensiones.get(nombre_dimension, {})
        fragmentos = (
            dim.get("fragmentos_openrouter") or dim.get("fragmentos_groq") or []
        )
        return " | ".join(fragmentos) if fragmentos else None

    def scores() -> dict:
        s = {
            "score_objectification": get_score("Objetificación Sexual"),
            "score_roles": get_score("Sumisión / Roles de Género"),
            "score_possession": get_score("Celos / Control"),
            "score_degrading": get_score("Insultos / Lenguaje Degradante"),
        }
        s["total_score"] = sum(s.values())
        return s

    nivel_global = resultado.get("nivel_global", "")
    puntuacion_global = resultado.get("puntuacion_global", 0)
    explanation = (
        f"puntuacion_global={puntuacion_global} | "
        f"nivel={nivel_global} | "
        f"discrepantes={resultado.get('dimensiones_discrepantes', [])}"
    )
    gender_representation = ", ".join(
        d["dimension"] for d in resultado.get("dimensiones", [])
    )
    symbolic_roles = ", ".join(resultado.get("sin_sesgo", []))

    eval_openrouter = (
        supabase.table("llm_evaluations")
        .insert(
            {
                "song_id": song_id,
                "lyrics_id": lyrics_id,
                "model_name": resultado.get(
                    "modelo_principal",
                    os.getenv("GITHUB_MODELS_MODEL")
                    or os.getenv("OPEN_ROUTER_MODEL", "openrouter/hunter-alpha"),
                ),
                "prompt_version": resultado.get("prompt_version", "v1.0"),
                "temperature": 0.1,
                **scores(),
                "evidence_objectification": get_fragmentos("Objetificación Sexual"),
                "evidence_roles": get_fragmentos("Sumisión / Roles de Género"),
                "evidence_degrading": get_fragmentos("Insultos / Lenguaje Degradante"),
                "dominant_narrative": nivel_global,
                "gender_representation": gender_representation,
                "symbolic_roles": symbolic_roles,
                "explanation": explanation,
                "llm_raw_response": resultado,
            }
        )
        .execute()
    )

    id_openrouter = eval_openrouter.data[0]["id"]

    (
        supabase.table("model_comparison")
        .insert(
            {
                "song_id": song_id,
                "evaluation_model_a_id": id_openrouter,
                "evaluation_model_b_id": id_openrouter,
                # Single-model persistence: keep diff_* neutral to avoid semantic confusion.
                "diff_score_objectification": 0,
                "diff_score_roles": 0,
                "diff_score_possession": 0,
                "diff_score_degrading": 0,
                "full_agreement": len(resultado.get("dimensiones_discrepantes", []))
                == 0,
                "cohen_kappa": resultado.get("acuerdo_kendall_tau"),
            }
        )
        .execute()
    )


class LyricInput(BaseModel):
    titulo: str
    artista: str
    genero_musical: str
    letra: str


class BatchInput(BaseModel):
    limit: int = 5
    dry_run: bool = True
    concurrency: int = 1
    song_ids: list[int] | None = None
    sequential: bool = True
    timeout_per_song_seconds: int = 45


@router.post("/lyrics")
async def analizar_letra_nueva(input: LyricInput):
    if len(input.letra.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="La letra es demasiado corta para analizarla",
        )
    return await analizar_cancion(
        song_id="manual",
        titulo=input.titulo,
        artista=input.artista,
        genero_musical=input.genero_musical,
        letra=input.letra,
    )


@router.post("/song/{song_id}")
async def analizar_por_id(song_id: int):
    cancion = supabase.table("songs").select("*").eq("id", song_id).single().execute()
    if not cancion.data:
        raise HTTPException(status_code=404, detail="Cancion no encontrada")

    letra_row = (
        supabase.table("lyrics").select("*").eq("song_id", song_id).single().execute()
    )
    if not letra_row.data:
        raise HTTPException(status_code=404, detail="Esta cancion aun no tiene letra")

    resultado = await analizar_cancion(
        song_id=str(song_id),
        titulo=cancion.data["title"],
        artista=cancion.data["artist"],
        genero_musical=cancion.data["genre"] or "desconocido",
        letra=letra_row.data["lyrics_text"],
    )

    await run_in_threadpool(
        guardar_en_supabase,
        song_id=song_id,
        lyrics_id=letra_row.data["id"],
        resultado=resultado,
    )

    return resultado


@router.post("/batch/supabase")
async def analizar_batch_desde_supabase(input: BatchInput):
    return await _analizar_batch_desde_supabase(input, reset_existing=False)


@router.post("/batch/supabase/reanalyze")
async def reanalizar_batch_seguro_desde_supabase(input: BatchInput):
    return await _analizar_batch_desde_supabase(input, reset_existing=True)


async def _analizar_batch_desde_supabase(input: BatchInput, reset_existing: bool):
    limit = max(1, min(input.limit, 200))
    concurrency = max(1, min(input.concurrency, 10))
    timeout_per_song = max(10, min(input.timeout_per_song_seconds, 300))

    if input.song_ids:
        targets = [{"song_id": sid} for sid in input.song_ids[:limit]]
    else:
        lyric_rows = await run_in_threadpool(listar_targets, limit)
        targets = [{"song_id": row["song_id"]} for row in (lyric_rows.data or [])]

    if not targets:
        return {
            "ok": 0,
            "errors": 0,
            "skipped": 0,
            "dry_run": input.dry_run,
            "results": [],
            "message": "No se encontraron canciones con letra para analizar",
        }

    semaphore = asyncio.Semaphore(concurrency)

    async def procesar(song_id: int) -> dict:
        async with semaphore:
            try:
                cancion = await run_in_threadpool(obtener_song, song_id)
                if not cancion.data:
                    return {"song_id": song_id, "status": "skipped", "reason": "song_not_found"}

                letra_row = await run_in_threadpool(obtener_lyrics, song_id)
                if not letra_row.data or not (letra_row.data.get("lyrics_text") or "").strip():
                    return {"song_id": song_id, "status": "skipped", "reason": "lyrics_missing"}

                resultado = await analizar_cancion(
                    song_id=str(song_id),
                    titulo=cancion.data.get("title") or "Sin titulo",
                    artista=cancion.data.get("artist") or "Artista desconocido",
                    genero_musical=cancion.data.get("genre") or "desconocido",
                    letra=letra_row.data["lyrics_text"],
                )

                deleted = None

                if not input.dry_run:
                    if reset_existing:
                        deleted = await run_in_threadpool(
                            limpiar_evaluaciones_previas,
                            song_id=song_id,
                        )
                    await run_in_threadpool(
                        guardar_en_supabase,
                        song_id=song_id,
                        lyrics_id=letra_row.data["id"],
                        resultado=resultado,
                    )

                return {
                    "song_id": song_id,
                    "status": "ok",
                    "puntuacion_global": resultado.get("puntuacion_global"),
                    "nivel_global": resultado.get("nivel_global"),
                    "saved": not input.dry_run,
                    "deleted_previous": deleted,
                }
            except Exception as e:
                return {"song_id": song_id, "status": "error", "reason": str(e)}

    if input.sequential or concurrency == 1:
        resultados = []
        for t in targets:
            try:
                r = await asyncio.wait_for(procesar(t["song_id"]), timeout=timeout_per_song)
            except asyncio.TimeoutError:
                r = {
                    "song_id": t["song_id"],
                    "status": "error",
                    "reason": f"timeout_after_{timeout_per_song}s",
                }
            resultados.append(r)
    else:
        tareas = [
            asyncio.wait_for(procesar(t["song_id"]), timeout=timeout_per_song)
            for t in targets
        ]
        raw = await asyncio.gather(*tareas, return_exceptions=True)
        resultados = []
        for t, item in zip(targets, raw):
            if isinstance(item, asyncio.TimeoutError):
                resultados.append(
                    {
                        "song_id": t["song_id"],
                        "status": "error",
                        "reason": f"timeout_after_{timeout_per_song}s",
                    }
                )
            elif isinstance(item, Exception):
                resultados.append(
                    {
                        "song_id": t["song_id"],
                        "status": "error",
                        "reason": str(item),
                    }
                )
            else:
                resultados.append(item)

    ok = sum(1 for r in resultados if r["status"] == "ok")
    errors = sum(1 for r in resultados if r["status"] == "error")
    skipped = sum(1 for r in resultados if r["status"] == "skipped")

    return {
        "ok": ok,
        "errors": errors,
        "skipped": skipped,
        "dry_run": input.dry_run,
        "concurrency": concurrency,
        "sequential": input.sequential or concurrency == 1,
        "timeout_per_song_seconds": timeout_per_song,
        "reset_existing": reset_existing,
        "results": resultados,
    }
