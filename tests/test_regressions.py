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


def test_strtotime_style_offsets_and_year_shorthands():
    assert str(stringtime.Date("back in 82")) == "1982-01-01 17:05:55"
    assert str(stringtime.Date("back in 08")) == "2008-01-01 17:05:55"
    assert (
        str(stringtime.Date("+1 week 2 days 4 hours 2 seconds"))
        == "2021-01-03 21:05:57"
    )
    assert (
        str(stringtime.Date("1 week 2 days 4 hours 2 seconds ago"))
        == "2020-12-16 13:05:53"
    )
    assert str(stringtime.Date("20080229")) == "2008-02-29 17:05:55"
    assert str(stringtime.Date("20080229 -1 year")) == "2007-02-28 17:05:55"
    assert str(stringtime.Date("20080229 +1 year")) == "2009-02-28 17:05:55"
    assert (
        str(stringtime.Date("+1 week, 2 days, 4 hours, 2 seconds"))
        == "2021-01-03 21:05:57"
    )
    assert (
        str(stringtime.Date("+1 week +2 days +4 hours +2 seconds"))
        == "2021-01-03 21:05:57"
    )
    assert str(stringtime.Date("1 week, 2 days ago")) == "2020-12-16 17:05:55"
    assert str(stringtime.Date("2008-02-29 -1 year")) == "2007-02-28 17:05:55"


def test_compound_offsets_do_not_leak_recurring_metadata():
    parsed = stringtime.Date("1 week and 2 days and 4 hours from now")

    assert str(parsed) == "2021-01-03 21:05:55"
    assert parsed.parse_metadata.semantic_kind == "relative_offset"


def test_compound_offsets_accept_stuck_together_units():
    parsed = stringtime.Date("2 years, 6months and 3 days")

    assert str(parsed) == "2023-06-28 17:05:55"
    assert parsed.parse_metadata.semantic_kind == "relative_offset"


def test_compound_offsets_accept_internal_plus_separator():
    parsed = stringtime.Date("2 years, 6months and 3 days plus 1 hour")

    assert str(parsed) == "2023-06-28 18:05:55"
    assert parsed.parse_metadata.semantic_kind == "relative_offset"


def test_recent_manual_breakages_are_pinned():
    assert (
        str(stringtime.Date("4 days before the end of next month"))
        == "2021-01-27 17:05:55"
    )
    assert (
        str(stringtime.Date("the fourteenth week after xmas"))
        == "2021-04-02 17:05:55"
    )
    assert (
        str(stringtime.Date("the last thursday in june 22"))
        == "2022-06-30 17:05:55"
    )
    assert str(stringtime.Date("the summer of 69")) == "1969-06-01 17:05:55"
    assert str(stringtime.Date("the night after xmas")) == "2020-12-26 21:00:00"
    assert str(stringtime.Date("5yrs ago")) == "2015-12-25 17:05:55"
    assert str(stringtime.Date("2yrs from now")) == "2022-12-25 17:05:55"


def test_compound_offsets_accept_internal_minus_separator():
    parsed = stringtime.Date("2 years, 6months and 3 days minus 1 hour")

    assert str(parsed) == "2023-06-28 16:05:55"
    assert parsed.parse_metadata.semantic_kind == "relative_offset"


def test_offset_tails_apply_to_general_base_phrases():
    tomorrow = stringtime.Date(
        "tomorrow minus 1 hour", relative_to="2020-12-25 17:05:55"
    )
    next_friday = stringtime.Date(
        "next friday plus 2 days", relative_to="2020-12-25 17:05:55"
    )
    first_monday = stringtime.Date(
        "the first monday in june minus 3 hours",
        relative_to="2020-12-25 17:05:55",
    )

    assert str(tomorrow) == "2020-12-26 16:05:55"
    assert tomorrow.parse_metadata.semantic_kind == "relative_offset"

    assert str(next_friday) == "2021-01-03 17:05:55"
    assert next_friday.parse_metadata.semantic_kind == "relative_offset"

    assert str(first_monday) == "2020-06-01 14:05:55"
    assert first_monday.parse_metadata.semantic_kind == "relative_offset"


def test_nested_ordinal_time_coordinate_regressions():
    minute_anchor = stringtime.Date(
        "the 14th minute on the 2nd week of the first month 2321"
    )
    second_anchor = stringtime.Date(
        "the twelth second of the 14th minute on the 2nd week of the first month 2321"
    )
    day_before = stringtime.Date(
        "the day before the twelth second of the 14th minute on the 2nd week of the first month 2321"
    )

    assert str(minute_anchor) == "2321-01-08 17:14:00"
    assert str(second_anchor) == "2321-01-08 17:14:12"
    assert str(day_before) == "2321-01-07 17:14:12"


def test_nested_ordinal_time_coordinate_accepts_offset_tail():
    parsed = stringtime.Date(
        "the day before the twelth second of the 14th minute on the 2nd week of the first month 2321 plus 1 hour"
    )

    assert str(parsed) == "2321-01-07 18:14:12"
    assert parsed.parse_metadata.semantic_kind == "relative_offset"


def test_explicit_year_week_of_month_does_not_roll_forward():
    parsed = stringtime.Date(
        "1992 on the 2nd week of the 7th month",
        relative_to="2020-12-25 17:05:55",
    )

    assert str(parsed) == "1992-07-08 17:05:55"


