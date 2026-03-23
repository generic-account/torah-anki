import re

STOPWORDS = {
    "the",
    "and",
    "that",
    "with",
    "from",
    "into",
    "over",
    "upon",
    "there",
    "their",
    "then",
    "when",
    "which",
    "shall",
    "were",
    "was",
    "are",
    "his",
    "her",
    "its",
    "him",
    "them",
    "said",
    "says",
    "god",
    "lord",  # optional: you may remove "god/lord" if you want them clozed
    "in",
    "on",
    "to",
    "of",
    "a",
    "an",
    "for",
    "as",
    "at",
    "by",
    "is",
    "be",
    "or",
    "not",
}

WORD_RE = re.compile(r"[A-Za-z’']+")


def _candidates(text: str) -> list[str]:
    # extract tokens (letters + apostrophes)
    toks = WORD_RE.findall(text)
    if not toks:
        return []

    # first token often capitalized just because sentence start; downweight it
    first = toks[0].lower()

    # 1) proper-ish (capitalized) excluding first-word cases like "In", "And", "Now"
    caps = []
    for t in toks:
        if t[0].isupper() and t.lower() not in STOPWORDS and t.lower() != first:
            caps.append(t)
    # 2) longer content words
    longs = []
    for t in toks:
        tl = t.lower()
        if tl in STOPWORDS:
            continue
        if len(t) >= 6:
            longs.append(t)

    # preserve order, unique
    seen = set()
    out = []
    for lst in (caps, longs):
        for t in lst:
            key = t.lower()
            if key not in seen:
                seen.add(key)
                out.append(t)
    return out


def _apply_cloze(text: str, target: str, cloze_n: int = 1) -> str:
    # Replace first occurrence with cloze markup; keep original casing/punct around it
    # Use word boundary-ish replace to avoid substring issues.
    pattern = re.compile(rf"\b{re.escape(target)}\b")
    return pattern.sub(f"{{{{c{cloze_n}::{target}}}}}", text, count=1)


def build_cloze_notes_for_verse(
    ref: str, parasha: str, book: str, verse_text: str, max_clozes: int = 2
) -> list[dict]:
    cands = _candidates(verse_text)
    notes = []
    for i, target in enumerate(cands[:max_clozes], start=1):
        clozed = _apply_cloze(
            verse_text, target, cloze_n=1
        )  # always c1 for Anki cloze note
        note_id = f"JPS1917|{ref}|c{i}"
        tags = f"Torah::{book}::{parasha} Type::AutoCloze"
        notes.append(
            {
                "NoteID": note_id,
                "Text": clozed,
                "Extra": f"{ref} | {parasha}",
                "Tags": tags,
            }
        )

    return notes


def build_cloze_notes_for_parasha(
    parasha_node: dict, get_verses_for_ref_range_fn, max_clozes_per_verse: int = 2
) -> list[dict]:
    parasha = parasha_node["parasha"]
    book = parasha_node["book"]
    whole_ref = parasha_node["wholeRef"]  # e.g. "Genesis 1:1-6:8"

    pairs = get_verses_for_ref_range_fn(whole_ref)  # [(ref, text), ...]

    out = []
    for ref, verse_text in pairs:
        out.extend(
            build_cloze_notes_for_verse(
                ref=ref,
                parasha=parasha,
                book=book,
                verse_text=verse_text,
                max_clozes=max_clozes_per_verse,
            )
        )
    return out
