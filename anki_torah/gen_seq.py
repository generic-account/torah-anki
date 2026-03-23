# anki_torah/gen_seq.py

from __future__ import annotations


def ref_to_dot(ref_range: str) -> str:
    """
    Convert:
      "Genesis 1:1-2:3" -> "Genesis.1.1-2.3"
      "Deuteronomy 31:1-30" -> "Deuteronomy.31.1-30"
    """
    book, rest = ref_range.split(" ", 1)
    rest = rest.replace(":", ".")
    return f"{book}.{rest}"


def build_overlapping_full(lines: list[str]) -> str:
    """
    Each line becomes its own cloze item:
      {{c1::line1}}
      {{c2::line2}}
      ...
    """
    return "\n".join([f"{{{{c{i}::{line}}}}}" for i, line in enumerate(lines, start=1)])


def build_sequence_notes(parasha_node: dict, get_text_range_fn) -> list[dict]:
    """
    Builds one note per aliyah for the Cloze (overlapping) note type.

    Your note type fields (after adding NoteID first) are:
      NoteID, Original, Title, Sources, Settings, Text1..Text20, Full

    We'll put:
      - Original = plain verses (one per line)
      - Title    = "Parasha — Aliyah i (RefRange)"
      - Full     = clozed lines {{c1::...}}, {{c2::...}}, ...
      - Text1..Text20 left blank (minimal)
      - Tags     = exported as a separate CSV column
    """
    notes: list[dict] = []
    parasha = parasha_node["parasha"]
    book = parasha_node["book"]

    for aliyah_i, aliyah_ref in enumerate(parasha_node["aliyot"], start=1):
        dot_range = ref_to_dot(aliyah_ref)
        verses = get_text_range_fn(dot_range)

        original = "\n".join(verses)
        full = build_overlapping_full(verses)

        note_id = f"JPS1917|{aliyah_ref}|seq{aliyah_i}"
        tags = f"Torah::{book}::{parasha} Type::Sequence Aliyah::{aliyah_i}"
        title = f"{parasha} — Aliyah {aliyah_i} ({aliyah_ref})"

        row = {
            "NoteID": note_id,
            "Original": original,
            "Title": title,
            "Remarks": "",
            "Sources": "",
            "Settings": "",
            "Full": full,
            "Tags": tags,
        }

        # Ensure Text1..Text20 exist (blank), so CSV export can be deterministic
        for j in range(1, 21):
            row[f"Text{j}"] = ""

        notes.append(row)

    return notes
