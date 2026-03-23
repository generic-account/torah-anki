from __future__ import annotations

from functools import lru_cache

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
    "say",
    "saying",
    "spoke",
    "speak",
    "god",
    "lord",
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

POS_BONUS = {
    "PROPN": 1.5,
    "NUM": 1.2,
    "NOUN": 1.0,
    "VERB": 0.8,
    "ADJ": 0.4,
}


@lru_cache(maxsize=1)
def _get_nlp():
    import spacy

    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        return spacy.blank("en")


def _normalize_token(token) -> str:
    lemma = (token.lemma_ or "").strip().lower()
    if not lemma or lemma == "-pron-":
        lemma = token.text.lower()
    return lemma


def _is_eligible(token, norm: str) -> bool:
    if token.is_space or token.is_punct:
        return False
    if not norm:
        return False
    return norm not in STOPWORDS


def _tokenize_for_tfidf(text: str) -> list[str]:
    doc = _get_nlp()(text)
    return [
        _normalize_token(t)
        for t in doc
        if not t.is_space and not t.is_punct and _normalize_token(t)
    ]


def _fit_vectorizer(verse_texts: list[str]):
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(
        tokenizer=_tokenize_for_tfidf,
        preprocessor=None,
        token_pattern=None,
        lowercase=False,
    )
    x = vectorizer.fit_transform(verse_texts)
    term_to_col = vectorizer.vocabulary_
    return x, term_to_col


def _token_score(token, term_to_col: dict[str, int], tfidf_row) -> float | None:
    norm = _normalize_token(token)
    if not _is_eligible(token, norm):
        return None

    tfidf_weight = 0.0
    col = term_to_col.get(norm)
    if col is not None:
        tfidf_weight = float(tfidf_row[0, col])

    pos_bonus = POS_BONUS.get(token.pos_, 0.0)
    cap_bonus = (
        0.7
        if token.text
        and token.text[0].isupper()
        and token.is_sent_start is False
        else 0.0
    )
    len_bonus = min(len(token.text), 12) * 0.02

    return tfidf_weight + pos_bonus + cap_bonus + len_bonus


def pick_spans(doc, tfidf_row, term_to_col: dict[str, int], max_spans: int = 2):
    scores = [_token_score(token, term_to_col, tfidf_row) for token in doc]

    candidates: list[tuple[float, int, int, int]] = []
    # tuple: (score, span_len, start_idx, end_idx_exclusive)
    for span_len in (3, 2, 1):
        for i in range(0, len(doc) - span_len + 1):
            span_scores = scores[i : i + span_len]
            if any(v is None for v in span_scores):
                continue
            avg = sum(span_scores) / span_len
            candidates.append((avg, span_len, i, i + span_len))

    if not candidates:
        return []

    best1 = max((c for c in candidates if c[1] == 1), default=None)
    best2 = max((c for c in candidates if c[1] == 2), default=None)
    best3 = max((c for c in candidates if c[1] == 3), default=None)

    chosen: list[tuple[float, int, int, int]] = []

    if best1 is not None:
        if best3 and best3[0] >= 1.0 and best3[0] >= best1[0] - 0.25:
            chosen.append(best3)
        elif best2 and best2[0] >= 0.9 and best2[0] >= best1[0] - 0.2:
            chosen.append(best2)
        else:
            chosen.append(best1)
    elif best3:
        chosen.append(best3)
    elif best2:
        chosen.append(best2)

    ranked = sorted(candidates, key=lambda c: (c[0], c[1], -c[2]), reverse=True)

    def overlaps(a, b):
        return not (a[3] <= b[2] or b[3] <= a[2])

    for cand in ranked:
        if len(chosen) >= max_spans:
            break
        if any(overlaps(cand, prev) for prev in chosen):
            continue
        if cand[1] > 1 and cand[0] < 0.8:
            continue
        if cand[1] == 1 and cand[0] < 0.1:
            continue
        chosen.append(cand)

    if not chosen:
        fallback = max((c for c in candidates if c[1] == 1), default=None)
        if fallback:
            chosen = [fallback]

    chosen.sort(key=lambda c: c[2])
    return [(start, end) for _, _, start, end in chosen[:max_spans]]


def _apply_cloze_offsets(text: str, spans: list[tuple[int, int]]) -> str:
    out = text
    for start_char, end_char in sorted(spans, key=lambda x: x[0], reverse=True):
        out = out[:start_char] + f"{{{{c1::{out[start_char:end_char]}}}}}" + out[end_char:]
    return out


def build_cloze_notes_for_verse(
    ref: str,
    parasha: str,
    book: str,
    verse_text: str,
    doc,
    tfidf_row,
    term_to_col: dict[str, int],
    max_clozes: int = 2,
) -> list[dict]:
    token_spans = pick_spans(doc=doc, tfidf_row=tfidf_row, term_to_col=term_to_col)
    notes = []

    for i, (start_idx, end_idx) in enumerate(token_spans[:max_clozes], start=1):
        start_char = doc[start_idx].idx
        end_char = doc[end_idx - 1].idx + len(doc[end_idx - 1].text)
        clozed = _apply_cloze_offsets(verse_text, [(start_char, end_char)])

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
    whole_ref = parasha_node["wholeRef"]

    pairs = get_verses_for_ref_range_fn(whole_ref)
    refs = [ref for ref, _ in pairs]
    verse_texts = [text for _, text in pairs]

    nlp = _get_nlp()
    docs = [nlp(text) for text in verse_texts]

    x, term_to_col = _fit_vectorizer(verse_texts)

    out = []
    for i, ref in enumerate(refs):
        out.extend(
            build_cloze_notes_for_verse(
                ref=ref,
                parasha=parasha,
                book=book,
                verse_text=verse_texts[i],
                doc=docs[i],
                tfidf_row=x[i],
                term_to_col=term_to_col,
                max_clozes=max_clozes_per_verse,
            )
        )
    return out
