"""Compare finished runs: solve rate against token spend, per arm."""

from __future__ import annotations

import argparse
from pathlib import Path

from agents_who_mean_well.metrics import compare, load_summary


def main() -> None:
    """Print the comparison table for every run file given."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "runs", type=Path, nargs="*", help="Run files; default runs/*.jsonl"
    )
    args = parser.parse_args()

    paths = args.runs or sorted(Path("runs").glob("*.jsonl"))
    print(compare([load_summary(path) for path in paths]))


if __name__ == "__main__":
    main()
