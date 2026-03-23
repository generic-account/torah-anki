# anki_torah/export_csv.py
import csv
from pathlib import Path

# For Cloze (built-in) after you add NoteID as first field:
# Fields: NoteID, Text, Extra
CLOZE_FIELDS = ["NoteID", "Text", "Extra", "Tags"]

# For Cloze (overlapping) after you add NoteID as first field:
# Fields: NoteID, Title, Original, Sources, Settings, Text1..Text20, Full
SEQUENCE_FIELDS = (
    ["NoteID", "Original", "Title", "Remarks", "Sources", "Settings"]
    + [f"Text{i}" for i in range(1, 21)]
    + ["Full", "Tags"]
)


def write_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        # No header row
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_cloze_csv(path: str, rows: list[dict]) -> None:
    """
    Expects rows that contain:
      NoteID, Text, Extra, Tags
    """
    write_csv(path, rows, CLOZE_FIELDS)


def write_sequence_csv(path: str, rows: list[dict]) -> None:
    """
    Expects rows that contain:
      NoteID, Title, Original, Sources, Settings, Text1..Text20, Full, Tags
    """
    write_csv(path, rows, list(SEQUENCE_FIELDS))
