# anki_torah/gen_seq.py


def ref_to_dot(ref: str) -> str:
    # "Genesis 1:1-2:3" -> "Genesis.1.1-2.3"
    book, rest = ref.split(" ", 1)
    rest = rest.replace(":", ".")
    return f"{book}.{rest}"


def build_sequence_notes(parasha_node: dict, get_text_range_fn) -> list[dict]:
    """
    parasha_node: {"parasha":..., "book":..., "wholeRef":..., "aliyot":[...]}
    get_text_range_fn: function(dot_ref_range)->list[str]
    """
    notes = []
    parasha = parasha_node["parasha"]
    book = parasha_node["book"]

    for i, aliyah_ref in enumerate(parasha_node["aliyot"], start=1):
        dot_range = ref_to_dot(aliyah_ref)
        verses = get_text_range_fn(dot_range)
        run_text = "\n".join(verses)

        note_id = f"JPS1917|{aliyah_ref}|seq{i}"
        tags = f"Torah::{book}::{parasha} Type::Sequence Aliyah::{i}"

        notes.append(
            {
                "NoteID": note_id,
                "RefRange": aliyah_ref,
                "Parasha": parasha,
                "RunText": run_text,
                "Tags": tags,
            }
        )

    return notes
