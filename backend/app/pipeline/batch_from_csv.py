"""
pipeline/batch_from_csv.py

Lee el CSV local, ejecuta el análisis con LangGraph (sin backend)
y sube los resultados directamente a Supabase.

Uso:
    uv run pipeline/batch_from_csv.py --csv data/songs.csv
    uv run pipeline/batch_from_csv.py --csv data/songs.csv --limit 5 --dry-run
    uv run pipeline/batch_from_csv.py --csv data/songs.csv --concurrency 3
"""

import argparse
import asyncio
import csv
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import os
from dotenv import load_dotenv

load_dotenv()

# ── Logging ────────────────────────────────────────────────────────────────────
Path("pipeline/logs").mkdir(parents=True, exist_ok=True)
log_filename = f"pipeline/logs/batch_csv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_filename),
    ],
)
log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.src.analysis.graph import analizar_cancion  # noqa: E402
from app.src.config.supabase_client import supabase  # noqa: E402


# ── Columnas del CSV (SSOT) ────────────────────────────────────────────────────
COL_SONG_ID = "id_song"
COL_TITLE = "title"
COL_ARTIST = "artist"
COL_GENRE = "genre"
COL_YEAR = "year"
COL_ARTIST_GENDER = "artist_gender"
COL_LYRICS_ID = "id_lyric"
COL_LYRICS_TEXT = "lyrics_text"
COL_LANGUAGE = "language_detected"

# Valores que se consideran español (normalizado a minúsculas)
SPANISH_LANG_VALUES = {"es", "español", "spanish", "es-la", "es-us", "spanglish"}


# ── Supabase helpers ───────────────────────────────────────────────────────────


def delete_existing_evaluations(song_id: int) -> int:
    comparisons_deleted = (
        supabase.table("model_comparison").delete().eq("song_id", song_id).execute()
    )
    evals_deleted = (
        supabase.table("llm_evaluations").delete().eq("song_id", song_id).execute()
    )
    return (len(evals_deleted.data) if evals_deleted.data else 0) + (
        len(comparisons_deleted.data) if comparisons_deleted.data else 0
    )


def guardar_en_supabase(
    song_id: int, lyrics_id: int, artist_gender: str, resultado: dict
) -> None:
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

    def get_fragmentos(nombre_dimension: str) -> str | None:
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

    base = {
        "song_id": song_id,
        "lyrics_id": lyrics_id,
        "prompt_version": resultado.get("prompt_version", "v1.0"),
        "temperature": 0.1,
        "dominant_narrative": nivel_global,
        "gender_representation": gender_representation,
        "symbolic_roles": symbolic_roles,
        "explanation": explanation,
        "llm_raw_response": resultado,
        "artist_gender": artist_gender or "unknown",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }

    eval_result = (
        supabase.table("llm_evaluations")
        .insert(
            {
                **base,
                "model_name": resultado.get(
                    "modelo_principal",
                    os.getenv("GITHUB_MODELS_MODEL")
                    or os.getenv("OPEN_ROUTER_MODEL", "openrouter/hunter-alpha"),
                ),
                **scores(),
                "evidence_objectification": get_fragmentos("Objetificación Sexual"),
                "evidence_roles": get_fragmentos("Sumisión / Roles de Género"),
                "evidence_degrading": get_fragmentos("Insultos / Lenguaje Degradante"),
            }
        )
        .execute()
    )

    id_eval = eval_result.data[0]["id"]

    supabase.table("model_comparison").insert(
        {
            "song_id": song_id,
            "evaluation_model_a_id": id_eval,
            "evaluation_model_b_id": id_eval,
            # Single-model pipeline: no model-vs-model delta is available.
            "diff_score_objectification": 0,
            "diff_score_roles": 0,
            "diff_score_possession": 0,
            "diff_score_degrading": 0,
            "full_agreement": len(resultado.get("dimensiones_discrepantes", [])) == 0,
            "cohen_kappa": resultado.get("acuerdo_kendall_tau"),
        }
    ).execute()


# ── Procesar una fila del CSV ──────────────────────────────────────────────────


