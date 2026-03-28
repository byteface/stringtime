import pytest

from tests.stringtime_cases import TestCaseStrict as StrictCases

pytestmark = [pytest.mark.parser, pytest.mark.regression]


class TestCaseExtract:
    test_extract_dates_single_phrase_from_sentence = (
        StrictCases.test_extract_dates_single_phrase_from_sentence
    )
    test_extract_dates_prefers_full_anchor_offset_phrase = (
        StrictCases.test_extract_dates_prefers_full_anchor_offset_phrase
    )
    test_extract_dates_prefers_full_anchor_offset_phrase_with_alias = (
        StrictCases.test_extract_dates_prefers_full_anchor_offset_phrase_with_alias
    )
    test_extract_dates_prefers_full_compound_anchor_offset_phrase = (
        StrictCases.test_extract_dates_prefers_full_compound_anchor_offset_phrase
    )
    test_extract_dates_prefers_full_compound_anchor_offset_phrase_with_year = (
        StrictCases.test_extract_dates_prefers_full_compound_anchor_offset_phrase_with_year
    )
    test_extract_dates_prefers_full_relative_phrase_with_specific_morning_time = (
        StrictCases.test_extract_dates_prefers_full_relative_phrase_with_specific_morning_time
    )
    test_extract_dates_prefers_full_before_midnight_phrase = (
        StrictCases.test_extract_dates_prefers_full_before_midnight_phrase
    )
    test_extract_dates_prefers_full_clock_strikes_anchor_phrase = (
        StrictCases.test_extract_dates_prefers_full_clock_strikes_anchor_phrase
    )
    test_extract_dates_prefers_full_relative_weekday_phrase = (
        StrictCases.test_extract_dates_prefers_full_relative_weekday_phrase
    )
    test_extract_dates_handles_compact_offset_tokens = (
        StrictCases.test_extract_dates_handles_compact_offset_tokens
    )
    test_extract_dates_handles_compact_offset_directional_phrases = (
        StrictCases.test_extract_dates_handles_compact_offset_directional_phrases
    )
    test_extract_dates_prefers_full_anchor_offset_with_article = (
        StrictCases.test_extract_dates_prefers_full_anchor_offset_with_article
    )
    test_extract_dates_prefers_full_couple_anchor_offset_phrase = (
        StrictCases.test_extract_dates_prefers_full_couple_anchor_offset_phrase
    )
    test_extract_dates_prefers_full_today_minus_phrase = (
        StrictCases.test_extract_dates_prefers_full_today_minus_phrase
    )
    test_extract_dates_prefers_full_now_take_away_phrase = (
        StrictCases.test_extract_dates_prefers_full_now_take_away_phrase
    )
    test_extract_dates_prefers_full_give_or_take_phrase = (
        StrictCases.test_extract_dates_prefers_full_give_or_take_phrase
    )
    test_extract_dates_prefers_full_by_tomorrow_noon_phrase = (
        StrictCases.test_extract_dates_prefers_full_by_tomorrow_noon_phrase
    )
    test_extract_dates_prefers_full_as_of_tomorrow_phrase = (
        StrictCases.test_extract_dates_prefers_full_as_of_tomorrow_phrase
    )
    test_extract_dates_prefers_full_on_next_weekday_phrase = (
        StrictCases.test_extract_dates_prefers_full_on_next_weekday_phrase
    )
    test_extract_dates_prefers_full_in_month_phrase = (
        StrictCases.test_extract_dates_prefers_full_in_month_phrase
    )
    test_extract_dates_prefers_full_at_noon_phrase = (
        StrictCases.test_extract_dates_prefers_full_at_noon_phrase
    )
    test_extract_dates_prefers_full_from_next_weekday_phrase = (
        StrictCases.test_extract_dates_prefers_full_from_next_weekday_phrase
    )
    test_extract_dates_prefers_full_ordinal_month_anchor_phrase = (
        StrictCases.test_extract_dates_prefers_full_ordinal_month_anchor_phrase
    )
    test_extract_dates_prefers_full_middle_of_month_anchor_phrase = (
        StrictCases.test_extract_dates_prefers_full_middle_of_month_anchor_phrase
    )
    test_extract_dates_prefers_full_ordinal_holiday_offset_phrase = (
        StrictCases.test_extract_dates_prefers_full_ordinal_holiday_offset_phrase
    )
    test_extract_dates_prefers_full_week_of_month_anchor_phrase = (
        StrictCases.test_extract_dates_prefers_full_week_of_month_anchor_phrase
    )
    test_extract_dates_prefers_full_other_night_phrase = (
        StrictCases.test_extract_dates_prefers_full_other_night_phrase
    )
    test_extract_dates_prefers_full_night_before_last_phrase = (
        StrictCases.test_extract_dates_prefers_full_night_before_last_phrase
    )
    test_extract_dates_prefers_full_next_valentines_phrase = (
        StrictCases.test_extract_dates_prefers_full_next_valentines_phrase
    )
    test_extract_dates_prefers_full_pancake_day_phrase = (
        StrictCases.test_extract_dates_prefers_full_pancake_day_phrase
    )
    test_extract_dates_prefers_full_shrove_tuesday_phrase = (
        StrictCases.test_extract_dates_prefers_full_shrove_tuesday_phrase
    )
    test_extract_dates_prefers_full_night_before_yesterday_phrase = (
        StrictCases.test_extract_dates_prefers_full_night_before_yesterday_phrase
    )
    test_extract_dates_prefers_full_y2k_phrase = (
        StrictCases.test_extract_dates_prefers_full_y2k_phrase
    )
    test_extract_dates_prefers_full_four_and_twenty_past_phrase = (
        StrictCases.test_extract_dates_prefers_full_four_and_twenty_past_phrase
    )
    test_extract_dates_prefers_full_on_part_of_day_phrase = (
        StrictCases.test_extract_dates_prefers_full_on_part_of_day_phrase
    )
    test_extract_dates_handles_in_the_part_of_day_phrase = (
        StrictCases.test_extract_dates_handles_in_the_part_of_day_phrase
    )
    test_extract_dates_prefers_full_numeric_in_the_part_of_day_phrase = (
        StrictCases.test_extract_dates_prefers_full_numeric_in_the_part_of_day_phrase
    )
    test_extract_dates_prefers_full_prior_today_phrase = (
        StrictCases.test_extract_dates_prefers_full_prior_today_phrase
    )
    test_extract_dates_prefers_full_earlier_today_phrase = (
        StrictCases.test_extract_dates_prefers_full_earlier_today_phrase
    )
    test_extract_dates_prefers_full_nights_time_phrase = (
        StrictCases.test_extract_dates_prefers_full_nights_time_phrase
    )
    test_extract_dates_prefers_full_part_of_day_of_ordinal_phrase = (
        StrictCases.test_extract_dates_prefers_full_part_of_day_of_ordinal_phrase
    )
    test_extract_dates_prefers_full_part_of_day_on_boundary_phrase = (
        StrictCases.test_extract_dates_prefers_full_part_of_day_on_boundary_phrase
    )
    test_extract_dates_prefers_full_numeric_ordinal_month_year_phrase = (
        StrictCases.test_extract_dates_prefers_full_numeric_ordinal_month_year_phrase
    )
    test_extract_dates_prefers_full_word_ordinal_month_year_time_phrase = (
        StrictCases.test_extract_dates_prefers_full_word_ordinal_month_year_time_phrase
    )
    test_extract_dates_prefers_full_ordinal_day_of_ordinal_month_phrase = (
        StrictCases.test_extract_dates_prefers_full_ordinal_day_of_ordinal_month_phrase
    )
    test_extract_dates_handles_now_phrase = StrictCases.test_extract_dates_handles_now_phrase
    test_extract_dates_handles_right_now_phrase = (
        StrictCases.test_extract_dates_handles_right_now_phrase
    )
    test_extract_dates_prefers_full_month_boundary_phrase = (
        StrictCases.test_extract_dates_prefers_full_month_boundary_phrase
    )
    test_extract_dates_prefers_full_month_start_phrase = (
        StrictCases.test_extract_dates_prefers_full_month_start_phrase
    )
    test_extract_dates_prefers_full_first_day_in_month_phrase = (
        StrictCases.test_extract_dates_prefers_full_first_day_in_month_phrase
    )
    test_extract_dates_prefers_full_last_day_in_month_phrase = (
        StrictCases.test_extract_dates_prefers_full_last_day_in_month_phrase
    )
    test_extract_dates_prefers_full_second_to_last_day_phrase = (
        StrictCases.test_extract_dates_prefers_full_second_to_last_day_phrase
    )
    test_extract_dates_prefers_full_last_weekday_of_year_phrase = (
        StrictCases.test_extract_dates_prefers_full_last_weekday_of_year_phrase
    )
    test_extract_dates_prefers_full_last_day_of_year_phrase = (
        StrictCases.test_extract_dates_prefers_full_last_day_of_year_phrase
    )
    test_extract_dates_prefers_full_hundredth_day_of_year_phrase = (
        StrictCases.test_extract_dates_prefers_full_hundredth_day_of_year_phrase
    )
    test_extract_dates_prefers_full_hundreth_day_of_year_phrase = (
        StrictCases.test_extract_dates_prefers_full_hundreth_day_of_year_phrase
    )
    test_extract_dates_prefers_full_last_day_of_month_next_year_phrase = (
        StrictCases.test_extract_dates_prefers_full_last_day_of_month_next_year_phrase
    )
    test_extract_dates_prefers_full_a_week_tomorrow_phrase = (
        StrictCases.test_extract_dates_prefers_full_a_week_tomorrow_phrase
    )
    test_extract_dates_prefers_full_a_week_on_monday_phrase = (
        StrictCases.test_extract_dates_prefers_full_a_week_on_monday_phrase
    )
    test_extract_dates_prefers_full_week_before_last_day_of_year_phrase = (
        StrictCases.test_extract_dates_prefers_full_week_before_last_day_of_year_phrase
    )
    test_extract_dates_prefers_full_one_month_today_phrase = (
        StrictCases.test_extract_dates_prefers_full_one_month_today_phrase
    )
    test_extract_dates_prefers_full_dinner_time_phrase = (
        StrictCases.test_extract_dates_prefers_full_dinner_time_phrase
    )
    test_extract_dates_prefers_full_bare_dinner_phrase = (
        StrictCases.test_extract_dates_prefers_full_bare_dinner_phrase
    )
    test_extract_dates_prefers_full_about_lunch_time_phrase = (
        StrictCases.test_extract_dates_prefers_full_about_lunch_time_phrase
    )
    test_extract_dates_prefers_full_two_fridays_from_now_phrase = (
        StrictCases.test_extract_dates_prefers_full_two_fridays_from_now_phrase
    )
    test_extract_dates_prefers_full_tuesday_gone_phrase = (
        StrictCases.test_extract_dates_prefers_full_tuesday_gone_phrase
    )
    test_extract_dates_prefers_full_tuesday_past_phrase = (
        StrictCases.test_extract_dates_prefers_full_tuesday_past_phrase
    )
    test_extract_dates_prefers_full_t_minus_phrase = (
        StrictCases.test_extract_dates_prefers_full_t_minus_phrase
    )
    test_extract_dates_prefers_full_t_minus_hyphen_phrase = (
        StrictCases.test_extract_dates_prefers_full_t_minus_hyphen_phrase
    )
    test_extract_dates_prefers_full_solar_event_phrase = (
        StrictCases.test_extract_dates_prefers_full_solar_event_phrase
    )
    test_extract_dates_prefers_full_solar_event_weekday_phrase = (
        StrictCases.test_extract_dates_prefers_full_solar_event_weekday_phrase
    )
    test_extract_dates_prefers_full_solar_event_at_date_phrase = (
        StrictCases.test_extract_dates_prefers_full_solar_event_at_date_phrase
    )
    test_extract_dates_prefers_full_first_light_phrase = (
        StrictCases.test_extract_dates_prefers_full_first_light_phrase
    )
    test_extract_dates_prefers_full_year_prefixed_ordinal_weekday_phrase = (
        StrictCases.test_extract_dates_prefers_full_year_prefixed_ordinal_weekday_phrase
    )
    test_extract_dates_prefers_full_week_of_last_century_phrase = (
        StrictCases.test_extract_dates_prefers_full_week_of_last_century_phrase
    )
    test_extract_dates_prefers_full_ordinal_second_of_minute_phrase = (
        StrictCases.test_extract_dates_prefers_full_ordinal_second_of_minute_phrase
    )
    test_extract_dates_prefers_full_ordinal_hour_phrase = (
        StrictCases.test_extract_dates_prefers_full_ordinal_hour_phrase
    )
    test_extract_dates_prefers_full_ordinal_second_minute_on_anchor_phrase = (
        StrictCases.test_extract_dates_prefers_full_ordinal_second_minute_on_anchor_phrase
    )
    test_extract_dates_prefers_full_day_before_nested_ordinal_time_phrase = (
        StrictCases.test_extract_dates_prefers_full_day_before_nested_ordinal_time_phrase
    )
    test_extract_dates_prefers_full_explicit_time_then_part_of_day_phrase = (
        StrictCases.test_extract_dates_prefers_full_explicit_time_then_part_of_day_phrase
    )
    test_extract_dates_prefers_full_leap_year_anchor_phrase = (
        StrictCases.test_extract_dates_prefers_full_leap_year_anchor_phrase
    )
    test_extract_dates_prefers_full_next_leap_day_phrase = (
        StrictCases.test_extract_dates_prefers_full_next_leap_day_phrase
    )
    test_extract_dates_prefers_full_midsummer_alias_phrase = (
        StrictCases.test_extract_dates_prefers_full_midsummer_alias_phrase
    )
    test_extract_dates_prefers_full_next_full_moon_phrase = (
        StrictCases.test_extract_dates_prefers_full_next_full_moon_phrase
    )
    test_extract_dates_prefers_full_anchor_offset_with_moon_event = (
        StrictCases.test_extract_dates_prefers_full_anchor_offset_with_moon_event
    )
    test_extract_dates_prefers_full_solar_event_on_moon_event = (
        StrictCases.test_extract_dates_prefers_full_solar_event_on_moon_event
    )
    test_extract_dates_prefers_full_business_day_after_moon_event = (
        StrictCases.test_extract_dates_prefers_full_business_day_after_moon_event
    )
    test_extract_dates_prefers_full_anchor_offset_with_quarter_anchor = (
        StrictCases.test_extract_dates_prefers_full_anchor_offset_with_quarter_anchor
    )
    test_extract_dates_prefers_full_solar_event_on_boundary_anchor = (
        StrictCases.test_extract_dates_prefers_full_solar_event_on_boundary_anchor
    )
    test_extract_dates_prefers_full_anchor_offset_with_ordinal_weekday_anchor = (
        StrictCases.test_extract_dates_prefers_full_anchor_offset_with_ordinal_weekday_anchor
    )
    test_extract_dates_prefers_full_solar_event_on_week_period_anchor = (
        StrictCases.test_extract_dates_prefers_full_solar_event_on_week_period_anchor
    )
    test_extract_dates_prefers_full_business_day_after_day_of_year_anchor = (
        StrictCases.test_extract_dates_prefers_full_business_day_after_day_of_year_anchor
    )
    test_extract_dates_prefers_full_ordinal_weekday_before_anchor_phrase = (
        StrictCases.test_extract_dates_prefers_full_ordinal_weekday_before_anchor_phrase
    )
    test_extract_dates_prefers_full_counted_weekday_after_anchor_phrase = (
        StrictCases.test_extract_dates_prefers_full_counted_weekday_after_anchor_phrase
    )
    test_extract_dates_prefers_full_weekday_before_holiday_anchor_phrase = (
        StrictCases.test_extract_dates_prefers_full_weekday_before_holiday_anchor_phrase
    )
    test_extract_dates_prefers_full_minute_past_hour_on_anchor_phrase = (
        StrictCases.test_extract_dates_prefers_full_minute_past_hour_on_anchor_phrase
    )
    test_extract_dates_prefers_full_clock_on_anchor_phrase = (
        StrictCases.test_extract_dates_prefers_full_clock_on_anchor_phrase
    )
    test_extract_dates_prefers_full_clock_tomorrow_phrase = (
        StrictCases.test_extract_dates_prefers_full_clock_tomorrow_phrase
    )
    test_extract_dates_prefers_full_relative_day_then_clock_phrase = (
        StrictCases.test_extract_dates_prefers_full_relative_day_then_clock_phrase
    )
    test_extract_dates_prefers_full_date_then_meridiem_clock_phrase = (
        StrictCases.test_extract_dates_prefers_full_date_then_meridiem_clock_phrase
    )
    test_extract_dates_prefers_full_date_then_twenty_to_meridiem_clock_phrase = (
        StrictCases.test_extract_dates_prefers_full_date_then_twenty_to_meridiem_clock_phrase
    )
    test_extract_dates_prefers_full_date_then_twenty_five_to_meridiem_clock_phrase = (
        StrictCases.test_extract_dates_prefers_full_date_then_twenty_five_to_meridiem_clock_phrase
    )
    test_extract_dates_prefers_full_minutes_to_meridiem_clock_phrase = (
        StrictCases.test_extract_dates_prefers_full_minutes_to_meridiem_clock_phrase
    )
    test_extract_dates_prefers_full_seconds_to_midnight_phrase = (
        StrictCases.test_extract_dates_prefers_full_seconds_to_midnight_phrase
    )
    test_extract_dates_prefers_full_seconds_to_midnight_in_month_anchor_phrase = (
        StrictCases.test_extract_dates_prefers_full_seconds_to_midnight_in_month_anchor_phrase
    )
    test_extract_dates_prefers_full_part_of_day_on_ordinal_weekday_phrase = (
        StrictCases.test_extract_dates_prefers_full_part_of_day_on_ordinal_weekday_phrase
    )
    test_extract_dates_prefers_full_clock_phrase_on_ordinal_weekday_phrase = (
        StrictCases.test_extract_dates_prefers_full_clock_phrase_on_ordinal_weekday_phrase
    )
    test_extract_dates_prefers_full_long_composed_phrase_batch = (
        StrictCases.test_extract_dates_prefers_full_long_composed_phrase_batch
    )
    test_extract_dates_prefers_full_date_when_clock_strikes_phrase = (
        StrictCases.test_extract_dates_prefers_full_date_when_clock_strikes_phrase
    )
    test_extract_dates_prefers_full_solstice_phrase = (
        StrictCases.test_extract_dates_prefers_full_solstice_phrase
    )
    test_extract_dates_prefers_full_article_solstice_phrase = (
        StrictCases.test_extract_dates_prefers_full_article_solstice_phrase
    )
    test_extract_dates_prefers_full_fiscal_phrase = (
        StrictCases.test_extract_dates_prefers_full_fiscal_phrase
    )
    test_extract_dates_prefers_full_month_close_phrase = (
        StrictCases.test_extract_dates_prefers_full_month_close_phrase
    )
    test_extract_dates_prefers_full_the_month_close_phrase = (
        StrictCases.test_extract_dates_prefers_full_the_month_close_phrase
    )
    test_extract_dates_prefers_full_named_lunar_phrase = (
        StrictCases.test_extract_dates_prefers_full_named_lunar_phrase
    )
    test_extract_dates_prefers_full_article_named_lunar_phrase = (
        StrictCases.test_extract_dates_prefers_full_article_named_lunar_phrase
    )
    test_extract_dates_prefers_full_harvest_moon_phrase = (
        StrictCases.test_extract_dates_prefers_full_harvest_moon_phrase
    )
    test_extract_dates_prefers_full_harvest_moon_typo_phrase = (
        StrictCases.test_extract_dates_prefers_full_harvest_moon_typo_phrase
    )
    test_extract_dates_prefers_full_leap_year_offset_phrase = (
        StrictCases.test_extract_dates_prefers_full_leap_year_offset_phrase
    )
    test_extract_dates_multiple_phrases_from_sentence = (
        StrictCases.test_extract_dates_multiple_phrases_from_sentence
    )
    test_extract_dates_can_return_timezone_aware_matches = (
        StrictCases.test_extract_dates_can_return_timezone_aware_matches
    )
    test_date_extract_mode_returns_matches = (
        StrictCases.test_date_extract_mode_returns_matches
    )
    test_extract_dates_returns_empty_when_no_phrase_found = (
        StrictCases.test_extract_dates_returns_empty_when_no_phrase_found
    )
