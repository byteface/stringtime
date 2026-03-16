#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stringtime.variant_sweeps import DEFAULT_REFERENCE, write_ladder_failures


def main():
    output_path = Path("data/ladder_variant_failures.json")
    result = write_ladder_failures(output_path, reference=DEFAULT_REFERENCE)
    print(f"Reference: {result['reference']}")
    print(f"Seeds: {result['seed_count']}")
    print(f"Supported: {result['supported_count']}")
    print(f"Exploratory: {result['exploratory_count']}")
    print(f"Written: {output_path}")


if __name__ == "__main__":
    main()
