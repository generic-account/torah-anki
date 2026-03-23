# anki_torah/export_csv.py
import csv
from pathlib import Path


def write_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        # No header row (simpler for Anki); if you want headers, set writeheader=True
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_cloze_csv(path: str, rows: list[dict]) -> None:
    write_csv(path, rows, ["NoteID", "Ref", "Parasha", "Text", "Tags"])


def write_sequence_csv(path: str, rows: list[dict]) -> None:
    write_csv(path, rows, ["NoteID", "RefRange", "Parasha", "RunText", "Tags"])
