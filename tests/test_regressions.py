import pytest
import stringtime

from tests.stringtime_cases import (
    test_anchor_offset_on_holiday_anchor,
    test_builtin_holiday_catalog_is_large,
    test_custom_holiday_registration_supports_fixed_and_year_specific_sources,
    test_end_of_play_with_composed_anchor_and_precise_seconds_tail,
    test_month_boundary_and_year_position_compositions,
    test_recent_composition_regression_extraction_spans,
    test_recent_composition_regressions,
    test_relative_named_month_day_with_time,
)

pytestmark = [pytest.mark.regression]


def test_relative_day_timestamp_grammar_extensions():
    assert str(stringtime.Date("today 17:52:10")) == "2020-12-25 17:52:10"
    assert str(stringtime.Date("tomorrow 17:52:10")) == "2020-12-26 17:52:10"
    assert str(stringtime.Date("yesterday 17:52:10")) == "2020-12-24 17:52:10"
    assert (
        str(stringtime.Date("before yesterday at 17:52"))
        == "2020-12-23 17:52:00"
    )
    assert str(stringtime.Date("before yesterday 5pm")) == "2020-12-23 17:00:00"
    assert str(stringtime.Date("before yesterday 17:52:10")) == "2020-12-23 17:52:10"
    assert (
        str(stringtime.Date("after tomorrow at 17:52:10"))
        == "2020-12-27 17:52:10"
    )
    assert str(stringtime.Date("after tomorrow 5pm")) == "2020-12-27 17:00:00"
    assert str(stringtime.Date("after tomorrow 17:52:10")) == "2020-12-27 17:52:10"
    assert str(stringtime.Date("@2")) == "2020-12-25 02:00:00"
    assert str(stringtime.Date("@ 2pm")) == "2020-12-25 14:00:00"


def test_forward_anchor_offset_grammar_extensions():
    assert str(stringtime.Date("2 days after tomorrow")) == "2020-12-28 17:05:55"
    assert str(stringtime.Date("2 days after before yesterday")) == "2020-12-25 17:05:55"


def test_period_anchor_and_anchor_offset_grammar_extensions():
    assert str(stringtime.Date("this month 5pm")) == "2020-12-25 17:00:00"
    assert str(stringtime.Date("this year 5pm")) == "2020-12-25 17:00:00"
    assert str(stringtime.Date("this week 17:52")) == "2020-12-25 17:52:00"
    assert str(stringtime.Date("next week 5pm")) == "2021-01-01 17:00:00"
    assert str(stringtime.Date("next week 17:52")) == "2021-01-01 17:52:00"
    assert str(stringtime.Date("last week 5pm")) == "2020-12-18 17:00:00"
    assert str(stringtime.Date("last week 17:52")) == "2020-12-18 17:52:00"
    assert str(stringtime.Date("this month at 5pm")) == "2020-12-25 17:00:00"
    assert str(stringtime.Date("this year at 5pm")) == "2020-12-25 17:00:00"
    assert str(stringtime.Date("next month at 5pm")) == "2021-01-25 17:00:00"
    assert str(stringtime.Date("next year at 5pm")) == "2021-12-25 17:00:00"
    assert (
        str(stringtime.Date("1 day and 2 hours after tomorrow"))
        == "2020-12-27 19:05:55"
    )
    assert (
        str(stringtime.Date("1 day and a half after tomorrow"))
        == "2020-12-28 05:05:55"
    )


def test_recurring_grammar_token_extensions():
    friday_from_next_week = stringtime.Date("every friday from next week")
    assert str(friday_from_next_week) == "2021-01-01 17:05:55"
    assert friday_from_next_week.parse_metadata.semantic_kind == "recurring"
    assert friday_from_next_week.parse_metadata.recurrence_start == "next week"

    excluded = stringtime.Date("every weekday except friday at 9am")
    assert str(excluded) == "2020-12-28 09:00:00"
    assert excluded.parse_metadata.semantic_kind == "recurring"

    bounded = stringtime.Date("every monday through june")
    assert str(bounded) == "2020-12-28 17:05:55"
    assert bounded.parse_metadata.semantic_kind == "recurring"


def test_relative_offset_and_anchor_offset_grammar_extensions():
    assert str(stringtime.Date("a minute ago")) == "2020-12-25 17:04:55"
    assert str(stringtime.Date("a minute hence")) == "2020-12-25 17:06:55"
    assert str(stringtime.Date("a minute from now")) == "2020-12-25 17:06:55"
    assert str(stringtime.Date("a minute ago at 5pm")) == "2020-12-25 17:00:00"
    assert str(stringtime.Date("a day before tomorrow")) == "2020-12-25 17:05:55"
    assert str(stringtime.Date("a day after tomorrow")) == "2020-12-27 17:05:55"


def test_composed_date_time_grammar_extensions():
    assert str(stringtime.Date("wednesday 5pm")) == "2020-12-30 17:00:00"
    assert str(stringtime.Date("5pm wednesday")) == "2020-12-30 17:00:00"
    assert str(stringtime.Date("5pm on wednesday")) == "2020-12-30 17:00:00"