async def procesar_fila(row: dict, dry_run: bool, semaphore: asyncio.Semaphore) -> dict:
    song_id = int(row[COL_SONG_ID])
    lyrics_id = int(row[COL_LYRICS_ID]) if row.get(COL_LYRICS_ID) else None
    title = row[COL_TITLE]
    artist = row[COL_ARTIST]
    genre = row.get(COL_GENRE) or "desconocido"
    artist_gender = row.get(COL_ARTIST_GENDER) or "unknown"
    lyrics_text = row.get(COL_LYRICS_TEXT, "")

    async with semaphore:
        log.info(f"▶ song_id={song_id} | {artist} — {title}")

        if not lyrics_text or len(lyrics_text.strip()) < 50:
            log.warning("  ⚠ Letra demasiado corta, saltando")
            return {"song_id": song_id, "status": "skipped", "reason": "letra_corta"}

        if lyrics_id is None:
            log.warning("  ⚠ Sin id_lyric, saltando")
            return {"song_id": song_id, "status": "skipped", "reason": "sin_lyrics_id"}

        if not dry_run:
            borradas = delete_existing_evaluations(song_id)
            if borradas:
                log.info(f"  🗑  Eliminadas {borradas} evaluaciones previas")

        try:
            resultado = await analizar_cancion(
                song_id=str(song_id),
                titulo=title,
                artista=artist,
                genero_musical=genre,
                letra=lyrics_text,
            )
        except Exception as e:
            log.error(f"  ✗ Error en análisis: {e}")
            return {"song_id": song_id, "status": "error", "reason": str(e)}

        if resultado.get("errores"):
            log.warning(f"  ⚠ Errores parciales: {resultado['errores']}")

        if dry_run:
            log.info(
                f"  [DRY-RUN] puntuacion_global={resultado.get('puntuacion_global')} "
                f"nivel={resultado.get('nivel_global')}"
            )
            return {"song_id": song_id, "status": "dry_run"}

        try:
            guardar_en_supabase(song_id, lyrics_id, artist_gender, resultado)
        except Exception as e:
            log.error(f"  ✗ Error al guardar en Supabase: {e}")
            return {"song_id": song_id, "status": "error", "reason": f"supabase: {e}"}

        log.info(
            f"  ✓ Guardado | puntuacion_global={resultado.get('puntuacion_global')} "
            f"nivel={resultado.get('nivel_global')}"
        )
        return {
            "song_id": song_id,
            "status": "ok",
            "puntuacion_global": resultado.get("puntuacion_global"),
            "nivel_global": resultado.get("nivel_global"),
        }


# ── Main ───────────────────────────────────────────────────────────────────────


async def main(args: argparse.Namespace) -> None:
    csv_path = Path(args.csv)
    if not csv_path.exists():
        log.error(f"CSV no encontrado: {csv_path}")
        sys.exit(1)

    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Filtrar: solo canciones en español con letra
    def es_espanol(row: dict) -> bool:
        lang = row.get(COL_LANGUAGE, "").strip().lower()
        return lang in SPANISH_LANG_VALUES

    rows_con_letra = [r for r in rows if r.get(COL_LYRICS_TEXT, "").strip()]
    rows_validas = [r for r in rows_con_letra if es_espanol(r)]
    rows_otros_lang = len(rows_con_letra) - len(rows_validas)

    log.info(
        f"Filas en CSV: {len(rows)} | "
        f"Con letra: {len(rows_con_letra)} | "
        f"En español: {len(rows_validas)} | "
        f"Otros idiomas (saltados): {rows_otros_lang}"
    )

    if args.limit:
        rows_validas = rows_validas[: args.limit]

    log.info(
        f"{'[DRY-RUN] ' if args.dry_run else ''}"
        f"A procesar: {len(rows_validas)} | Concurrencia: {args.concurrency}"
    )

    semaphore = asyncio.Semaphore(args.concurrency)
    tareas = [procesar_fila(row, args.dry_run, semaphore) for row in rows_validas]
    resultados = await asyncio.gather(*tareas)

    ok = sum(1 for r in resultados if r["status"] == "ok")
    skipped = sum(1 for r in resultados if r["status"] == "skipped")
    dry = sum(1 for r in resultados if r["status"] == "dry_run")
    errors = [r for r in resultados if r["status"] == "error"]

    log.info("─" * 60)
    log.info(
        f"RESUMEN | ✓ OK: {ok} | ⚠ Saltadas: {skipped} | ✗ Errores: {len(errors)}"
        + (f" | 🔍 Dry-run: {dry}" if dry else "")
    )
    for e in errors:
        log.info(f"  song_id={e['song_id']} → {e.get('reason', '?')}")
    log.info(f"Log: {log_filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CSV local → LangGraph (sin backend) → Supabase"
    )
    parser.add_argument(
        "--csv", default="../data/final/dataset_final.csv", help="Ruta al CSV"
    )
    parser.add_argument(
        "--concurrency", type=int, default=1, help="Canciones en paralelo (default: 1)"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Procesar solo las primeras N canciones"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecuta el análisis pero NO guarda en Supabase",
    )
    asyncio.run(main(parser.parse_args()))
