import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from app.src.config.supabase_client import supabase

load_dotenv()

ARTIFACTS_DIR = Path("pipeline/artifacts")
LOGS_DIR = Path("pipeline/logs")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def configure_logger(name: str) -> tuple[logging.Logger, Path]:
    log_path = LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path),
        ],
        force=True,
    )
    return logging.getLogger(name), log_path


def nivel_global(puntuacion: float) -> str:
    if puntuacion == 0:
        return "Sin sesgo detectado"
    if puntuacion < 1.5:
        return "Leve"
    if puntuacion < 2.5:
        return "Moderado"
    return "Grave"


def default_artifact_path(prefix: str) -> Path:
    return ARTIFACTS_DIR / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"


def append_jsonl(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def list_target_song_ids(limit: int, song_ids: list[int] | None = None) -> list[int]:
    if song_ids:
        return song_ids[:limit]
    rows = supabase.table("lyrics").select("song_id").limit(limit).execute()
    return [row["song_id"] for row in (rows.data or [])]


def fetch_song(song_id: int):
    return supabase.table("songs").select("*").eq("id", song_id).single().execute()


def fetch_lyrics(song_id: int):
    return (
        supabase.table("lyrics").select("*").eq("song_id", song_id).single().execute()
    )


async def fetch_song_bundle(song_id: int) -> tuple[dict | None, dict | None]:
    song = await asyncio.to_thread(fetch_song, song_id)
    lyrics = await asyncio.to_thread(fetch_lyrics, song_id)
    return song.data, lyrics.data
