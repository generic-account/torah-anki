from __future__ import annotations

import re


def tagify(value: str) -> str:
    """
    Convert a string to a safe Anki tag component.

    - strips surrounding whitespace
    - replaces whitespace with underscores
    - removes characters outside [A-Za-z0-9_:.-]
    """
    value = value.strip()
    value = re.sub(r"\s+", "_", value)
    return re.sub(r"[^A-Za-z0-9_:.-]", "", value)
