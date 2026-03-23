#!/usr/bin/env python3
import argparse
import sys

from anki_torah.parasha import get_parashot
from anki_torah.sefaria import get_verses_for_ref_range, get_text_range
from anki_torah.gen_cloze import build_cloze_notes_for_parasha
from anki_torah.gen_seq import build_sequence_notes
from anki_torah.export_csv import write_cloze_csv, write_sequence_csv


def cmd_list(_: argparse.Namespace) -> int:
    ps = get_parashot()
    for p in ps:
        print(p["parasha"])
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    name = args.parasha
    ps = get_parashot()
    try:
        p = next(x for x in ps if x["parasha"].lower() == name.lower())
    except StopIteration:
        print(
            f"Unknown parasha: {name!r}. Try: python anki_torah.py list",
            file=sys.stderr,
        )
        return 2

    seq_notes = build_sequence_notes(p, get_text_range)
    cloze_notes = build_cloze_notes_for_parasha(p, get_verses_for_ref_range)

    out_prefix = args.out_prefix or p["parasha"]
    seq_path = f"out/{out_prefix}.sequence.csv"
    cloze_path = f"out/{out_prefix}.cloze.csv"

    write_sequence_csv(seq_path, seq_notes)
    write_cloze_csv(cloze_path, cloze_notes)

    print(f"Wrote {seq_path} ({len(seq_notes)} notes)")
    print(f"Wrote {cloze_path} ({len(cloze_notes)} notes)")
    return 0


def cmd_build_all(args: argparse.Namespace) -> int:
    ps = get_parashot()

    all_seq = []
    all_cloze = []

    if args.limit is not None:
        ps = ps[: args.limit]

    for p in ps:
        seq_notes = build_sequence_notes(p, get_text_range)
        cloze_notes = build_cloze_notes_for_parasha(p, get_verses_for_ref_range)
        all_seq.extend(seq_notes)
        all_cloze.extend(cloze_notes)

        if not args.quiet:
            print(f"{p['parasha']}: +{len(seq_notes)} seq, +{len(cloze_notes)} cloze")

    seq_path = f"out/{args.out_prefix}.sequence.csv"
    cloze_path = f"out/{args.out_prefix}.cloze.csv"

    write_sequence_csv(seq_path, all_seq)
    write_cloze_csv(cloze_path, all_cloze)

    if not args.quiet:
        print(f"Wrote {seq_path} ({len(all_seq)} notes)")
        print(f"Wrote {cloze_path} ({len(all_cloze)} notes)")

    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="anki_torah", description="Generate Anki CSVs for Torah memorization."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List parashah names.")
    p_list.set_defaults(func=cmd_list)

    p_build = sub.add_parser(
        "build", help="Build CSVs for a parashah (cloze + sequence)."
    )
    p_build.add_argument(
        "parasha", help="Parashah name (e.g., Bereshit, Noach, Lech-Lecha)."
    )
    p_build.add_argument(
        "--out-prefix", help="Override output filename prefix (default: parashah name)."
    )
    p_build.set_defaults(func=cmd_build)

    p_build_all = sub.add_parser(
        "build-all", help="Build combined CSVs for all parashot."
    )
    p_build_all.add_argument(
        "--out-prefix", default="ALL", help="Output filename prefix (default: ALL)."
    )
    p_build_all.add_argument(
        "--limit", type=int, help="Only build the first N parashot (for testing)."
    )
    p_build_all.add_argument(
        "--quiet", action="store_true", help="Suppress per-parashah output."
    )
    p_build_all.set_defaults(func=cmd_build_all)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
