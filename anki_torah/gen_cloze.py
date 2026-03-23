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
    try:
        import spacy
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "spaCy is required for cloze generation. Install spaCy and then run: "
            "python -m spacy download en_core_web_sm"
        ) from exc

    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        raise RuntimeError(
            "spaCy model 'en_core_web_sm' is required. Install it with: "
            "python -m spacy download en_core_web_sm"
        )


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
    terms = []
    for token in doc:
        if token.is_space or token.is_punct:
            continue
        norm = _normalize_token(token)
        if norm:
            terms.append(norm)
    return terms


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
    return _base_token_score(token, norm, term_to_col, tfidf_row)


def _base_token_score(
    token, norm: str, term_to_col: dict[str, int], tfidf_row
) -> float:
    if token.is_space or token.is_punct or not norm:
        return 0.0

    tfidf_weight = 0.0
    col = term_to_col.get(norm)
    if col is not None:
        tfidf_weight = float(tfidf_row[0, col])

    pos_bonus = POS_BONUS.get(token.pos_, 0.0)
    cap_bonus = (
        0.7
        if token.text and token.text[0].isupper() and token.is_sent_start is False
        else 0.0
    )
    len_bonus = min(len(token.text), 12) * 0.008

    return tfidf_weight + pos_bonus + cap_bonus + len_bonus

    return tfidf_weight + pos_bonus + cap_bonus + len_bonus


def pick_spans(doc, tfidf_row, term_to_col: dict[str, int], max_spans: int = 2):
    stop_penalty = 0.00
    phrase_bonus = {1: 0.0, 2: 0.15, 3: 0.25}
    phrase_floor = 0.1

    token_data = []
    for token in doc:
        norm = _normalize_token(token)
        is_content = _is_eligible(token, norm)
        base_score = _base_token_score(token, norm, term_to_col, tfidf_row)
        if token.is_space or token.is_punct:
            span_value = stop_penalty
        elif is_content:
            span_value = base_score
        else:
            span_value = stop_penalty

        token_data.append(
            {
                "is_content": is_content,
                "base_score": base_score,
                "span_value": span_value,
            }
        )

    candidates: list[tuple[float, int, int, int, int]] = []
    # tuple: (score, span_len, start_idx, end_idx_exclusive, num_content_tokens)
    for span_len in (3, 2, 1):
        for i in range(0, len(doc) - span_len + 1):
            window = token_data[i : i + span_len]
            num_content_tokens = sum(1 for entry in window if entry["is_content"])
            if span_len == 1 and num_content_tokens == 0:
                continue
            if span_len > 1 and num_content_tokens == 0:
                continue
            avg = sum(entry["span_value"] for entry in window) / span_len
            score = avg + phrase_bonus[span_len]
            candidates.append((score, span_len, i, i + span_len, num_content_tokens))

    if not candidates:
        return []

    def _rank_key(c):
        return (-c[0], -c[1], c[2])

    ranked = sorted(candidates, key=_rank_key)
    singles = [c for c in ranked if c[1] == 1]
    phrases = [c for c in ranked if c[1] in (2, 3) and c[4] > 0]

    best1 = singles[0] if singles else None
    best_phrase = phrases[0] if phrases else None

    chosen: list[tuple[float, int, int, int, int]] = []
    if best1 and best_phrase:
        close_by_delta = best_phrase[0] >= (best1[0] - 0.50)
        close_by_ratio = best_phrase[0] >= (best1[0] * 0.85)
        if best_phrase[0] >= phrase_floor and (close_by_delta or close_by_ratio):
            chosen.append(best_phrase)
        else:
            chosen.append(best1)
    elif best_phrase and best_phrase[0] >= phrase_floor:
        chosen.append(best_phrase)
    elif best1:
        chosen.append(best1)
    elif best_phrase:
        chosen.append(best_phrase)

    def overlaps(a, b):
        return not (a[3] <= b[2] or b[3] <= a[2])

    for cand in ranked:
        if len(chosen) >= max_spans:
            break
        if any(overlaps(cand, prev) for prev in chosen):
            continue
        if cand[1] > 1 and cand[4] == 0:
            continue
        if cand[1] > 1 and cand[0] < phrase_floor:
            continue
        if cand[1] == 1 and cand[4] == 0:
            continue
        chosen.append(cand)

    if not chosen:
        fallback = singles[0] if singles else None
        if fallback:
            chosen = [fallback]

    chosen.sort(key=lambda c: c[2])
    return [(start, end) for _, _, start, end, _ in chosen[:max_spans]]


def _apply_cloze_offsets(text: str, spans: list[tuple[int, int]]) -> str:
    out = text
    for start_char, end_char in sorted(spans, key=lambda x: x[0], reverse=True):
        out = (
            out[:start_char]
            + f"{{{{c1::{out[start_char:end_char]}}}}}"
            + out[end_char:]
        )
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
