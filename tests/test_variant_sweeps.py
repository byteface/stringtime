import pytest
from pathlib import Path

from stringtime.variant_sweeps import (DEFAULT_REFERENCE,
                                       generate_extraction_cases,
                                       generate_variant_cases,
                                       run_exploratory_structure_sweep,
                                       run_extraction_sweep, run_ladder_sweep,
                                       run_range_glue_sweep, run_variant_sweep)

pytestmark = [pytest.mark.variant, pytest.mark.slow]


def test_variant_sweeps_generate_at_least_one_hundred_cases():
    cases = generate_variant_cases()

    assert len(cases) >= 180


def test_variant_sweeps_include_expected_families():
    cases = generate_variant_cases()
    phrases = {case.phrase.lower() for case in cases}

    assert "tomorrow night" in phrases
    assert "2moro night" in phrases
    assert "end of the month" in phrases
    assert "the first day of october" in phrases
    assert "the first day in october" in phrases
    assert "first monday of may" in phrases
    assert "by tomorrow noon" in phrases
    assert "from the next wednesday" in phrases
    assert any("valentine's day" in phrase for phrase in phrases)
    assert "t minus 5 minutes" in phrases
    assert "the last tuesday before the end of last autumn" in phrases
    assert "2 fridays after spring equinox" in phrases
    assert "a week before xmas" in phrases
    assert "5pm on friday before xmas" in phrases
    assert "the first business day after fiscal year end" in phrases
    assert "noon on 3 days after start of week" in phrases
    assert "5pm on friday before the twelfth month" in phrases
    assert "10 seconds to midnight on the first monday in may" in phrases
    assert "the middle of september at 10 seconds to midnight" in phrases
    assert "last september 22nd at 3:30pm" in phrases
    assert "last september 22nd @ 3:30 pm" in phrases
    assert "end of play tuesday in feb" in phrases
    assert "close of play tuesday in feb" in phrases
    assert (
        "2028 at 3pm on boxing day" in phrases
        or "2028 at 3pm on boxing day 2028" in phrases
    )
    assert "at 4pm on the first friday of june 2028" in phrases
    assert (
        "the first friday of june 2028 at 4pm" in phrases
        or "the first friday of june 2028 @ 4pm" in phrases
    )
    assert "the first monday of may" in phrases
    assert "in 3 days from next wednesday" in phrases
    assert (
        "evening on fiscal year end" in phrases
        or "in the evening on fiscal year end" in phrases
    )
    assert "the first working day after fiscal year end" in phrases
    assert "quarter past five" in phrases
    assert "the 1st of the 3rd 22 @ 3pm" in phrases


def test_variant_sweep_report_shape():
    report = run_variant_sweep(reference=DEFAULT_REFERENCE)

    assert report["seed_count"] > 0
    assert report["variant_count"] >= 180
    assert report["failure_count"] >= 0
    assert isinstance(report["failures"], list)


def test_variant_sweep_script_exists():
    assert Path("scripts/find_variant_failures.py").exists()


def test_extraction_variant_sweeps_generate_many_cases():
    cases = generate_extraction_cases()

    assert len(cases) >= 700


def test_extraction_variant_sweep_report_shape():
    report = run_extraction_sweep(reference=DEFAULT_REFERENCE)

    assert report["seed_count"] > 0
    assert report["extraction_variant_count"] >= 500
    assert report["failure_count"] >= 0
    assert isinstance(report["failures"], list)


def test_extraction_variant_sweep_script_exists():
    assert Path("scripts/find_extraction_variant_failures.py").exists()


def test_range_glue_sweep_report_shape():
    report = run_range_glue_sweep(reference=DEFAULT_REFERENCE)

    assert report["seed_count"] >= 10
    assert report["supported_count"] >= 0
    assert report["unsupported_count"] >= 0
    assert isinstance(report["results"], list)


def test_range_glue_sweep_script_exists():
    assert Path("scripts/find_range_variant_failures.py").exists()


def test_ladder_sweep_report_shape():
    report = run_ladder_sweep(reference=DEFAULT_REFERENCE)

    assert report["seed_count"] >= 35
    assert report["supported_count"] >= 0
    assert report["exploratory_count"] >= 0
    assert isinstance(report["results"], list)


def test_ladder_sweep_script_exists():
    assert Path("scripts/find_ladder_variant_failures.py").exists()


def test_exploratory_structure_sweep_report_shape():
    report = run_exploratory_structure_sweep(reference=DEFAULT_REFERENCE)

    assert report["seed_count"] >= 6
    assert report["exact_count"] >= 0
    assert report["non_exact_count"] >= 0
    assert isinstance(report["results"], list)


def test_exploratory_structure_sweep_script_exists():
    assert Path("scripts/find_exploratory_structure_failures.py").exists()
