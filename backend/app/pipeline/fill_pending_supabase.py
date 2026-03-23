import argparse
import asyncio
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.pipeline.batch_from_csv import guardar_en_supabase
from app.src.analysis.graph import analizar_cancion
from app.src.config.supabase_client import supabase


LOGS_DIR = Path("pipeline/logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def configure_logger() -> tuple[logging.Logger, Path]:
    log_path = LOGS_DIR / f"fill_pending_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path),
        ],
        force=True,
    )
    return logging.getLogger("fill_pending"), log_path


def fetch_lyrics_page(offset: int, page_size: int):
    return (
        supabase.table("lyrics")
        .select("song_id,id,lyrics_text")
        .range(offset, offset + page_size - 1)
        .execute()
    )


def is_already_evaluated(song_id: int) -> bool:
    existing = (
        supabase.table("llm_evaluations")
        .select("id", count="exact")
        .eq("song_id", song_id)
        .limit(1)
        .execute()
    )
    return (existing.count or 0) > 0


def fetch_song(song_id: int):
    return supabase.table("songs").select("*").eq("id", song_id).single().execute()


def is_token_or_rate_error(msg: str) -> bool:
    lowered = (msg or "").lower()
    return any(
        marker in lowered
        for marker in [
            "402",
            "429",
            "payment required",
            "quota",
            "rate limit",
            "insufficient credits",
            "credit",
        ]
    )


def is_rate_limit_error(msg: str) -> bool:
    lowered = (msg or "").lower()
    return "429" in lowered or "rate limit" in lowered or "too many requests" in lowered


def extract_provider_from_error(msg: str, fallback_provider: str) -> str:
    match = re.search(r"\[([a-zA-Z0-9_-]+)\]", msg or "")
    if match:
        return match.group(1).lower()
    return fallback_provider


def read_provider_rpm(provider: str) -> float | None:
    for key in (f"LLM_RPM_{provider.upper()}", "LLM_RPM_DEFAULT"):
        raw = os.getenv(key)
        if not raw:
            continue
        try:
            value = float(raw)
        except ValueError:
            continue
        if value > 0:
            return value
    return None


def set_provider_rpm(provider: str, rpm: float) -> None:
    os.environ[f"LLM_RPM_{provider.upper()}"] = f"{rpm:.2f}".rstrip("0").rstrip(".")


async def main(args: argparse.Namespace) -> None:
    log, log_path = configure_logger()

    offset = args.offset
    processed_ok = 0
    processed_error = 0
    skipped_existing = 0
    skipped_invalid = 0
    scanned = 0
    consecutive_provider_failures = 0

    log.info(
        "Inicio fill_pending | max_songs=%s page_size=%s offset=%s cooldown=%ss",
        args.max_songs,
        args.page_size,
        args.offset,
        args.cooldown_seconds,
    )
    log.info(
        "Adaptive RPM=%s | provider_base=%s | start_rpm=%s | min_rpm=%s | step_down=%s",
        args.adaptive_rpm,
        args.adaptive_provider,
        args.adaptive_start_rpm,
        args.min_rpm,
        args.rpm_step_down,
    )

    while processed_ok < args.max_songs:
        rows = fetch_lyrics_page(offset, args.page_size).data or []
        if not rows:
            log.info("No hay mas filas en lyrics para escanear. Fin de corrida.")
            break

        for row in rows:
            scanned += 1
            song_id = row.get("song_id")
            lyrics_id = row.get("id")
            lyrics_text = row.get("lyrics_text") or ""

            if not song_id or not lyrics_id or len(lyrics_text.strip()) < 50:
                skipped_invalid += 1
                continue

            if is_already_evaluated(song_id):
                skipped_existing += 1
                continue

            song_row = fetch_song(song_id).data
            if not song_row:
                skipped_invalid += 1
                continue

            try:
                log.info(
                    "Analizando song_id=%s | %s - %s",
                    song_id,
                    song_row.get("artist") or "Artista desconocido",
                    song_row.get("title") or "Sin titulo",
                )

                resultado = await analizar_cancion(
                    song_id=str(song_id),
                    titulo=song_row.get("title") or "Sin titulo",
                    artista=song_row.get("artist") or "Artista desconocido",
                    genero_musical=song_row.get("genre") or "desconocido",
                    letra=lyrics_text,
                )

                guardar_en_supabase(
                    song_id=song_id,
                    lyrics_id=lyrics_id,
                    artist_gender=song_row.get("artist_gender") or "unknown",
                    resultado=resultado,
                )

                processed_ok += 1
                consecutive_provider_failures = 0
                log.info(
                    "Guardado OK song_id=%s | puntuacion_global=%s nivel=%s | total_ok=%s",
                    song_id,
                    resultado.get("puntuacion_global"),
                    resultado.get("nivel_global"),
                    processed_ok,
                )
            except Exception as exc:
                processed_error += 1
                err_msg = str(exc).strip() or exc.__class__.__name__
                log.error("Error song_id=%s -> %s", song_id, err_msg)

                if is_token_or_rate_error(err_msg):
                    consecutive_provider_failures += 1

                    if args.adaptive_rpm and is_rate_limit_error(err_msg):
                        provider = extract_provider_from_error(
                            err_msg,
                            args.adaptive_provider,
                        )
                        current_rpm = read_provider_rpm(provider)
                        if current_rpm is None:
                            current_rpm = args.adaptive_start_rpm
                            set_provider_rpm(provider, current_rpm)

                        new_rpm = max(args.min_rpm, current_rpm - args.rpm_step_down)
                        if new_rpm < current_rpm:
                            set_provider_rpm(provider, new_rpm)
                            log.warning(
                                "429 detectado (%s). Bajando %s RPM: %.2f -> %.2f",
                                provider,
                                provider,
                                current_rpm,
                                new_rpm,
                            )

                        if args.extra_wait_on_429_seconds > 0:
                            log.warning(
                                "Espera extra tras 429: %.1fs",
                                args.extra_wait_on_429_seconds,
                            )
                            await asyncio.sleep(args.extra_wait_on_429_seconds)

                    if consecutive_provider_failures >= args.max_consecutive_provider_failures:
                        log.error(
                            "Deteniendo corrida por fallos consecutivos de proveedor (%s).",
                            consecutive_provider_failures,
                        )
                        log.info("Log: %s", log_path)
                        return
                else:
                    consecutive_provider_failures = 0

            if processed_ok >= args.max_songs:
                break

            if args.cooldown_seconds > 0:
                await asyncio.sleep(args.cooldown_seconds)

        offset += len(rows)

    log.info(
        "Fin fill_pending | ok=%s error=%s skipped_existing=%s skipped_invalid=%s scanned=%s",
        processed_ok,
        processed_error,
        skipped_existing,
        skipped_invalid,
        scanned,
    )
    log.info("Log: %s", log_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analiza solo canciones pendientes en Supabase (sin duplicar evaluaciones)"
    )
    parser.add_argument("--max-songs", type=int, default=50)
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--cooldown-seconds", type=float, default=0.5)
    parser.add_argument("--max-consecutive-provider-failures", type=int, default=3)
    parser.add_argument("--adaptive-rpm", action="store_true")
    parser.add_argument("--adaptive-provider", type=str, default="groq")
    parser.add_argument("--adaptive-start-rpm", type=float, default=8.0)
    parser.add_argument("--min-rpm", type=float, default=2.0)
    parser.add_argument("--rpm-step-down", type=float, default=1.0)
    parser.add_argument("--extra-wait-on-429-seconds", type=float, default=20.0)
    asyncio.run(main(parser.parse_args()))