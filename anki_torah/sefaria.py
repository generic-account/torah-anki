import requests

BASE_URL = "https://www.sefaria.org"
VERSION_TITLE = "The Holy Scriptures: A New Translation (JPS 1917)"
VERSION_PARAM = f"english|{VERSION_TITLE}"


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
