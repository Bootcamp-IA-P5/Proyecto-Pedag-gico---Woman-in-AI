import argparse
import asyncio
from pathlib import Path

from app.agents.critic_agent import CriticAgent
from app.agents.judge_agent import JudgeAgent
from app.pipeline.batch_from_csv import delete_existing_evaluations, guardar_en_supabase
from app.pipeline.two_stage_common import (
    append_jsonl,
    configure_logger,
    default_artifact_path,
    nivel_global,
    read_jsonl,
)


MIN_COVERAGE_FOR_CONCLUSIVE = 0.75


async def revisar_dimension(
    letra: str,
    resultado_dimension: dict,
    critic: CriticAgent,
    judge: JudgeAgent,
    timeout_seconds: int,
) -> tuple[dict, dict]:
    revision = await asyncio.wait_for(
        critic.revisar(letra, resultado_dimension), timeout=timeout_seconds
    )
    veredicto = await asyncio.wait_for(
        judge.juzgar(letra, resultado_dimension, revision), timeout=timeout_seconds
    )
    return revision, veredicto


async def procesar_artifact(entry: dict, timeout_seconds: int, logger) -> dict:
    critic = CriticAgent()
    judge = JudgeAgent()
    letra = entry["lyrics_text"]
    stage1_data = entry.get("stage1", {})
    stage1_dims = stage1_data.get("dimensiones", [])
    stage1_errors = stage1_data.get("errores") or []
    dims_con_error = {
        item.get("dimension") for item in stage1_errors if item.get("dimension")
    }

    dimensiones_finales = []
    errores = []
    inconclusas = []

    for dim in stage1_dims:
        dimension_nombre = dim.get("dimension")
        stage1_fallback = (dim.get("proveedor") or "").lower() == "fallback"
        stage1_error = dimension_nombre in dims_con_error

        if stage1_fallback or stage1_error:
            motivo = "stage1_fallback" if stage1_fallback else "stage1_error"
            inconclusas.append(dimension_nombre)
            dimensiones_finales.append(
                {
                    "dimension": dimension_nombre,
                    "puntuacion_openrouter": dim.get("puntuacion", 0),
                    "fragmentos_openrouter": dim.get("fragmentos", []),
                    "puntuacion_final": dim.get("puntuacion", 0),
                    "hay_discrepancia": False,
                    "juez_openrouter": {},
                    "justificacion_openrouter": dim.get("justificacion", ""),
                    "proveedor_openrouter": dim.get("proveedor", "desconocido"),
                    "modelo_openrouter": dim.get("modelo", "desconocido"),
                    "revision_critica": None,
                    "confiable": False,
                    "motivo_inconcluso": motivo,
                }
            )
            continue

        try:
            revision, veredicto = await revisar_dimension(
                letra, dim, critic, judge, timeout_seconds
            )
        except Exception as exc:
            errores.append(
                {
                    "dimension": dim.get("dimension"),
                    "error": str(exc) or exc.__class__.__name__,
                }
            )
            inconclusas.append(dimension_nombre)
            dimensiones_finales.append(
                {
                    "dimension": dimension_nombre,
                    "puntuacion_openrouter": dim.get("puntuacion", 0),
                    "fragmentos_openrouter": dim.get("fragmentos", []),
                    "puntuacion_final": dim.get("puntuacion", 0),
                    "hay_discrepancia": False,
                    "juez_openrouter": {},
                    "justificacion_openrouter": dim.get("justificacion", ""),
                    "proveedor_openrouter": dim.get("proveedor", "desconocido"),
                    "modelo_openrouter": dim.get("modelo", "desconocido"),
                    "revision_critica": None,
                    "confiable": False,
                    "motivo_inconcluso": "stage2_error",
                }
            )
            continue

        dimensiones_finales.append(
            {
                "dimension": dimension_nombre,
                "puntuacion_openrouter": revision.get(
                    "puntuacion_revisada", dim.get("puntuacion", 0)
                ),
                "fragmentos_openrouter": dim.get("fragmentos", []),
                "puntuacion_final": veredicto.get("puntuacion_final", 0),
                "hay_discrepancia": veredicto.get("hay_discrepancia", False),
                "juez_openrouter": veredicto.get("evaluacion_openrouter", {}),
                "justificacion_openrouter": dim.get("justificacion", ""),
                "proveedor_openrouter": dim.get("proveedor", "desconocido"),
                "modelo_openrouter": dim.get("modelo", "desconocido"),
                "revision_critica": revision,
                "confiable": True,
            }
        )

    scores = [item["puntuacion_final"] for item in dimensiones_finales]
    puntuacion = round(sum(scores) / len(scores), 1) if scores else 0.0
    total_dim = len(dimensiones_finales)
    confiables = [d for d in dimensiones_finales if d.get("confiable", False)]
    cobertura = round((len(confiables) / total_dim), 2) if total_dim else 0.0
    sin_sesgo_confiable = [
        d["dimension"] for d in confiables if d["puntuacion_final"] == 0
    ]
    es_conclusivo = cobertura >= MIN_COVERAGE_FOR_CONCLUSIVE
    nivel = nivel_global(puntuacion) if es_conclusivo else "Inconcluso (cobertura insuficiente)"

    discrepantes = [d for d in dimensiones_finales if d["hay_discrepancia"]]
    requiere_revision = (
        len(discrepantes) > 1
        or not es_conclusivo
        or bool(errores)
    )

    puntuacion_global = puntuacion if es_conclusivo else None

    resultado_final = {
        "song_id": str(entry["song_id"]),
        "titulo": entry["title"],
        "artista": entry["artist"],
        "genero_musical": entry["genre"],
        "puntuacion_global": puntuacion_global,
        "puntuacion_global_preliminar": puntuacion,
        "nivel_global": nivel,
        "dimensiones": [
            d for d in dimensiones_finales
            if d.get("confiable", False) and d["puntuacion_final"] > 0
        ],
        "sin_sesgo": sin_sesgo_confiable,
        "dimensiones_inconclusas": inconclusas or None,
        "cobertura_dimensiones": cobertura,
        "dimensiones_discrepantes": [d["dimension"] for d in discrepantes],
        "requiere_revision_humana": requiere_revision,
        "prompt_version": "v1.0",
        "errores": errores or None,
        "modelo_principal": "two-stage-openrouter-github",
        "pipeline_mode": "full-two-stage",
    }

    logger.info(
        f"stage2 song_id={entry['song_id']} puntuacion_global={resultado_final['puntuacion_global']}"
    )
    return {
        "song_id": entry["song_id"],
        "lyrics_id": entry["lyrics_id"],
        "artist_gender": entry.get("artist_gender") or "unknown",
        "final_result": resultado_final,
        "status": "ok",
    }


async def main(args: argparse.Namespace) -> None:
    logger, log_path = configure_logger("stage2_jurors")
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else default_artifact_path("stage2")
    entries = read_jsonl(input_path)

    logger.info(f"Stage 2 -> artefactos a procesar: {len(entries)}")
    for entry in entries:
        result = await procesar_artifact(entry, args.timeout_per_juror_seconds, logger)
        append_jsonl(output_path, result)

        if not args.dry_run and result["status"] == "ok":
            if args.reset_existing:
                delete_existing_evaluations(result["song_id"])
            guardar_en_supabase(
                song_id=result["song_id"],
                lyrics_id=result["lyrics_id"],
                artist_gender=result["artist_gender"],
                resultado=result["final_result"],
            )

    logger.info(f"Artefacto stage2: {output_path}")
    logger.info(f"Log: {log_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Stage 2: critico + juez desde artefacto stage1"
    )
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--timeout-per-juror-seconds", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reset-existing", action="store_true")
    asyncio.run(main(parser.parse_args()))
