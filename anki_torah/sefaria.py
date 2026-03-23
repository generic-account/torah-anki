import requests
import re
from typing import List, Tuple

BASE_URL = "https://www.sefaria.org"
VERSION_TITLE = "The Holy Scriptures: A New Translation (JPS 1917)"
VERSION_PARAM = f"english|{VERSION_TITLE}"

# Case A: Book 1:1-2:3
_REF_A = re.compile(r"^([A-Za-z]+)\s+(\d+):(\d+)-(\d+):(\d+)$")
# Case B: Book 31:1-30   (same chapter)
_REF_B = re.compile(r"^([A-Za-z]+)\s+(\d+):(\d+)-(\d+)$")


def _flatten(x):
    if x is None:
        return []
    if isinstance(x, str):
        s = x.strip()
        return [s] if s else []
    if isinstance(x, list):
        out = []
        for item in x:
            out.extend(_flatten(item))
        return out
    return []


def _fetch(tref: str) -> dict:
    # Expect tref in Sefaria dot form, e.g. Genesis.1.1 or Genesis.1.1-5
    r = requests.get(
        f"{BASE_URL}/api/v3/texts/{tref}",
        params={
            "version": VERSION_PARAM,
            "context": 0,
            "format": "text_only",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def get_text(tref: str) -> str:
    data = _fetch(tref)
    text = data["versions"][0]["text"]
    segs = _flatten(text)
    if not segs:
        raise ValueError(f"No text returned for {tref}")
    return segs[0] if len(segs) == 1 else " ".join(segs)


def get_text_range(tref_range: str) -> list[str]:
    data = _fetch(tref_range)
    text = data["versions"][0]["text"]
    segs = _flatten(text)
    if not segs:
        raise ValueError(f"No text returned for {tref_range}")
    return segs


def parse_ref_range(ref_range: str) -> Tuple[str, int, int, int, int]:
    s = ref_range.strip()

    m = _REF_A.match(s)
    if m:
        book = m.group(1)
        sc, sv, ec, ev = map(int, m.groups()[1:])
        return book, sc, sv, ec, ev

    m = _REF_B.match(s)
    if m:
        book = m.group(1)
        ch = int(m.group(2))
        sv = int(m.group(3))
        ev = int(m.group(4))
        return book, ch, sv, ch, ev

    raise ValueError(f"Unsupported ref_range format: {ref_range!r}")


def get_chapter(book: str, chapter: int) -> List[str]:
    """
    Returns list of verses for e.g. Genesis chapter 1.
    """
    return get_text_range(f"{book}.{chapter}")


def iter_verses(
    book: str, start_ch: int, start_v: int, end_ch: int, end_v: int
) -> List[Tuple[str, str]]:
    """
    Iterate verses across chapters, inclusive bounds.
    Returns list of (ref, verse_text) where ref is 'Genesis 1:1' style.
    """
    out: List[Tuple[str, str]] = []
    for ch in range(start_ch, end_ch + 1):
        verses = get_chapter(book, ch)  # list[str], 1-indexed conceptually

        if ch == start_ch and ch == end_ch:
            lo, hi = start_v, end_v
        elif ch == start_ch:
            lo, hi = start_v, len(verses)
        elif ch == end_ch:
            lo, hi = 1, end_v
        else:
            lo, hi = 1, len(verses)

        # slice uses 0-index; inclusive hi
        for vnum in range(lo, hi + 1):
            text = verses[vnum - 1]
            ref = f"{book} {ch}:{vnum}"
            out.append((ref, text))
    return out


def get_verses_for_ref_range(ref_range: str) -> List[Tuple[str, str]]:
    """
    Convenience: takes 'Genesis 1:1-2:3' and returns list of (ref,text).
    """
    book, sc, sv, ec, ev = parse_ref_range(ref_range)
    return iter_verses(book, sc, sv, ec, ev)
