#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stringtime.variant_sweeps import DEFAULT_REFERENCE, write_variant_failures


def main():
    output_path = Path("data/variant_failures.json")
    result = write_variant_failures(output_path, reference=DEFAULT_REFERENCE)
    print(f"Reference: {result['reference']}")
    print(f"Seeds: {result['seed_count']}")
    print(f"Variants: {result['variant_count']}")
    print(f"Failures: {result['failure_count']}")
    print(f"Written: {output_path}")


if __name__ == "__main__":
    main()
