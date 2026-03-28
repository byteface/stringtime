import pytest

from tests.stringtime_cases import TestCaseStrict as StrictCases

pytestmark = [pytest.mark.parser, pytest.mark.regression]


class TestCaseStrict:
    test_assert_phrases = StrictCases.test_assert_phrases
    test_assert_dates = StrictCases.test_assert_dates
    test_assert_DEBUG_OFF = StrictCases.test_assert_DEBUG_OFF
    test_present = StrictCases.test_present
    test_timezone_aware_output_utc = StrictCases.test_timezone_aware_output_utc
    test_timezone_aware_output_named_zone = StrictCases.test_timezone_aware_output_named_zone
    test_timezone_aware_output_with_offset_suffix = (
        StrictCases.test_timezone_aware_output_with_offset_suffix
    )
    test_relative_to_string_changes_reference_now = (
        StrictCases.test_relative_to_string_changes_reference_now
    )
    test_relative_to_datetime_changes_reference_now = (
        StrictCases.test_relative_to_datetime_changes_reference_now
    )
    test_relative_to_applies_to_sentence_extraction = (
        StrictCases.test_relative_to_applies_to_sentence_extraction
    )
    test_empty_string_uses_relative_to_reference = (
        StrictCases.test_empty_string_uses_relative_to_reference
    )
    test_sleeps_until_christmas = StrictCases.test_sleeps_until_christmas
    test_parse_metadata_for_exact_parser_match = (
        StrictCases.test_parse_metadata_for_exact_parser_match
    )
    test_parse_metadata_for_dateutil_fallback = (
        StrictCases.test_parse_metadata_for_dateutil_fallback
    )
    test_parse_metadata_for_extracted_match = (
        StrictCases.test_parse_metadata_for_extracted_match
    )
    test_parse_metadata_marks_day_phrase_as_period = (
        StrictCases.test_parse_metadata_marks_day_phrase_as_period
    )
    test_parse_metadata_marks_boundary_phrase = (
        StrictCases.test_parse_metadata_marks_boundary_phrase
    )
    test_parse_metadata_marks_part_of_day_phrase = (
        StrictCases.test_parse_metadata_marks_part_of_day_phrase
    )
