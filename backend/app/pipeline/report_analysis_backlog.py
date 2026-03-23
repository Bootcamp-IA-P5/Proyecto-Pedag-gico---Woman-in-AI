import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.src.config.supabase_client import supabase


def fetch_lyrics_song_ids(page_size: int = 1000) -> set[int]:
    ids: set[int] = set()
    offset = 0
    while True:
        rows = (
            supabase.table("lyrics")
            .select("song_id")
            .range(offset, offset + page_size - 1)
            .execute()
            .data
            or []
        )
        if not rows:
            break
        ids.update(
            int(row["song_id"])
            for row in rows
            if row.get("song_id") is not None
        )
        offset += len(rows)
        if len(rows) < page_size:
            break
    return ids


def fetch_evaluated_song_ids(page_size: int = 1000) -> set[int]:
    ids: set[int] = set()
    offset = 0
    while True:
        rows = (
            supabase.table("llm_evaluations")
            .select("song_id")
            .range(offset, offset + page_size - 1)
            .execute()
            .data
            or []
        )
        if not rows:
            break
        ids.update(
            int(row["song_id"])
            for row in rows
            if row.get("song_id") is not None
        )
        offset += len(rows)
        if len(rows) < page_size:
            break
    return ids


def export_pending_ids(path: Path, pending_ids: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["song_id"])
        for song_id in pending_ids:
            writer.writerow([song_id])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reporte de backlog de analisis (sin consumir tokens LLM)"
    )
    parser.add_argument(
        "--export-pending-csv",
        type=str,
        default=None,
        help="Ruta opcional para exportar IDs pendientes a CSV",
    )
    args = parser.parse_args()

    lyrics_ids = fetch_lyrics_song_ids()
    evaluated_ids = fetch_evaluated_song_ids()

    pending_ids = sorted(list(lyrics_ids - evaluated_ids))

    print("=== BACKLOG ANALISIS ===")
    print(f"Canciones con letra: {len(lyrics_ids)}")
    print(f"Canciones con evaluacion: {len(evaluated_ids)}")
    print(f"Pendientes de evaluar: {len(pending_ids)}")

    if pending_ids:
        preview = ", ".join(str(song_id) for song_id in pending_ids[:20])
        print(f"Primeros pending song_id: {preview}")

    if args.export_pending_csv:
        export_path = Path(args.export_pending_csv)
        export_pending_ids(export_path, pending_ids)
        print(f"CSV pendiente exportado en: {export_path}")


if __name__ == "__main__":
    main()