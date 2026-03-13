from __future__ import annotations

import argparse
import sys
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from cif_engine import run_situation, summarize_mood, summarize_pair
from cif_situations import SITUATIONS


def print_transcript(result) -> None:
    print(f"\n=== {result.situation_id} ===")
    for turn in result.transcript:
        print(
            f"Turn {turn['turn']}: {turn['initiator']} -> {turn['responder']} | "
            f"{turn['exchange']} | {turn['outcome']} | {turn['line']}"
        )
        print(
            f"  volition={turn['volition']} ({', '.join(turn['volition_reasons']) or 'no rules'}) | "
            f"acceptance={turn['acceptance']} ({', '.join(turn['acceptance_reasons']) or 'no rules'})"
        )
        if turn["changes"]:
            print(f"  changes: {', '.join(turn['changes'])}")
        if turn["trigger_notes"]:
            print(f"  triggers: {', '.join(turn['trigger_notes'])}")


def print_summary(result) -> None:
    situation = SITUATIONS[result.situation_id]
    print(f"\n=== {situation.id} ===")
    print(situation.description)
    print(f"Exchange counts: {result.exchange_counts}")
    for character in situation.characters:
        print(f"  {summarize_mood(result.final_state, character.name)}")
    names = [character.name for character in situation.characters]
    for initiator in names:
        for responder in names:
            if initiator == responder:
                continue
            print(f"  {summarize_pair(result.final_state, initiator, responder)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run self-contained CiF experiment situations.")
    parser.add_argument("--list", action="store_true", help="List available situation ids.")
    parser.add_argument("--situation", action="append", help="Run one or more specific situations.")
    parser.add_argument("--transcript", action="store_true", help="Print full transcript output.")
    args = parser.parse_args(argv)

    if args.list:
        for situation_id in SITUATIONS:
            print(situation_id)
        return 0

    selected = args.situation or list(SITUATIONS)
    for situation_id in selected:
        result = run_situation(SITUATIONS[situation_id])
        if args.transcript:
            print_transcript(result)
        print_summary(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
