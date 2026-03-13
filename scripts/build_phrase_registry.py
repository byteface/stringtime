#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stringtime.phrase_registry import DEFAULT_REFERENCE, build_registry


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a phrase registry and reverse phrase map for stringtime."
    )
    parser.add_argument(
        "--relative-to",
        default=DEFAULT_REFERENCE,
        help="Reference datetime used to make relative phrase expansion deterministic.",
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Directory to write registry files into.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    result = build_registry(relative_to=args.relative_to)

    write_json(output_dir / "phrase_registry.json", result)
    write_json(output_dir / "phrase_reverse_map.json", result["reverse_map"])
    write_json(output_dir / "phrase_reverse_records.json", result["reverse_records"])
    write_json(output_dir / "phrase_registry_failures.json", result["failures"])

    print(
        "Generated phrase registry:",
        result["summary"]["phrase_count"],
        "phrases,",
        result["summary"]["successful_phrase_count"],
        "strict parses,",
        result["summary"]["distinct_datetime_count"],
        "distinct datetimes",
    )
    if result["summary"]["failed_phrase_count"]:
        print("Failures written to", output_dir / "phrase_registry_failures.json")


if __name__ == "__main__":
    main()
