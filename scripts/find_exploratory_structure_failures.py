#!/usr/bin/env python3

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stringtime.variant_sweeps import (  # noqa: E402
    DEFAULT_REFERENCE,
    write_exploratory_structure_failures,
)


def main():
    output_path = Path("data/exploratory_structure_failures.json")
    result = write_exploratory_structure_failures(
        output_path, reference=DEFAULT_REFERENCE
    )
    print(f"Reference: {result['reference']}")
    print(f"Seeds: {result['seed_count']}")
    print(f"Exact: {result['exact_count']}")
    print(f"Non-exact: {result['non_exact_count']}")
    print(f"Written: {output_path}")


if __name__ == "__main__":
    main()