def test_explicit_year_anchor_family_stays_in_year_and_keeps_tail():
    month_anchor = stringtime.Date(
        "the twelfth month 1992",
        relative_to="2020-12-25 17:05:55",
    )
    ordinal_weekday = stringtime.Date(
        "the first monday in june 1992",
        relative_to="2020-12-25 17:05:55",
    )
    anchored_tail = stringtime.Date(
        "the day before the first monday in june 1992 plus 1 hour",
        relative_to="2020-12-25 17:05:55",
    )

    assert str(month_anchor) == "1992-12-01 17:05:55"
    assert str(ordinal_weekday) == "1992-06-01 17:05:55"
    assert str(anchored_tail) == "1992-05-31 18:05:55"
    assert anchored_tail.parse_metadata.semantic_kind == "relative_offset"


def test_anchor_comma_offset_list_parses_from_explicit_year():
    parsed = stringtime.Date(
        "1998, 2mins, 20 secs plus 1 hour",
        relative_to="2020-12-25 17:05:55",
    )

    assert str(parsed) == "1998-01-01 18:08:15"
    assert parsed.parse_metadata.semantic_kind == "relative_offset"


def test_missing_reasonable_shapes_are_now_supported():
    expectations = {
        "the weekend after next": "2021-01-02 17:05:55",
        "the month after next": "2021-02-25 17:05:55",
        "the year after next": "2022-12-25 17:05:55",
        "the last week of next month": "2021-01-25 17:05:55",
        "the second half of next year": "2021-07-01 17:05:55",
        "the first half of 2027": "2027-01-01 17:05:55",
        "the morning after christmas": "2020-12-26 09:00:00",
        "the evening before halloween": "2020-10-30 19:00:00",
        "in 1w2d": "2021-01-03 17:05:55",
        "+1w2d4h": "2021-01-03 21:05:55",
        "two fortnights ago": "2020-11-27 17:05:55",
        "three quarters of an hour from now": "2020-12-25 17:50:55",
    }

    for phrase, expected in expectations.items():
        parsed = stringtime.Date(phrase, relative_to="2020-12-25 17:05:55")
        assert str(parsed) == expected, phrase

    monthly_recurring = stringtime.Date(
        "every last friday of the month",
        relative_to="2020-12-25 17:05:55",
    )
    quarterly_recurring = stringtime.Date(
        "every first business day of the quarter",
        relative_to="2020-12-25 17:05:55",
    )

    assert str(monthly_recurring) == "2021-01-29 17:05:55"
    assert monthly_recurring.parse_metadata.semantic_kind == "recurring"
    assert str(quarterly_recurring) == "2021-01-01 17:05:55"
    assert quarterly_recurring.parse_metadata.semantic_kind == "recurring"


def test_fractional_and_short_duration_offsets_are_supported():
    expectations = {
        "quarter of an hour": "2020-12-25 17:20:55",
        "an hour and a half away": "2020-12-25 18:35:55",
        "3 quarters of an hour ago": "2020-12-25 16:20:55",
        "3/4 of an hour": "2020-12-25 17:50:55",
        "1/4 of an hour": "2020-12-25 17:20:55",
        "half a year ago": "2020-06-25 17:05:55",
        "in a min": "2020-12-25 17:06:55",
    }

    for phrase, expected in expectations.items():
        parsed = stringtime.Date(phrase, relative_to="2020-12-25 17:05:55")
        assert str(parsed) == expected, phrase
        assert parsed.parse_metadata.semantic_kind == "relative_offset", phrase


def test_slash_dates_are_parsed_natively_and_date_order_is_configurable():
    uk_short = stringtime.Date("26/7/99", relative_to="2020-12-25 17:05:55")
    uk_time = stringtime.Date("26/7/2027 at 2pm", relative_to="2020-12-25 17:05:55")
    impossible_mdy = stringtime.Date(
        "26/7/99", relative_to="2020-12-25 17:05:55", date_order="mdy"
    )
    impossible_dmy = stringtime.Date(
        "7/26/99", relative_to="2020-12-25 17:05:55", date_order="dmy"
    )
    us_ambiguous = stringtime.Date(
        "7/8/99", relative_to="2020-12-25 17:05:55", date_order="mdy"
    )
    gb_ambiguous = stringtime.Date(
        "7/8/99", relative_to="2020-12-25 17:05:55", date_order="dmy"
    )

    assert str(uk_short) == "1999-07-26 17:05:55"
    assert uk_short.parse_metadata.used_dateutil is False
    assert str(uk_time) == "2027-07-26 14:00:00"
    assert uk_time.parse_metadata.used_dateutil is False
    assert str(impossible_mdy) == "1999-07-26 17:05:55"
    assert impossible_mdy.parse_metadata.used_dateutil is False
    assert str(impossible_dmy) == "1999-07-26 17:05:55"
    assert impossible_dmy.parse_metadata.used_dateutil is False
    assert str(us_ambiguous) == "1999-07-08 17:05:55"
    assert us_ambiguous.parse_metadata.used_dateutil is False
    assert str(gb_ambiguous) == "1999-08-07 17:05:55"
    assert gb_ambiguous.parse_metadata.used_dateutil is False
