import argparse
import asyncio
from pathlib import Path

from app.agents.jelous_agent import CelosAgent
from app.agents.object_agent import ObjetificacionAgent
from app.agents.strong_language_agent import InsultosAgent
from app.agents.sumision_agent import SumisionAgent
from app.pipeline.two_stage_common import (
    append_jsonl,
    configure_logger,
    default_artifact_path,
    fetch_song_bundle,
    list_target_song_ids_async,
    nivel_global,
)


AGENTS = [
    CelosAgent(),
    InsultosAgent(),
    SumisionAgent(),
    ObjetificacionAgent(),
]


async def analizar_dimension(agent, letra: str, timeout_seconds: int) -> dict:
    return await asyncio.wait_for(agent.analizar(letra), timeout=timeout_seconds)


async def procesar_song(song_id: int, timeout_seconds: int, logger) -> dict:
    song, lyrics = await fetch_song_bundle(song_id)
    if not song:
        return {"song_id": song_id, "status": "skipped", "reason": "song_not_found"}
    if not lyrics or not (lyrics.get("lyrics_text") or "").strip():
        return {"song_id": song_id, "status": "skipped", "reason": "lyrics_missing"}

    letra = lyrics["lyrics_text"]
    dimensiones = []
    errores = []

    for agent in AGENTS:
        try:
            resultado = await analizar_dimension(agent, letra, timeout_seconds)
            dimensiones.append(resultado)
        except Exception as exc:
            err_msg = str(exc).strip() or exc.__class__.__name__
            errores.append(
                {
                    "dimension": agent.dimension,
                    "error": err_msg,
                }
            )
            dimensiones.append(
                {
                    "dimension": agent.dimension,
                    "puntuacion": 0,
                    "fragmentos": [],
                    "justificacion": "",
                    "proveedor": "fallback",
                    "modelo": "fallback",
                }
            )

    scores = [item.get("puntuacion", 0) for item in dimensiones]
    puntuacion = round(sum(scores) / len(scores), 1) if scores else 0.0

    artifact = {
        "song_id": song_id,
        "lyrics_id": lyrics["id"],
        "title": song.get("title") or "Sin titulo",
        "artist": song.get("artist") or "Artista desconocido",
        "genre": song.get("genre") or "desconocido",
        "artist_gender": song.get("artist_gender") or "unknown",
        "lyrics_text": letra,
        "stage1": {
            "puntuacion_global": puntuacion,
            "nivel_global": nivel_global(puntuacion),
            "dimensiones": dimensiones,
            "errores": errores or None,
            "pipeline_mode": "dimensions-only",
        },
        "status": "ok",
    }
    logger.info(
        f"stage1 song_id={song_id} puntuacion_global={artifact['stage1']['puntuacion_global']}"
    )
    return artifact


async def main(args: argparse.Namespace) -> None:
    logger, log_path = configure_logger("stage1_dimensions")
    output_path = Path(args.output) if args.output else default_artifact_path("stage1")
    targets = await list_target_song_ids_async(args.limit, args.song_ids)

    logger.info(f"Stage 1 -> canciones objetivo: {len(targets)}")
    for song_id in targets:
        result = await procesar_song(
            song_id, args.timeout_per_dimension_seconds, logger
        )
        append_jsonl(output_path, result)

    logger.info(f"Artefacto stage1: {output_path}")
    logger.info(f"Log: {log_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Stage 1: 4 agentes de dimension desde Supabase"
    )
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--song-ids", type=int, nargs="*", default=None)
    parser.add_argument("--timeout-per-dimension-seconds", type=int, default=25)
    parser.add_argument("--output", type=str, default=None)
    asyncio.run(main(parser.parse_args()))
