import datetime
from pathlib import Path

from stringtime import Phrase, nearest_phrase_for, nearest_phrases_for, phrase_for, phrases_for
from scripts.build_phrase_registry import build_registry
from stringtime.phrase_registry import generate_phrase_records


def test_phrase_registry_has_no_duplicate_phrases():
    records = generate_phrase_records()
    phrases = [record["phrase"] for record in records]

    assert len(phrases) == len(set(phrases))


def test_phrase_registry_includes_expected_variants():
    phrases = {record["phrase"] for record in generate_phrase_records()}

    assert "end of the month" in phrases
    assert "start of the next quarter" in phrases
    assert "half five" in phrases
    assert "in a fortnight" in phrases
    assert "next tuesday evening" in phrases
    assert "tomorrow at 5pm utc" in phrases


def test_phrase_registry_records_include_metadata():
    record = next(
        entry for entry in generate_phrase_records() if entry["phrase"] == "half five"
    )

    assert record["locale"] == "en-GB"
    assert record["style"] == "colloquial"
    assert record["semantic_kind"] == "instant"
    assert record["representative_granularity"] == "minute"
    assert record["is_canonical"] is True
    assert "clock_phrase" in record["tags"]


def test_phrase_registry_marks_day_phrases_as_periods():
    record = next(
        entry for entry in generate_phrase_records() if entry["phrase"] == "monday"
    )

    assert record["semantic_kind"] == "period"
    assert record["representative_granularity"] == "day"


def test_build_registry_creates_canonical_reverse_records():
    result = build_registry("2020-12-25 17:05:55")

    reverse_entry = result["reverse_map"]["2021-01-01 17:05:55"]
    assert reverse_entry["canonical_phrase"] in reverse_entry["phrases"]
    assert "start of next quarter" in reverse_entry["phrases"]
    assert "start of the next quarter" in reverse_entry["phrases"]

    detailed_entry = next(
        entry
        for entry in result["reverse_records"]
        if entry["parsed"] == "2021-01-01 17:05:55"
    )
    assert detailed_entry["phrase_count"] >= 3
    assert detailed_entry["canonical_style"] in detailed_entry["styles"]
    assert "boundary" in detailed_entry["categories"]
    assert "boundary" in detailed_entry["semantic_kinds"]


def test_registry_builder_script_is_importable():
    assert Path("scripts/build_phrase_registry.py").exists()


def test_phrase_for_returns_canonical_phrase_for_datetime():
    dt = datetime.datetime(2021, 1, 1, 17, 5, 55)

    assert phrase_for(dt, relative_to="2020-12-25 17:05:55") == "start of next quarter"
    assert Phrase(dt, relative_to="2020-12-25 17:05:55") == "start of next quarter"


def test_phrases_for_returns_all_known_variants_for_datetime():
    dt = datetime.datetime(2021, 1, 1, 17, 5, 55)

    phrases = phrases_for(dt, relative_to="2020-12-25 17:05:55")

    assert "start of next quarter" in phrases
    assert "start of the next quarter" in phrases
    assert "first day of next quarter" in phrases


def test_phrase_for_returns_none_when_no_exact_registry_match():
    dt = datetime.datetime(2037, 6, 1, 12, 34, 56)

    assert phrase_for(dt, relative_to="2020-12-25 17:05:55") is None
    assert phrases_for(dt, relative_to="2020-12-25 17:05:55") == []


def test_nearest_phrase_for_returns_closest_known_phrase():
    dt = datetime.datetime(2021, 1, 1, 12, 34, 56)

    assert nearest_phrase_for(dt, relative_to="2020-12-25 17:05:55") == "start of next quarter"


def test_nearest_phrases_for_returns_ranked_candidates():
    dt = datetime.datetime(2037, 6, 1, 12, 34, 56)

    candidates = nearest_phrases_for(dt, relative_to="2020-12-25 17:05:55", limit=3)

    assert len(candidates) == 3
    assert candidates[0].delta_seconds <= candidates[1].delta_seconds
    assert all(candidate.phrase for candidate in candidates)
