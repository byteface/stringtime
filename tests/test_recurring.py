import pytest

from tests.stringtime_cases import (
    test_recurring_schedule_advanced_extracts_full_phrase,
    test_recurring_schedule_advanced_metadata,
    test_recurring_schedule_advanced_phrases_parse,
    test_recurring_schedule_extended_phrases_parse,
    test_recurring_schedule_extracts_full_phrase,
    test_recurring_schedule_handles_common_aliases_and_case,
    test_recurring_schedule_metadata_stays_recurring,
    test_recurring_schedule_starter_phrases_parse,
    test_recurring_weekday_parses_and_marks_metadata,
    test_recurring_weekday_with_time_keeps_recurring_metadata,
)

pytestmark = [pytest.mark.recurring]
