from pathlib import Path

from stringtime.variant_sweeps import (
    DEFAULT_REFERENCE,
    generate_extraction_cases,
    generate_variant_cases,
    run_extraction_sweep,
    run_variant_sweep,
)


def test_variant_sweeps_generate_at_least_one_hundred_cases():
    cases = generate_variant_cases()

    assert len(cases) >= 80


def test_variant_sweeps_include_expected_families():
    cases = generate_variant_cases()
    phrases = {case.phrase.lower() for case in cases}

    assert "tomorrow night" in phrases
    assert "2moro night" in phrases
    assert "end of the month" in phrases
    assert any("valentine's day" in phrase for phrase in phrases)
    assert "t minus 5 minutes" in phrases


def test_variant_sweep_report_shape():
    report = run_variant_sweep(reference=DEFAULT_REFERENCE)

    assert report["seed_count"] > 0
    assert report["variant_count"] >= 80
    assert report["failure_count"] >= 0
    assert isinstance(report["failures"], list)


def test_variant_sweep_script_exists():
    assert Path("scripts/find_variant_failures.py").exists()


def test_extraction_variant_sweeps_generate_many_cases():
    cases = generate_extraction_cases()

    assert len(cases) >= 200


def test_extraction_variant_sweep_report_shape():
    report = run_extraction_sweep(reference=DEFAULT_REFERENCE)

    assert report["seed_count"] > 0
    assert report["extraction_variant_count"] >= 200
    assert report["failure_count"] >= 0
    assert isinstance(report["failures"], list)


def test_extraction_variant_sweep_script_exists():
    assert Path("scripts/find_extraction_variant_failures.py").exists()
