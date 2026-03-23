import requests

BASE_URL = "https://www.sefaria.org"
TORAH_BOOKS = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]


def _raw_index(book: str) -> dict:
    r = requests.get(f"{BASE_URL}/api/v2/raw/index/{book}", timeout=30)
    r.raise_for_status()
    return r.json()


def get_parashot() -> list[dict]:
    """
    Returns a list of parashah dicts:
      {
        "parasha": "Bereshit",
        "book": "Genesis",
        "wholeRef": "Genesis 1:1-6:8",
        "aliyot": ["Genesis 1:1-2:3", ..., 7 items]
      }
    """
    out = []
    for book in TORAH_BOOKS:
        idx = _raw_index(book)
        alt = (idx.get("alt_structs") or {}).get("Parasha") or {}
        nodes = alt.get("nodes") or []
        for n in nodes:
            # Some nodes may be nested; but for Torah Parasha it’s typically flat.
            parasha = n.get("sharedTitle") or n.get("title")
            whole = n.get("wholeRef")
            refs = n.get("refs") or []
            if not parasha or not whole or len(refs) != 7:
                # Skip anything unexpected; you can tighten later if needed.
                continue
            out.append(
                {
                    "parasha": parasha,
                    "book": book,
                    "wholeRef": whole,
                    "aliyot": refs,
                }
            )
    return out
