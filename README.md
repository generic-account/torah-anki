# torah-anki

Generate Anki flashcards for memorizing the Torah (English, **JPS 1917**) with minimal weekly effort.

2 types of automatically generated cards:
- **Cloze verse cards** (Anki Cloze note type): per-verse deletions (up to 2 per verse)
- **Sequence / overlap cards** (Anki Cloze (overlapping) note type): one note per aliyah (7 per parashah), with each verse as the next step in the sequence

## Requirements

- Python 3
- Anki Desktop
- Cloze Overlapper extension

## Run the generator

List available parashah names:

```bash
python3 anki_torah.py list
````

Build one parashah:

```bash
python3 anki_torah.py build Bereshit
```
generating
- `out/<Parasha>.cloze.csv`  
- `out/<Parasha>.sequence.csv`

Build all parashot into combined CSVs:

```bash
python3 anki_torah.py build-all
```

generating
- `out/ALL.cloze.csv`  
- `out/ALL.sequence.csv`

## Anki import

We use stable IDs so re-importing updates notes instead of duplicating them.

1) Add NodeID field to Cloze and Cloze (overlapping) note types
2) Drag this field to the top
3) Create the deck
4) Import close cards, making sure u select comma separation
5) Import sequence cards, also comma separating

## Notes

* Text source: The Holy Scriptures: A New Translation (JPS 1917), from Sefaria v3 Texts API
* Sequence notes are generated one per aliyah (7 per parashah)
* Cloze notes are generated up to 2 per verse using simple heuristics

## Future additions (some manual, some not):
- Better close heuristics
- Manual summary cards for each parshah
- Numerology
- Lives of key characters
- 613 commandments
