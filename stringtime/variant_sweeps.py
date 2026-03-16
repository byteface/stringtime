import json
import re
from datetime import datetime, timedelta
from dataclasses import asdict, dataclass
from pathlib import Path

from stringtime import Date

DEFAULT_REFERENCE = "2020-12-25 17:05:55"


@dataclass(frozen=True)
class VariantSeed:
    phrase: str
    expected: str
    family: str


@dataclass(frozen=True)
class VariantCase:
    phrase: str
    expected: str
    family: str
    source_phrase: str


@dataclass(frozen=True)
class ExtractionCase:
    text: str
    expected_text: str
    expected: str
    family: str
    source_phrase: str


@dataclass(frozen=True)
class RangeGlueSeed:
    phrase: str
    family: str


@dataclass(frozen=True)
class CompositionAnchor:
    phrase: str
    expected: str
    family: str


@dataclass(frozen=True)
class LadderStep:
    phrase: str
    expected: str | None
    family: str
    source_phrase: str


@dataclass(frozen=True)
class ExploratorySeed:
    phrase: str
    family: str
    expectation: str


SEED_CASES = (
    VariantSeed("tomorrow night", "2020-12-26 21:00:00", "parts_of_day"),
    VariantSeed("next Tuesday evening", "2020-12-29 19:00:00", "parts_of_day"),
    VariantSeed("end of month", "2020-12-31 17:05:55", "boundary"),
    VariantSeed("the start of june", "2021-06-01 17:05:55", "boundary"),
    VariantSeed("the first day in october", "2020-10-01 17:05:55", "boundary"),
    VariantSeed("the last day in october", "2020-10-31 17:05:55", "boundary"),
    VariantSeed("the first day of october", "2020-10-01 17:05:55", "boundary"),
    VariantSeed("the last day of october", "2020-10-31 17:05:55", "boundary"),
    VariantSeed("today at noon", "2020-12-25 12:00:00", "named_time"),
    VariantSeed("noon today", "2020-12-25 12:00:00", "named_time"),
    VariantSeed("midnight on Friday", "2020-12-25 00:00:00", "named_time"),
    VariantSeed("Friday at midnight", "2020-12-25 00:00:00", "named_time"),
    VariantSeed("3 days from next Wednesday", "2021-01-02 17:05:55", "anchor_offset"),
    VariantSeed("15 minutes before midnight", "2020-12-24 23:45:00", "anchor_offset"),
    VariantSeed("the first Monday in May", "2020-05-04 17:05:55", "ordinal_weekday"),
    VariantSeed("first Monday of May", "2020-05-04 17:05:55", "ordinal_weekday"),
    VariantSeed("the last Friday in June", "2020-06-26 17:05:55", "ordinal_weekday"),
    VariantSeed("last Friday of June", "2020-06-26 17:05:55", "ordinal_weekday"),
    VariantSeed("the 12th of last month", "2020-11-12 17:05:55", "ordinal_date"),
    VariantSeed("next month on the first", "2021-01-01 17:05:55", "ordinal_date"),
    VariantSeed("the first of next month", "2021-01-01 17:05:55", "ordinal_date"),
    VariantSeed("1st of next month", "2021-01-01 17:05:55", "ordinal_date"),
    VariantSeed("next valentines", "2021-02-14 17:05:55", "holiday"),
    VariantSeed("valentine's day", "2020-02-14 17:05:55", "holiday"),
    VariantSeed("pancake day", "2020-02-25 17:05:55", "holiday"),
    VariantSeed("New Year's Day", "2020-01-01 17:05:55", "holiday"),
    VariantSeed("new year's day", "2020-01-01 17:05:55", "holiday"),
    VariantSeed("Halloween", "2020-10-31 17:05:55", "holiday"),
    VariantSeed("hallowe'en", "2020-10-31 17:05:55", "holiday"),
    VariantSeed("shrove tuesday", "2020-02-25 17:05:55", "holiday"),
    VariantSeed("2moro @ noonish", "2020-12-26 12:00:00", "alias"),
    VariantSeed("tmrw@7", "2020-12-26 07:00:00", "alias"),
    VariantSeed("2day@noon", "2020-12-25 12:00:00", "alias"),
    VariantSeed("tmrw@midnite", "2020-12-26 00:00:00", "alias"),
    VariantSeed("frdy", "2020-12-25 17:05:55", "alias"),
    VariantSeed("wknd", "2020-12-26 17:05:55", "alias"),
    VariantSeed("5m", "2020-12-25 17:10:55", "alias"),
    VariantSeed("5m ago", "2020-12-25 17:00:55", "alias"),
    VariantSeed("2h", "2020-12-25 19:05:55", "alias"),
    VariantSeed("2h ago", "2020-12-25 15:05:55", "alias"),
    VariantSeed("1d", "2020-12-26 17:05:55", "alias"),
    VariantSeed("1d from now", "2020-12-26 17:05:55", "alias"),
    VariantSeed("1w", "2021-01-01 17:05:55", "alias"),
    VariantSeed("1w ago", "2020-12-18 17:05:55", "alias"),
    VariantSeed("1y from now", "2021-12-25 17:05:55", "alias"),
    VariantSeed("T-minus 5 minutes", "2020-12-25 17:00:55", "alias"),
    VariantSeed("in a fortnight", "2021-01-08 17:05:55", "duration"),
    VariantSeed("an hour and a half ago", "2020-12-25 15:35:55", "duration"),
    VariantSeed("half five tomorrow night", "2020-12-26 05:30:00", "clock_phrase"),
    VariantSeed("when the clock strikes 6", "2020-12-25 06:00:00", "clock_phrase"),
    VariantSeed("quarter past 5", "2020-12-25 05:15:00", "clock_phrase"),
    VariantSeed("half past 5", "2020-12-25 05:30:00", "clock_phrase"),
    VariantSeed("quarter to 6", "2020-12-25 05:45:00", "clock_phrase"),
    VariantSeed("4 and twenty past 7", "2020-12-25 07:24:00", "clock_phrase"),
    VariantSeed("yesterday at 5 past 10", "2020-12-24 10:05:00", "clock_phrase"),
    VariantSeed("tomorrow at 5 past 10", "2020-12-26 10:05:00", "clock_phrase"),
    VariantSeed("December 1st @ 5 to 6pm", "2020-12-01 17:55:00", "clock_phrase"),
    VariantSeed("December 1st @ twenty to 6pm", "2020-12-01 17:40:00", "clock_phrase"),
    VariantSeed("December 1st @ twenty five to 7pm", "2020-12-01 18:35:00", "clock_phrase"),
    VariantSeed("December 1st @ quarter to 6pm", "2020-12-01 17:45:00", "clock_phrase"),
    VariantSeed("next monday at twenty to 6pm", "2020-12-28 17:40:00", "clock_phrase"),
    VariantSeed("next monday at twenty five to 7pm", "2020-12-28 18:35:00", "clock_phrase"),
    VariantSeed("4 minutes to 4pm", "2020-12-25 15:56:00", "clock_phrase"),
    VariantSeed("4 minutes to 4pm tomorrow", "2020-12-26 15:56:00", "clock_phrase"),
    VariantSeed("10 seconds to midnight", "2020-12-25 23:59:50", "clock_phrase"),
    VariantSeed("10 seconds to midnight tomorrow", "2020-12-26 23:59:50", "clock_phrase"),
    VariantSeed("10 seconds to 4pm", "2020-12-25 15:59:50", "clock_phrase"),
    VariantSeed("10 seconds to midnight in mid september", "2021-09-15 23:59:50", "clock_phrase"),
    VariantSeed("on the fourteenth of february when the clock strikes 12", "2020-02-14 12:00:00", "clock_phrase"),
    VariantSeed("Friday afternoon", "2020-12-25 15:00:00", "parts_of_day"),
    VariantSeed("on Friday evening", "2020-12-25 19:00:00", "parts_of_day"),
    VariantSeed("on Tuesday afternoon", "2020-12-29 15:00:00", "parts_of_day"),
    VariantSeed("the second to last day of the month", "2020-12-30 17:05:55", "boundary"),
    VariantSeed("the other night", "2020-12-24 21:00:00", "parts_of_day"),
    VariantSeed("right now", "2020-12-25 17:05:55", "alias"),
    VariantSeed("a week 2moro", "2021-01-02 17:05:55", "anchor_offset"),
    VariantSeed("bank holiday", "2020-12-25 17:05:55", "holiday"),
    VariantSeed("Christmas Eve", "2020-12-24 17:05:55", "holiday"),
    VariantSeed("the last Sunday of the year", "2020-12-27 17:05:55", "ordinal_weekday"),
    VariantSeed("the hundredth day of the year", "2020-04-09 17:05:55", "day_of_year"),
    VariantSeed("the hundreth day of the year", "2020-04-09 17:05:55", "day_of_year"),
    VariantSeed("end of business tomorrow", "2020-12-26 17:00:00", "business"),
    VariantSeed("EOP", "2020-12-25 17:00:00", "business"),
    VariantSeed("close of year", "2020-12-31 17:05:55", "business"),
    VariantSeed("close of the year", "2020-12-31 17:05:55", "business"),
    VariantSeed("start of next quarter", "2021-01-01 17:05:55", "business"),
    VariantSeed("start of the next quarter", "2021-01-01 17:05:55", "business"),
    VariantSeed("at dinner time", "2020-12-25 18:00:00", "mealtime"),
    VariantSeed("tea time", "2020-12-26 17:00:00", "mealtime"),
    VariantSeed("at midday", "2020-12-25 12:00:00", "linking"),
    VariantSeed("Sunday @ about lunch time", "2020-12-27 12:30:00", "mealtime"),
    VariantSeed("the other day", "2020-12-23 17:05:55", "relative_day"),
    VariantSeed("the day before yesterday", "2020-12-23 17:05:55", "relative_day"),
    VariantSeed("the day after tomorrow", "2020-12-27 17:05:55", "relative_day"),
    VariantSeed("in the morrow", "2020-12-26 17:05:55", "relative_day"),
    VariantSeed("Tuesday gone", "2020-12-22 17:05:55", "relative_weekday"),
    VariantSeed("Tuesday past", "2020-12-22 17:05:55", "relative_weekday"),
    VariantSeed("the 2nd week of january", "2021-01-08 17:05:55", "week_period"),
    VariantSeed("the day before the 2nd week of january", "2021-01-07 17:05:55", "week_period"),
    VariantSeed("3 weeks ago at 2am", "2020-12-04 02:00:00", "relative_time"),
    VariantSeed("plus 1 day", "2020-12-26 17:05:55", "add_subtract"),
    VariantSeed("minus 1 day", "2020-12-24 17:05:55", "add_subtract"),
    VariantSeed("today plus 1 hour", "2020-12-25 18:05:55", "add_subtract"),
    VariantSeed("today minus 1 hour", "2020-12-25 16:05:55", "add_subtract"),
    VariantSeed("now add 1 hour", "2020-12-25 18:05:55", "add_subtract"),
    VariantSeed("now take away 1 hour", "2020-12-25 16:05:55", "add_subtract"),
    VariantSeed("give or take a day", "2020-12-26 17:05:55", "approximate_offset"),
    VariantSeed("a day or so", "2020-12-26 17:05:55", "approximate_offset"),
    VariantSeed("approximately a day", "2020-12-26 17:05:55", "approximate_offset"),
    VariantSeed("by tomorrow noon", "2020-12-26 12:00:00", "linking"),
    VariantSeed("by noon tomorrow", "2020-12-26 12:00:00", "linking"),
    VariantSeed("as of tomorrow", "2020-12-26 17:05:55", "linking"),
    VariantSeed("on next tuesday", "2020-12-29 17:05:55", "linking"),
    VariantSeed("on the next tuesday", "2020-12-29 17:05:55", "linking"),
    VariantSeed("in october", "2021-10-01 17:05:55", "linking"),
    VariantSeed("at noon", "2020-12-25 12:00:00", "linking"),
    VariantSeed("from next wednesday", "2020-12-30 17:05:55", "linking"),
    VariantSeed("from the next wednesday", "2020-12-30 17:05:55", "linking"),
    VariantSeed("tomorrow at 5pm UTC", "2020-12-26 17:00:00", "timezone"),
    VariantSeed("next Friday 9am PST", "2021-01-01 09:00:00", "timezone"),
    VariantSeed("tomorrow at 5pm UTC+2", "2020-12-26 17:00:00", "timezone"),
    VariantSeed("tomorrow at 5 p.m. UTC", "2020-12-26 17:00:00", "timezone"),
    VariantSeed("start of Q2", "2020-04-01 17:05:55", "quarter"),
    VariantSeed("mid Q1 2027", "2027-02-15 17:05:55", "quarter"),
    VariantSeed("the next leap year", "2024-01-01 17:05:55", "leap_year"),
    VariantSeed("a day before the next leap year", "2023-12-31 17:05:55", "leap_year"),
    VariantSeed("full moon", "2020-12-29 22:44:26", "moon"),
    VariantSeed("next new moon", "2021-01-13 17:06:27", "moon"),
    VariantSeed("harvest moon", "2021-09-21 17:20:52", "moon"),
    VariantSeed("blue moon", "2023-08-31 10:58:01", "moon"),
    VariantSeed("3 days after start of Q2", "2020-04-04 17:05:55", "anchor_registry"),
    VariantSeed("at dusk on end of month", "2020-12-31 16:30:00", "anchor_registry"),
    VariantSeed("2 days after the first Monday in May", "2020-05-06 17:05:55", "anchor_registry"),
    VariantSeed("at dawn on the 2nd week of january", "2021-01-08 07:30:00", "anchor_registry"),
    VariantSeed("the first business day after the hundredth day of the year", "2020-04-10 17:05:55", "anchor_registry"),
    VariantSeed("next summer", "2021-06-01 17:05:55", "season"),
    VariantSeed("spring equinox", "2021-03-20 12:00:00", "solstice_equinox"),
    VariantSeed("fiscal year end", "2020-12-31 17:05:55", "fiscal"),
    VariantSeed("month close", "2020-12-31 17:05:55", "fiscal"),
    VariantSeed("start of week", "2020-12-21 17:05:55", "recurring_week"),
    VariantSeed("on wednesdays", "2020-12-30 17:05:55", "recurring_weekday"),
    VariantSeed("wolf moon", "2021-01-28 11:28:29", "named_lunar"),
    VariantSeed("the last tuesday before the end of last autumn", "2020-11-24 17:05:55", "stacked_anchor"),
    VariantSeed("the first business day after fiscal year end", "2021-01-01 17:05:55", "stacked_anchor"),
    VariantSeed("the first business day after month close", "2021-01-01 17:05:55", "stacked_anchor"),
    VariantSeed("at dusk on the spring equinox", "2021-03-20 18:40:00", "stacked_anchor"),
    VariantSeed("at dawn on wolf moon", "2021-01-28 07:30:00", "stacked_anchor"),
    VariantSeed("in the evening on fiscal year end", "2020-12-31 19:00:00", "stacked_anchor"),
    VariantSeed("the first business day after the wolf moon", "2021-01-29 11:28:29", "stacked_anchor"),
    VariantSeed("the last tuesday before the next summer", "2021-05-25 17:05:55", "stacked_anchor"),
    VariantSeed("2 fridays after spring equinox", "2021-04-02 12:00:00", "stacked_anchor"),
    VariantSeed("the 7th of the 6th eighty one", "1981-06-07 17:05:55", "ordinal_month_year"),
    VariantSeed("the first of the 3rd 22 @ 3pm", "2022-03-01 15:00:00", "ordinal_month_year"),
    VariantSeed("the first of the 3rd 22 at 3pm", "2022-03-01 15:00:00", "ordinal_month_year"),
    VariantSeed("7th of the 6th 81", "1981-06-07 17:05:55", "ordinal_month_year"),
    VariantSeed("the 7th of the sixth 81", "1981-06-07 17:05:55", "ordinal_month_year"),
    VariantSeed("the fourteenth week after xmas", "2021-04-02 17:05:55", "anchor_offset"),
    VariantSeed("328 years ago on xmas day", "1692-12-25 17:05:55", "anchor_offset"),
    VariantSeed("two Fridays from now", "2021-01-08 17:05:55", "counted_weekday"),
    VariantSeed("the twelfth month", "2021-12-01 17:05:55", "month_anchor"),
    VariantSeed("the 12th month of the year", "2021-12-01 17:05:55", "month_anchor"),
    VariantSeed("the day before the twelfth month", "2021-11-30 17:05:55", "month_anchor"),
    VariantSeed("the day before the 12th month", "2021-11-30 17:05:55", "month_anchor"),
    VariantSeed("the middle of september", "2021-09-15 17:05:55", "month_anchor"),
    VariantSeed("on the last day of the month in february", "2020-02-29 17:05:55", "boundary"),
    VariantSeed("at 12 on the first day of the month in june", "2020-06-01 12:00:00", "boundary"),
    VariantSeed("the night before last", "2020-12-23 21:00:00", "parts_of_day"),
    VariantSeed("the night b4 yesterday", "2020-12-23 21:00:00", "parts_of_day"),
    VariantSeed(
        "10 seconds to midnight on the first Monday in May",
        "2020-05-04 23:59:50",
        "reordered_composition",
    ),
    VariantSeed(
        "on the first Monday in May at 10 seconds to midnight",
        "2020-05-04 23:59:50",
        "reordered_composition",
    ),
    VariantSeed(
        "5 past 10 on the first Monday in May",
        "2020-05-04 10:05:00",
        "reordered_composition",
    ),
    VariantSeed(
        "on the first Monday in May at 5 past 10",
        "2020-05-04 10:05:00",
        "reordered_composition",
    ),
    VariantSeed(
        "10 seconds to midnight on the middle of september",
        "2021-09-15 23:59:50",
        "mixed_precision",
    ),
    VariantSeed(
        "the middle of september at 10 seconds to midnight",
        "2021-09-15 23:59:50",
        "mixed_precision",
    ),
    VariantSeed(
        "the friday after the second week in june at quarter to six",
        "2021-06-11 05:45:00",
        "long_composition",
    ),
    VariantSeed(
        "ten seconds before noon on the last sunday in october",
        "2020-10-25 11:59:50",
        "long_composition",
    ),
    VariantSeed(
        "at five past ten on the second friday after christmas",
        "2021-01-08 10:05:00",
        "long_composition",
    ),
    VariantSeed(
        "the first business day before the end of next summer",
        "2021-08-30 17:05:55",
        "long_composition",
    ),
    VariantSeed(
        "half past seven on the hundredth day of next year",
        "2021-04-10 07:30:00",
        "long_composition",
    ),
    VariantSeed(
        "the tuesday after the first full moon in april",
        "2021-05-04 01:40:38",
        "long_composition",
    ),
    VariantSeed(
        "five to midnight on the last day in february next year",
        "2021-02-28 23:55:00",
        "long_composition",
    ),
    VariantSeed(
        "the middle of december at quarter past eight in the evening",
        "2021-12-15 20:15:00",
        "long_composition",
    ),
    VariantSeed(
        "three days before the spring equinox at dawn",
        "2021-03-17 05:45:00",
        "long_composition",
    ),
    VariantSeed(
        "the penultimate friday in november at twenty to six",
        "2020-11-20 05:40:00",
        "long_composition",
    ),
    VariantSeed(
        "2 hours after dusk on the first monday in may",
        "2020-05-04 22:20:00",
        "long_composition",
    ),
    VariantSeed(
        "the last working day before fiscal year end at noon",
        "2020-12-30 12:00:00",
        "long_composition",
    ),
    VariantSeed(
        "the first tuesday before the harvest moon at half past seven",
        "2021-09-14 07:30:00",
        "long_composition",
    ),
    VariantSeed(
        "twenty seconds after dusk on the last friday in march",
        "2020-03-27 18:40:20",
        "long_composition",
    ),
    VariantSeed(
        "the second business day after the first full moon in may",
        "2021-05-28 14:24:40",
        "long_composition",
    ),
    VariantSeed(
        "quarter to midnight on the penultimate day of next month",
        "2021-01-30 23:45:00",
        "long_composition",
    ),
    VariantSeed(
        "the third monday after the spring equinox at dawn",
        "2021-04-05 04:45:00",
        "long_composition",
    ),
    VariantSeed(
        "5 past 10 on the first business day after fiscal q1",
        "2021-01-04 10:05:00",
        "long_composition",
    ),
    VariantSeed(
        "the last sunday before the middle of december at noon",
        "2021-12-12 12:00:00",
        "long_composition",
    ),
    VariantSeed(
        "two hours before sunrise on the hundredth day of 2027",
        "2027-04-10 03:25:00",
        "long_composition",
    ),
    VariantSeed(
        "the friday after the last day in february 2028 at 3pm",
        "2028-03-03 15:00:00",
        "long_composition",
    ),
    VariantSeed(
        "the second week in october at five to midnight",
        "2021-10-08 23:55:00",
        "long_composition",
    ),
    VariantSeed(
        "the first friday of next winter at dusk",
        "2021-12-03 16:30:00",
        "long_composition",
    ),
    VariantSeed(
        "the first monday in may five past ten",
        "2020-05-04 10:05:00",
        "long_composition",
    ),
    VariantSeed(
        "quarter past eight the first business day after christmas",
        "2020-12-28 08:15:00",
        "long_composition",
    ),
    VariantSeed(
        "the last working day of next month at end of business",
        "2021-01-29 17:00:00",
        "long_composition",
    ),
    VariantSeed(
        "ten seconds to noon the penultimate friday in november",
        "2020-11-20 11:59:50",
        "long_composition",
    ),
    VariantSeed(
        "friday after the last full moon @ 2:30:12",
        "2020-12-04 02:30:12",
        "long_composition",
    ),
    VariantSeed(
        "3 easters ago",
        "2018-04-01 17:05:55",
        "counted_holiday",
    ),
    VariantSeed(
        "5 fridays ago",
        "2020-11-20 17:05:55",
        "counted_weekday",
    ),
    VariantSeed(
        "in 6 fridays time",
        "2021-02-05 17:05:55",
        "counted_weekday",
    ),
    VariantSeed(
        "half a second after 12pm",
        "2020-12-25 12:00:00.500000",
        "relative_subsecond",
    ),
    VariantSeed(
        "5pm in december 2027",
        "2027-12-01 17:00:00",
        "long_composition",
    ),
    VariantSeed(
        "10 seconds to midnight the first monday in may",
        "2020-05-04 23:59:50",
        "long_composition",
    ),
    VariantSeed(
        "friday the 1st of last december @ 2",
        "2019-12-06 02:00:00",
        "long_composition",
    ),
    VariantSeed(
        "the week before christmas",
        "2020-12-18 17:05:55",
        "anchor_offset",
    ),
    VariantSeed(
        "the month after next easter",
        "2021-05-04 17:05:55",
        "anchor_offset",
    ),
    VariantSeed(
        "quarter to six by the end of june",
        "2021-06-30 05:45:00",
        "long_composition",
    ),
    VariantSeed(
        "the second half of december",
        "2021-12-16 17:05:55",
        "month_anchor",
    ),
    VariantSeed(
        "late afternoon on the first monday in may",
        "2020-05-04 16:30:00",
        "long_composition",
    ),
    VariantSeed(
        "5pm by december 2027",
        "2027-12-01 17:00:00",
        "long_composition",
    ),
    VariantSeed(
        "the weekend after next christmas",
        "2022-01-01 17:05:55",
        "anchor_offset",
    ),
    VariantSeed(
        "half a millisecond after noon",
        "2020-12-25 12:00:00.000500",
        "relative_subsecond",
    ),
    VariantSeed(
        "the first tuesday in june in the evening at 5 past 10",
        "2020-06-02 22:05:00",
        "long_composition",
    ),
    VariantSeed(
        "the full moon before last",
        "2020-10-31 21:16:20",
        "moon",
    ),
    VariantSeed(
        "the friday and the 1st of december 2023",
        "2023-12-01 17:05:55",
        "date_consistency",
    ),
    VariantSeed(
        "end of play tuesday in feb",
        "2021-02-02 17:00:00",
        "business_phrase",
    ),
    VariantSeed(
        "feb 2nd @ 2:20 and 20 seconds",
        "2020-02-02 02:20:20",
        "long_composition",
    ),
    VariantSeed(
        "last september 22nd @ 3:30pm",
        "2020-09-22 15:30:00",
        "ordinal_month_year",
    ),
    VariantSeed(
        "at 3pm on boxing day 2028",
        "2028-12-26 15:00:00",
        "holiday",
    ),
    VariantSeed(
        "2028 at 4pm on the first friday of June",
        "2028-06-02 16:00:00",
        "ordinal_weekday",
    ),
    VariantSeed(
        "the last friday of the year 2029 @ 3pm",
        "2029-12-28 15:00:00",
        "ordinal_weekday",
    ),
)


RANGE_GLUE_SEEDS = (
    RangeGlueSeed("between noon and 2pm", "range"),
    RangeGlueSeed("between midnight and noon tomorrow", "range"),
    RangeGlueSeed("noon to 2pm", "range"),
    RangeGlueSeed("noon until 2pm", "range"),
    RangeGlueSeed("noon through 2pm", "range"),
    RangeGlueSeed("noon thru 2pm", "range"),
    RangeGlueSeed("from Tuesday to Friday", "range"),
    RangeGlueSeed("from next Wednesday to Friday", "range"),
    RangeGlueSeed("between tomorrow and Friday", "range"),
    RangeGlueSeed("Friday through Monday", "range"),
    RangeGlueSeed("Friday till Monday", "range"),
    RangeGlueSeed("Friday til Monday", "range"),
    RangeGlueSeed("Friday until Monday", "range"),
    RangeGlueSeed("through the weekend", "range"),
    RangeGlueSeed("until christmas", "range"),
    RangeGlueSeed("til xmas", "range"),
    RangeGlueSeed("till xmas", "range"),
    RangeGlueSeed("between lunch and dinner", "range"),
)


COMPOSITION_ANCHORS = (
    CompositionAnchor("Christmas Eve", "2020-12-24 17:05:55", "holiday"),
    CompositionAnchor("palm sunday", "2020-04-05 17:05:55", "holiday"),
    CompositionAnchor("wolf moon", "2021-01-28 11:28:29", "named_lunar"),
    CompositionAnchor("full moon", "2020-12-29 22:44:26", "moon"),
    CompositionAnchor("spring equinox", "2021-03-20 12:00:00", "solstice_equinox"),
    CompositionAnchor("next summer", "2021-06-01 17:05:55", "season"),
    CompositionAnchor("fiscal year end", "2020-12-31 17:05:55", "fiscal"),
    CompositionAnchor("month close", "2020-12-31 17:05:55", "fiscal"),
    CompositionAnchor("end of month", "2020-12-31 17:05:55", "boundary"),
    CompositionAnchor("start of Q2", "2020-04-01 17:05:55", "quarter"),
    CompositionAnchor("the first Monday in May", "2020-05-04 17:05:55", "ordinal_weekday"),
    CompositionAnchor("the last Sunday of the year", "2020-12-27 17:05:55", "ordinal_weekday"),
    CompositionAnchor("the twelfth month", "2021-12-01 17:05:55", "month_anchor"),
    CompositionAnchor("the hundredth day of the year", "2020-04-09 17:05:55", "day_of_year"),
    CompositionAnchor("the 2nd week of january", "2021-01-08 17:05:55", "week_period"),
    CompositionAnchor("start of week", "2020-12-21 17:05:55", "recurring_week"),
)


LADDER_STEPS = (
    LadderStep("xmas", "2020-12-25 17:05:55", "ladder_supported", "xmas_ladder"),
    LadderStep("before xmas", None, "ladder_exploratory", "xmas_ladder"),
    LadderStep("a week before xmas", "2020-12-18 17:05:55", "ladder_supported", "xmas_ladder"),
    LadderStep("the week before xmas", None, "ladder_exploratory", "xmas_ladder"),
    LadderStep("Friday before xmas", "2020-12-18 17:05:55", "ladder_supported", "xmas_ladder"),
    LadderStep("5pm on Friday before xmas", "2020-12-18 17:00:00", "ladder_supported", "xmas_ladder"),
    LadderStep("palm sunday", "2020-04-05 17:05:55", "ladder_supported", "palm_sunday_ladder"),
    LadderStep("Friday after palm sunday", "2020-04-10 17:05:55", "ladder_supported", "palm_sunday_ladder"),
    LadderStep("at 4 past 10 on friday after palm sunday", "2020-04-10 10:04:00", "ladder_supported", "palm_sunday_ladder"),
    LadderStep("full moon", "2020-12-29 22:44:26", "ladder_supported", "full_moon_ladder"),
    LadderStep("3 days after full moon", "2021-01-01 22:44:26", "ladder_supported", "full_moon_ladder"),
    LadderStep("at dusk on 3 days after full moon", "2021-01-01 17:00:00", "ladder_supported", "full_moon_ladder"),
    LadderStep("start of Q2", "2020-04-01 17:05:55", "ladder_supported", "quarter_ladder"),
    LadderStep("2 days before start of Q2", "2020-03-30 17:05:55", "ladder_supported", "quarter_ladder"),
    LadderStep("in the evening on 2 days before start of Q2", "2020-03-30 19:00:00", "ladder_supported", "quarter_ladder"),
    LadderStep("next summer", "2021-06-01 17:05:55", "ladder_supported", "season_ladder"),
    LadderStep("3 days after next summer", "2021-06-04 17:05:55", "ladder_supported", "season_ladder"),
    LadderStep("in the evening on 3 days after next summer", "2021-06-04 19:00:00", "ladder_supported", "season_ladder"),
    LadderStep("spring equinox", "2021-03-20 12:00:00", "ladder_supported", "solstice_ladder"),
    LadderStep("Friday after spring equinox", "2021-03-26 12:00:00", "ladder_supported", "solstice_ladder"),
    LadderStep("at 4 past 10 on friday after spring equinox", "2021-03-26 10:04:00", "ladder_supported", "solstice_ladder"),
    LadderStep("fiscal year end", "2020-12-31 17:05:55", "ladder_supported", "fiscal_ladder"),
    LadderStep("the first business day after fiscal year end", "2021-01-01 17:05:55", "ladder_supported", "fiscal_ladder"),
    LadderStep("in the evening on the first business day after fiscal year end", "2021-01-01 19:00:00", "ladder_supported", "fiscal_ladder"),
    LadderStep("start of week", "2020-12-21 17:05:55", "ladder_supported", "recurring_week_ladder"),
    LadderStep("3 days after start of week", "2020-12-24 17:05:55", "ladder_supported", "recurring_week_ladder"),
    LadderStep("noon on 3 days after start of week", "2020-12-24 12:00:00", "ladder_supported", "recurring_week_ladder"),
    LadderStep("the first Monday in May", "2020-05-04 17:05:55", "ladder_supported", "ordinal_weekday_ladder"),
    LadderStep("2 days after the first Monday in May", "2020-05-06 17:05:55", "ladder_supported", "ordinal_weekday_ladder"),
    LadderStep("noon on 2 days after the first Monday in May", "2020-05-06 12:00:00", "ladder_supported", "ordinal_weekday_ladder"),
    LadderStep("the hundredth day of the year", "2020-04-09 17:05:55", "ladder_supported", "day_of_year_ladder"),
    LadderStep("the first business day after the hundredth day of the year", "2020-04-10 17:05:55", "ladder_supported", "day_of_year_ladder"),
    LadderStep("at dusk on the first business day after the hundredth day of the year", "2020-04-10 19:35:00", "ladder_supported", "day_of_year_ladder"),
    LadderStep("the 2nd week of january", "2021-01-08 17:05:55", "ladder_supported", "week_period_ladder"),
    LadderStep("2 days before the 2nd week of january", "2021-01-06 17:05:55", "ladder_supported", "week_period_ladder"),
    LadderStep("in the evening on 2 days before the 2nd week of january", "2021-01-06 19:00:00", "ladder_supported", "week_period_ladder"),
    LadderStep("the twelfth month", "2021-12-01 17:05:55", "ladder_supported", "month_anchor_ladder"),
    LadderStep("Friday before the twelfth month", "2021-11-26 17:05:55", "ladder_supported", "month_anchor_ladder"),
    LadderStep("5pm on Friday before the twelfth month", "2021-11-26 17:00:00", "ladder_supported", "month_anchor_ladder"),
    LadderStep("end of month", "2020-12-31 17:05:55", "ladder_supported", "boundary_ladder"),
    LadderStep("Friday before end of month", "2020-12-25 17:05:55", "ladder_supported", "boundary_ladder"),
    LadderStep("5pm on Friday before end of month", "2020-12-25 17:00:00", "ladder_supported", "boundary_ladder"),
)


EXPLORATORY_SEEDS = (
    ExploratorySeed("december 2027 @ 5pm", "mixed_precision_exploratory", "incomplete_month_year_time"),
    ExploratorySeed("on friday in june at 5 past 10", "mixed_precision_exploratory", "ambiguous_weekday_in_month"),
    ExploratorySeed("5 past 10 on friday in june", "mixed_precision_exploratory", "ambiguous_weekday_in_month"),
    ExploratorySeed("friday in june at 5 past 10", "mixed_precision_exploratory", "ambiguous_weekday_in_month"),
    ExploratorySeed("5 past 10 friday in june", "mixed_precision_exploratory", "ambiguous_weekday_in_month"),
    ExploratorySeed("in the evening the first Monday in May", "connector_drift_exploratory", "missing_connector"),
    ExploratorySeed("5 past 10 at the first Monday in May", "connector_drift_exploratory", "awkward_connector"),
    ExploratorySeed("ten past on the 14th", "incomplete_clock_exploratory", "missing_clock_target"),
    ExploratorySeed("friday and the 2nd of december 2023", "contradiction_exploratory", "weekday_date_conflict"),
    ExploratorySeed("monday the 1st of december 2023 at noon", "contradiction_exploratory", "weekday_date_conflict"),
    ExploratorySeed("4 hours before midnight in december 2027", "incomplete_anchor_exploratory", "missing_day_anchor"),
)


def _dedupe_keep_order(items):
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _parse_expected_datetime(expected):
    return datetime.strptime(expected, "%Y-%m-%d %H:%M:%S")


def _format_expected_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


_SOLAR_TIMES = {
    1: {"dawn": (7, 30), "dusk": (17, 0)},
    2: {"dawn": (6, 45), "dusk": (17, 50)},
    3: {"dawn": (5, 45), "dusk": (18, 40)},
    4: {"dawn": (4, 45), "dusk": (19, 35)},
    5: {"dawn": (4, 0), "dusk": (20, 20)},
    6: {"dawn": (3, 30), "dusk": (20, 50)},
    7: {"dawn": (3, 45), "dusk": (20, 45)},
    8: {"dawn": (4, 30), "dusk": (19, 55)},
    9: {"dawn": (5, 20), "dusk": (18, 55)},
    10: {"dawn": (6, 10), "dusk": (17, 45)},
    11: {"dawn": (6, 55), "dusk": (16, 50)},
    12: {"dawn": (7, 25), "dusk": (16, 30)},
}


def _previous_weekday(dt, weekday):
    current = dt.date()
    while True:
        current -= timedelta(days=1)
        if current.weekday() == weekday:
            return dt.replace(year=current.year, month=current.month, day=current.day)


def _nth_weekday_after(dt, weekday, count):
    current = dt.date()
    found = 0
    while found < count:
        current += timedelta(days=1)
        if current.weekday() == weekday:
            found += 1
    return dt.replace(year=current.year, month=current.month, day=current.day)


def _first_business_day_after(dt):
    current = dt.date()
    while True:
        current += timedelta(days=1)
        if current.weekday() < 5:
            return dt.replace(year=current.year, month=current.month, day=current.day)


def _set_solar_time(dt, event):
    hour, minute = _SOLAR_TIMES[dt.month][event]
    return dt.replace(hour=hour, minute=minute, second=0)


def _set_clock_time(dt, hour, minute):
    return dt.replace(hour=hour, minute=minute, second=0)


def _apply_day_offset(dt, days):
    shifted = dt + timedelta(days=days)
    return dt.replace(
        year=shifted.year,
        month=shifted.month,
        day=shifted.day,
    )


def _common_variants(phrase):
    variants = [phrase]

    if "@" in phrase:
        variants.append(phrase.replace("@", " @ "))
        variants.append(phrase.replace("@", " at "))
    if " at " in f" {phrase} ":
        variants.append(phrase.replace(" at ", " @ "))

    replacements = (
        ("tomorrow", "2moro"),
        ("tomorrow", "tmrw"),
        ("tomorrow", "2moz"),
        ("2moro", "tomorrow"),
        ("night", "nite"),
        ("christmas", "xmas"),
        ("end of business", "eob"),
        ("close of year", "eoy"),
        ("before", "b4"),
        ("b4", "before"),
        ("T-minus", "T minus"),
        ("T minus", "T-minus"),
    )
    for source, target in replacements:
        if re.search(rf"\b{re.escape(source)}\b", phrase, flags=re.IGNORECASE):
            variants.append(
                re.sub(rf"\b{re.escape(source)}\b", target, phrase, flags=re.IGNORECASE)
            )

    if phrase and phrase[0].isalpha():
        variants.append(phrase.lower())
        variants.append(phrase.title())
        variants.append(phrase.upper())

    return _dedupe_keep_order([variant.strip() for variant in variants if variant.strip()])


def _connector_variants(seed):
    phrase = seed.phrase
    variants = []

    if seed.family == "boundary":
        connector_replacements = (
            (" day of ", " day in "),
            (" day in ", " day of "),
            (" of the year", " of year"),
            (" in the year", " in year"),
            (" of the month", " of month"),
            (" in the month", " in month"),
        )
        for source, target in connector_replacements:
            if source in phrase:
                variants.append(phrase.replace(source, target))

        if phrase.startswith("the "):
            variants.append(phrase.removeprefix("the "))
        elif phrase.split()[0] in {"start", "end", "close", "first", "last"}:
            variants.append(f"the {phrase}")

    if seed.family == "ordinal_weekday":
        if " in " in phrase:
            variants.append(phrase.replace(" in ", " of "))
        if " of " in phrase:
            variants.append(phrase.replace(" of ", " in "))
        variants.append(phrase.replace(" of the year", " of year"))
        variants.append(phrase.replace(" in the year", " in year"))
        if phrase.startswith("the "):
            variants.append(phrase.removeprefix("the "))

    if seed.family == "named_time":
        if phrase == "midnight on Friday":
            variants.extend(("on Friday at midnight", "midnight on the Friday"))
        if phrase == "today at noon":
            variants.extend(("at noon today",))

    if seed.family == "anchor_offset":
        if phrase == "3 days from next Wednesday":
            variants.extend(
                (
                    "3 days from the next Wednesday",
                    "3 days after the next Wednesday",
                )
            )
        if phrase == "15 minutes before midnight":
            variants.extend(("15 minutes before the midnight",))
        if phrase == "a week 2moro":
            variants.extend(("a week from tomorrow", "one week from tomorrow"))
        if phrase == "the fourteenth week after xmas":
            variants.extend(("the fourteenth week after the xmas",))

    if seed.family == "business":
        if phrase == "close of year":
            variants.extend(("close of the year", "end of the year"))
        if phrase == "start of next quarter":
            variants.extend(("start of the next quarter", "the start of the next quarter"))
        if phrase == "end of business tomorrow":
            variants.extend(("end of business by tomorrow",))

    if seed.family == "ordinal_date":
        if phrase == "next month on the first":
            variants.extend(("next month on first", "next month on the 1st"))
        if phrase == "the 12th of last month":
            variants.extend(("12th of last month", "the 12th in last month"))

    if seed.family == "month_anchor":
        if phrase == "the twelfth month":
            variants.extend(("the twelfth month of the year", "the 12th month of the year"))
        if phrase == "the day before the twelfth month":
            variants.extend(("the day before the twelfth month of the year",))

    if seed.family == "quarter":
        if phrase == "start of Q2":
            variants.extend(("start of the Q2",))
        if phrase == "mid Q1 2027":
            variants.extend(("mid of Q1 2027",))

    if seed.family == "timezone":
        if phrase == "tomorrow at 5pm UTC":
            variants.extend(("at 5pm UTC tomorrow",))
        if phrase == "tomorrow at 5pm UTC+2":
            variants.extend(("at 5pm UTC+2 tomorrow",))

    return _dedupe_keep_order([variant for variant in variants if variant and variant != phrase])


def _swap_at_joiners(phrase):
    variants = []
    if " @ " in phrase:
        variants.append(phrase.replace(" @ ", " at "))
    if " at " in phrase:
        variants.append(phrase.replace(" at ", " @ "))
    return variants


def _space_meridiem_variants(phrase):
    variants = []
    variants.append(re.sub(r"(\d)(am|pm)\b", r"\1 \2", phrase, flags=re.IGNORECASE))
    variants.append(re.sub(r"(\d)\s+(am|pm)\b", r"\1\2", phrase, flags=re.IGNORECASE))
    return variants


def _year_position_matrix(seed):
    phrase = seed.phrase
    variants = []

    trailing_year_match = re.fullmatch(r"(?P<rest>.+?)\s+(?P<year>\d{4})", phrase)
    if trailing_year_match is not None:
        rest = trailing_year_match.group("rest")
        year = trailing_year_match.group("year")
        variants.append(f"{year} {rest}")
        time_on_anchor_match = re.fullmatch(
            r"(?P<time>(?:at|@)\s+.+?)\s+on\s+(?P<anchor>.+)",
            rest,
            re.IGNORECASE,
        )
        if time_on_anchor_match is not None:
            variants.append(
                f"{time_on_anchor_match.group('anchor')} {year} {time_on_anchor_match.group('time')}"
            )

    leading_year_match = re.fullmatch(r"(?P<year>\d{4})\s+(?P<rest>.+)", phrase)
    if leading_year_match is not None:
        year = leading_year_match.group("year")
        rest = leading_year_match.group("rest")
        variants.append(f"{rest} {year}")
        time_on_anchor_match = re.fullmatch(
            r"(?P<time>(?:at|@)\s+.+?)\s+on\s+(?P<anchor>.+)",
            rest,
            re.IGNORECASE,
        )
        if time_on_anchor_match is not None:
            variants.append(
                f"{time_on_anchor_match.group('time')} on {time_on_anchor_match.group('anchor')} {year}"
            )

    return [variant for variant in variants if variant != phrase]


def _looks_anchor_like(text):
    return bool(
        re.search(
            r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|january|february|march|april|may|june|july|august|september|october|november|december|christmas|xmas|easter|halloween|boxing day|full moon|wolf moon|harvest moon|blue moon|equinox|solstice|month|year|quarter|week|day)\b",
            text,
            re.IGNORECASE,
        )
    )


def _positional_axis_cases(case):
    variants = []
    phrase = case.phrase

    time_on_anchor_year = re.fullmatch(
        r"(?P<time>(?:at|@)\s+.+?)\s+on\s+(?P<anchor>.+?)\s+(?P<year>\d{4})",
        phrase,
        re.IGNORECASE,
    )
    if time_on_anchor_year is not None:
        variants.append(
            f"{time_on_anchor_year.group('year')} {time_on_anchor_year.group('time')} on {time_on_anchor_year.group('anchor')}"
        )
        variants.append(
            f"{time_on_anchor_year.group('anchor')} {time_on_anchor_year.group('year')} {time_on_anchor_year.group('time')}"
        )

    year_time_on_anchor = re.fullmatch(
        r"(?P<year>\d{4})\s+(?P<time>(?:at|@)\s+.+?)\s+on\s+(?P<anchor>.+)",
        phrase,
        re.IGNORECASE,
    )
    if year_time_on_anchor is not None:
        variants.append(
            f"{year_time_on_anchor.group('time')} on {year_time_on_anchor.group('anchor')} {year_time_on_anchor.group('year')}"
        )
        variants.append(
            f"{year_time_on_anchor.group('anchor')} {year_time_on_anchor.group('year')} {year_time_on_anchor.group('time')}"
        )

    time_on_anchor = re.fullmatch(
        r"(?P<time>(?:at|@)\s+.+?)\s+on\s+(?P<anchor>.+)",
        phrase,
        re.IGNORECASE,
    )
    if time_on_anchor is not None and _looks_anchor_like(time_on_anchor.group("anchor")):
        variants.append(f"{time_on_anchor.group('anchor')} {time_on_anchor.group('time')}")

    anchor_at_time = re.fullmatch(
        r"(?P<anchor>.+?)\s+(?P<joiner>at|@)\s+(?P<time>.+)",
        phrase,
        re.IGNORECASE,
    )
    if anchor_at_time is not None and _looks_anchor_like(anchor_at_time.group("anchor")):
        variants.append(
            f"at {anchor_at_time.group('time')} on {anchor_at_time.group('anchor')}"
        )

    anchor_year = re.fullmatch(r"(?P<anchor>.+?)\s+(?P<year>\d{4})", phrase, re.IGNORECASE)
    if (
        anchor_year is not None
        and case.family
        in {"holiday", "boundary", "ordinal_weekday", "month_anchor", "day_of_year", "long_composition"}
        and _looks_anchor_like(anchor_year.group("anchor"))
    ):
        variants.append(f"{anchor_year.group('year')} {anchor_year.group('anchor')}")

    unique = []
    seen = set()
    for variant in variants:
        key = variant.lower()
        if key == phrase.lower() or key in seen:
            continue
        seen.add(key)
        unique.append(
            VariantCase(
                phrase=variant,
                expected=case.expected,
                family=case.family,
                source_phrase=case.source_phrase,
            )
        )
    return unique


def _can_articleize_anchor(anchor):
    anchor = anchor.strip()
    if anchor.startswith("the "):
        return False
    if re.match(r"^(?:today|tomorrow|yesterday)\b", anchor, re.IGNORECASE):
        return False
    if re.match(
        r"^(?:christmas|xmas|easter|halloween|valentines?|valentine's day|palm sunday|wolf moon|full moon|harvest moon|blue moon)\b",
        anchor,
        re.IGNORECASE,
    ):
        return False
    if len(anchor.split()) == 1:
        return False
    return True


def _relative_named_month_day_time_variants(seed):
    if seed.family not in {"ordinal_month_year", "long_composition"}:
        return []
    match = re.fullmatch(
        r"(?P<relation>last|next|this)\s+(?P<month>[a-z]+)\s+(?P<day>\d{1,2}(?:st|nd|rd|th)?)(?:\s+(?P<joiner>@|at)\s+(?P<time>.+))?",
        seed.phrase,
        re.IGNORECASE,
    )
    if match is None:
        return []

    variants = []
    relation = match.group("relation")
    month = match.group("month")
    day = match.group("day")
    joiner = match.group("joiner")
    time = match.group("time")

    if time is not None:
        variants.extend(_swap_at_joiners(seed.phrase))
        variants.extend(_space_meridiem_variants(seed.phrase))
    variants.append(f"{relation} {month.title()} {day}{f' {joiner} {time}' if time else ''}")
    return variants


def _clock_phrase_matrix(seed):
    if seed.family not in {"clock_phrase", "long_composition", "reordered_composition", "mixed_precision"}:
        return []
    phrase = seed.phrase
    variants = []

    if re.search(r"\b(?:December|January|February|March|April|May|June|July|August|September|October|November)\s+\d", phrase):
        variants.extend(_swap_at_joiners(phrase))
        variants.extend(_space_meridiem_variants(phrase))

    if re.search(r"\b(?:today|tomorrow|yesterday|next monday|next friday)\b", phrase, re.IGNORECASE):
        variants.extend(_swap_at_joiners(phrase))

    clock_forms = (
        ("quarter past 5", ("quarter past five", "a quarter past 5", "quarter past 05")),
        ("half past 5", ("half past five", "half past 05")),
        ("quarter to 6", ("quarter to six", "a quarter to 6", "quarter to 06")),
        ("4 and twenty past 7", ("four and twenty past 7", "4 and 20 past 7", "four and 20 past 7", "4 and twenty past seven")),
        ("when the clock strikes 6", ("the clock strikes 6", "when the clock strikes six", "the clock strikes six")),
    )
    for source, replacements in clock_forms:
        if phrase == source:
            variants.extend(replacements)

    if re.search(r"\b(?:yesterday|tomorrow|next monday)\b.*\b(?:past|to)\b", phrase, re.IGNORECASE):
        variants.extend(_swap_at_joiners(phrase))

    if re.search(r"\b\d{1,2}\s+minutes?\s+to\s+\d{1,2}\s?pm\b", phrase, re.IGNORECASE):
        variants.append(re.sub(r"\bpm\b", " pm", phrase, flags=re.IGNORECASE))

    return [variant for variant in variants if variant != phrase]


def _business_matrix(seed):
    if seed.family not in {"business", "business_phrase", "long_composition"}:
        return []
    phrase = seed.phrase
    variants = []

    match = re.fullmatch(r"(?P<label>end of play|end of business|eop)\s+(?P<anchor>.+)", phrase)
    if match is not None:
        label = match.group("label")
        anchor = match.group("anchor")
        replacements = {
            "end of play": ("close of play", "eop"),
            "end of business": ("close of business", "eob", "cob"),
            "eop": ("end of play",),
        }
        for replacement in replacements.get(label, ()):
            variants.append(f"{replacement} {anchor}")

    return variants


def _time_anchor_matrix(seed):
    if seed.family not in {"linking", "long_composition"}:
        return []
    phrase = seed.phrase
    variants = []
    match = re.fullmatch(r"(?P<time>.+?)\s+by\s+(?P<anchor>.+)", phrase)
    if match is not None:
        variants.append(f"{match.group('time')} on {match.group('anchor')}")
        variants.extend(_space_meridiem_variants(phrase))
    return variants


def _ordinal_weekday_matrix(seed):
    if seed.family not in {"ordinal_weekday", "reordered_composition"}:
        return []
    phrase = seed.phrase
    variants = []
    match = re.fullmatch(
        r"(?:the\s+)?(?P<occurrence>first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th|last|penultimate)\s+(?P<weekday>[A-Za-z]+)\s+(?P<link>in|of)\s+(?P<period>.+)",
        phrase,
        re.IGNORECASE,
    )
    if match is None:
        return variants

    occurrence = match.group("occurrence")
    weekday = match.group("weekday")
    link = match.group("link")
    period = match.group("period")
    other_link = "of" if link == "in" else "in"

    variants.extend(
        (
            f"{occurrence} {weekday} {link} {period}",
            f"the {occurrence} {weekday} {other_link} {period}",
            f"{occurrence} {weekday} {other_link} {period}",
        )
    )
    if period.startswith("the "):
        variants.append(f"the {occurrence} {weekday} {link} {period.removeprefix('the ')}")
    return variants


def _anchor_offset_matrix(seed):
    if seed.family not in {"anchor_offset"}:
        return []
    phrase = seed.phrase
    variants = []
    match = re.fullmatch(
        r"(?P<offset>.+?)\s+(?P<direction>from|after|before)\s+(?P<anchor>.+)",
        phrase,
        re.IGNORECASE,
    )
    if match is not None:
        offset = match.group("offset")
        direction = match.group("direction")
        anchor = match.group("anchor")
        if direction == "from":
            variants.extend(
                (
                    f"{offset} after {anchor}",
                    f"in {offset} from {anchor}",
                )
            )
        else:
            variants.append(f"in {offset} {direction} {anchor}")
        if _can_articleize_anchor(anchor):
            variants.append(f"{offset} {direction} the {anchor}")

    match = re.fullmatch(
        r"(?P<offset>.+?)\s+(?P<anchor>today|tomorrow|yesterday)",
        phrase,
        re.IGNORECASE,
    )
    if match is not None:
        offset = match.group("offset")
        anchor = match.group("anchor")
        variants.extend((f"{offset} from {anchor}", f"{offset} after {anchor}"))

    return variants


def _parts_of_day_matrix(seed):
    if seed.family not in {"parts_of_day", "stacked_anchor"}:
        return []
    phrase = seed.phrase
    variants = []

    part_swaps = {
        "afternoon": ("arvo",),
        "night": ("nite",),
        "tomorrow": ("2moro", "tmrw"),
    }
    for source, targets in part_swaps.items():
        if re.search(rf"\b{re.escape(source)}\b", phrase, flags=re.IGNORECASE):
            for target in targets:
                variants.append(
                    re.sub(rf"\b{re.escape(source)}\b", target, phrase, flags=re.IGNORECASE)
                )

    match = re.fullmatch(r"(?P<date>.+?)\s+(?P<part>morning|afternoon|evening|night)", phrase, re.IGNORECASE)
    if match is not None:
        date = match.group("date")
        part = match.group("part")
        if not date.lower().startswith("on ") and date.lower() not in {"the other", "other"}:
            variants.append(f"on {date} {part}")
            variants.append(f"{part} on {date}")

    return variants


def _business_family_matrix(seed):
    if seed.family not in {"business", "business_phrase", "stacked_anchor", "long_composition"}:
        return []
    phrase = seed.phrase
    variants = []

    if phrase in {"end of business tomorrow", "end of play tomorrow", "eop tomorrow"}:
        variants.extend(("end of business by tomorrow", "end of play by tomorrow"))

    match = re.fullmatch(
        r"(?:the\s+)?(?P<count>first|second|third|\d+)\s+(?:business|working)\s+days?\s+(?P<direction>after|before)\s+(?P<anchor>.+)",
        phrase,
        re.IGNORECASE,
    )
    if match is not None:
        count = match.group("count")
        direction = match.group("direction")
        anchor = match.group("anchor")
        variants.extend(
            (
                f"{count} working days {direction} {anchor}",
                f"the {count} business day {direction} {anchor}",
            )
        )

    match = re.fullmatch(r"(?P<label>end of business|end of play|eop)\s+(?P<anchor>.+)", phrase, re.IGNORECASE)
    if match is not None:
        label = match.group("label")
        anchor = match.group("anchor")
        if label == "end of play":
            variants.extend((f"close of play {anchor}", f"eop {anchor}"))
        elif label == "end of business":
            variants.extend((f"close of business {anchor}", f"eob {anchor}", f"cob {anchor}"))

    return variants


def _ordinal_month_year_matrix(seed):
    if seed.family not in {"ordinal_month_year"}:
        return []
    phrase = seed.phrase
    variants = []

    match = re.fullmatch(
        r"(?:the\s+)?(?P<day>\d{1,2}(?:st|nd|rd|th)?|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\s+of\s+(?:the\s+)?(?P<month>[a-z0-9]+)\s+(?P<year>.+?)(?:\s+(?P<joiner>@|at)\s+(?P<time>.+))?$",
        phrase,
        re.IGNORECASE,
    )
    if match is not None:
        day = match.group("day")
        month = match.group("month")
        year = match.group("year")
        joiner = match.group("joiner")
        time = match.group("time")

        variants.extend(
            (
                f"{day} of the {month} {year}" + (f" {joiner} {time}" if time else ""),
                f"the {day} of {month} {year}" + (f" {joiner} {time}" if time else ""),
            )
        )
        if time is not None:
            variants.extend(_swap_at_joiners(phrase))
            variants.extend(_space_meridiem_variants(phrase))

    match = re.fullmatch(
        r"(?P<relation>last|next|this)\s+(?P<month>[a-z]+)\s+(?P<day>\d{1,2}(?:st|nd|rd|th)?)(?:\s+(?P<joiner>@|at)\s+(?P<time>.+))?",
        phrase,
        re.IGNORECASE,
    )
    if match is not None:
        variants.extend(_relative_named_month_day_time_variants(seed))

    return variants


def _stacked_anchor_matrix(seed):
    if seed.family not in {"stacked_anchor"}:
        return []
    phrase = seed.phrase
    variants = []

    match = re.fullmatch(r"the last tuesday before (?P<anchor>.+)", phrase, re.IGNORECASE)
    if match is not None:
        anchor = match.group("anchor")
        variants.extend((f"last tuesday before {anchor}", f"the last tuesday before the {anchor}" if not anchor.startswith("the ") else f"last tuesday before {anchor}"))

    match = re.fullmatch(r"the first business day after (?P<anchor>.+)", phrase, re.IGNORECASE)
    if match is not None:
        anchor = match.group("anchor")
        variants.extend((f"first business day after {anchor}", f"the first working day after {anchor}"))

    match = re.fullmatch(r"at (?P<time>dawn|dusk) on (?P<anchor>.+)", phrase, re.IGNORECASE)
    if match is not None:
        variants.extend((f"{match.group('time')} on {match.group('anchor')}", f"at {match.group('time')} on the {match.group('anchor')}" if not match.group('anchor').startswith('the ') else f"{match.group('time')} on {match.group('anchor')}"))

    match = re.fullmatch(r"in the evening on (?P<anchor>.+)", phrase, re.IGNORECASE)
    if match is not None:
        anchor = match.group("anchor")
        variants.extend((f"evening on {anchor}", f"in the evening on the {anchor}" if not anchor.startswith("the ") else f"evening on {anchor}"))

    match = re.fullmatch(r"(?P<count>\d+|two)\s+fridays after (?P<anchor>.+)", phrase, re.IGNORECASE)
    if match is not None:
        variants.extend((f"two fridays after {match.group('anchor')}", f"{match.group('count')} fridays after the {match.group('anchor')}" if not match.group('anchor').startswith('the ') else f"two fridays after {match.group('anchor')}"))

    return variants


def _family_variants(seed):
    phrase = seed.phrase
    variants = list(_common_variants(phrase))
    variants.extend(_connector_variants(seed))
    variants.extend(_relative_named_month_day_time_variants(seed))
    variants.extend(_clock_phrase_matrix(seed))
    variants.extend(_business_matrix(seed))
    variants.extend(_time_anchor_matrix(seed))
    variants.extend(_ordinal_weekday_matrix(seed))
    variants.extend(_anchor_offset_matrix(seed))
    variants.extend(_parts_of_day_matrix(seed))
    variants.extend(_business_family_matrix(seed))
    variants.extend(_ordinal_month_year_matrix(seed))
    variants.extend(_stacked_anchor_matrix(seed))
    variants.extend(_year_position_matrix(seed))

    if seed.family == "parts_of_day":
        variants.append(phrase.replace("tomorrow", "2moro"))
        variants.append(phrase.replace("tomorrow", "tmrw"))
        if phrase.lower().startswith("next "):
            variants.append(f"on {phrase}")
        if "afternoon" in phrase:
            variants.append(phrase.replace("afternoon", "arvo"))
        if phrase == "the other night":
            variants.extend(("other night", "the other nite"))
        if phrase == "the night before last":
            variants.extend(("night before last", "the night b4 last"))
        if phrase == "the night b4 yesterday":
            variants.extend(("night b4 yesterday", "the night before yesterday"))

    if seed.family == "boundary":
        if phrase == "end of month":
            variants.extend(("end of the month", "the end of month", "month end"))
        if phrase == "on the last day of the month in february":
            variants.extend(
                (
                    "the last day of the month in february",
                    "on the last day of month in february",
                )
            )
        if phrase == "the start of june":
            variants.extend(
                ("start of june", "the beginning of june", "the start of the month of june")
            )
        if phrase == "the first day in october":
            variants.extend(
                (
                    "first day in october",
                    "the first day of october",
                    "first day of october",
                )
            )
        if phrase == "the last day in october":
            variants.extend(
                (
                    "last day in october",
                    "the last day of october",
                    "last day of october",
                )
            )
        if phrase == "the second to last day of the month":
            variants.extend(
                (
                    "second to last day of the month",
                    "the second-last day of the month",
                    "the penultimate day of the month",
                )
            )

    if seed.family == "ordinal_date":
        if "12th" in phrase:
            variants.extend(
                (
                    phrase.replace("the 12th", "12th"),
                    phrase.replace("12th", "twelfth"),
                    phrase.replace("the 12th of", "12th of"),
                )
            )
        if phrase == "next month on the first":
            variants.extend(
                (
                    "the first of next month",
                    "the 1st of next month",
                    "next month on 1st",
                    "1st of next month",
                )
            )

    if seed.family == "holiday":
        if "valentines" in phrase:
            variants.extend(
                (
                    phrase.replace("valentines", "valentine's day"),
                    phrase.replace("valentines", "valentines day"),
                    phrase.replace("valentines", "st valentine's day"),
                    phrase.replace("valentines", "saint valentine's day"),
                )
            )
        if phrase == "pancake day":
            variants.extend(("shrove tuesday", "shrove Tuesday"))
        if phrase == "shrove tuesday":
            variants.extend(("Shrove Tuesday", "pancake day"))
        if phrase == "Christmas Eve":
            variants.extend(("xmas eve", "christmas eve", "Xmas Eve", "the night before christmas"))
        if phrase == "New Year's Day":
            variants.extend(
                ("new years day", "new year's day", "New Years Day", "new year's")
            )
        if phrase == "Halloween":
            variants.extend(("hallowe'en", "halloween", "all hallows eve"))
        if phrase == "bank holiday":
            variants.extend(("the bank holiday", "bank holiday monday"))

    if seed.family == "duration":
        if "fortnight" in phrase:
            variants.extend(
                (
                    phrase.replace("fortnight", "2 weeks"),
                    phrase.replace("in a fortnight", "a fortnight from now"),
                )
            )
        if phrase == "an hour and a half ago":
            variants.extend(("1.5 hours ago", "one hour and a half ago"))

    if seed.family == "clock_phrase":
        if phrase == "when the clock strikes 6":
            variants.extend(
                (
                    "the clock strikes 6",
                    "when the clock strikes six",
                    "the clock strikes six",
                )
            )
        if phrase == "half five tomorrow night":
            variants.extend(("5:30 tomorrow night", "half 5 tomorrow night"))
        if phrase == "quarter past 5":
            variants.extend(("quarter past five", "a quarter past 5", "quarter past 05"))
        if phrase == "half past 5":
            variants.extend(("half past five", "half past 05"))
        if phrase == "quarter to 6":
            variants.extend(("quarter to six", "a quarter to 6", "quarter to 06"))
        if phrase == "4 and twenty past 7":
            variants.extend(
                (
                    "four and twenty past 7",
                    "4 and 20 past 7",
                    "four and 20 past 7",
                    "4 and twenty past seven",
                )
            )
        if phrase == "yesterday at 5 past 10":
            variants.extend(
                (
                    "yesterday @ 5 past 10",
                    "yesterday at five past ten",
                )
            )
        if phrase == "tomorrow at 5 past 10":
            variants.extend(
                (
                    "tomorrow @ 5 past 10",
                    "tomorrow at five past ten",
                )
            )
        if phrase == "December 1st @ 5 to 6pm":
            variants.extend(
                (
                    "December 1st at 5 to 6pm",
                    "December 1st @ five to 6pm",
                )
            )
        if phrase == "December 1st @ twenty to 6pm":
            variants.extend(
                (
                    "December 1st at twenty to 6pm",
                    "December 1st @ 20 to 6pm",
                )
            )
        if phrase == "December 1st @ twenty five to 7pm":
            variants.extend(
                (
                    "December 1st at twenty five to 7pm",
                    "December 1st @ twenty-five to 7pm",
                )
            )
        if phrase == "December 1st @ quarter to 6pm":
            variants.extend(
                (
                    "December 1st at quarter to 6pm",
                    "December 1st @ a quarter to 6pm",
                )
            )
        if phrase == "next monday at twenty to 6pm":
            variants.extend(
                (
                    "next monday @ twenty to 6pm",
                    "next monday at 20 to 6pm",
                )
            )
        if phrase == "next monday at twenty five to 7pm":
            variants.extend(
                (
                    "next monday @ twenty five to 7pm",
                    "next monday at twenty-five to 7pm",
                )
            )
        if phrase == "4 minutes to 4pm":
            variants.extend(
                (
                    "4 minutes to 4 pm",
                )
            )
        if phrase == "4 minutes to 4pm tomorrow":
            variants.extend(
                (
                    "4 minutes to 4 pm tomorrow",
                )
            )
        if phrase == "10 seconds to midnight":
            variants.extend(
                (
                )
            )
        if phrase == "10 seconds to midnight tomorrow":
            variants.extend(
                (
                    "10 seconds to midnight  tomorrow",
                )
            )
        if phrase == "10 seconds to 4pm":
            variants.extend(
                (
                    "10 seconds to 4 pm",
                )
            )
        if phrase == "10 seconds to midnight in mid september":
            variants.extend(
                (
                    "10 seconds to midnight on the middle of september",
                )
            )
        if phrase == "on the fourteenth of february when the clock strikes 12":
            variants.extend(
                (
                    "the fourteenth of february when the clock strikes 12",
                    "on the fourteenth of february when the clock strikes twelve",
                )
            )

    if seed.family == "named_time":
        if phrase == "today at noon":
            variants.extend(("today noon", "noon today", "midday today"))
        if phrase == "midnight on Friday":
            variants.extend(("Friday at midnight", "midnight Friday"))

    if seed.family == "anchor_offset":
        if phrase == "3 days from next Wednesday":
            variants.extend(
                (
                    "in 3 days from next Wednesday",
                    "3 days after next Wednesday",
                    "3 days from next wednesday",
                )
            )
        if phrase == "15 minutes before midnight":
            variants.extend(
                (
                    "15 mins before midnight",
                    "15 minutes b4 midnight",
                    "15 minutes before 12am",
                )
            )
        if phrase == "a week 2moro":
            variants.extend(("a week tomorrow", "one week tomorrow"))
        if phrase == "the fourteenth week after xmas":
            variants.extend(
                (
                    "fourteenth week after xmas",
                    "the 14th week after xmas",
                    "the fourteenth week after christmas",
                )
            )

    if seed.family == "relative_time":
        if phrase == "3 weeks ago at 2am":
            variants.extend(("3 weeks ago at 2 am", "3 weeks ago at 2 in the morning"))

    if seed.family == "add_subtract":
        if phrase == "plus 1 day":
            variants.extend(("+ 1 day", "add 1 day"))
        if phrase == "minus 1 day":
            variants.extend(("- 1 day", "take away 1 day", "off 1 day"))
        if phrase == "today plus 1 hour":
            variants.extend(("today add 1 hour", "now plus 1 hour"))
        if phrase == "today minus 1 hour":
            variants.extend(("today take away 1 hour", "now minus 1 hour"))
        if phrase == "now add 1 hour":
            variants.extend(("now plus 1 hour",))
        if phrase == "now take away 1 hour":
            variants.extend(("now minus 1 hour", "now off 1 hour"))

    if seed.family == "approximate_offset":
        if phrase == "give or take a day":
            variants.extend(
                (
                    "give or take 1 day",
                    "a day or so",
                    "roughly a day",
                    "approximately a day",
                    "about a day",
                    "around a day",
                )
            )

    if seed.family == "linking":
        if phrase == "by tomorrow noon":
            variants.extend(("by noon tomorrow",))
        if phrase == "on next tuesday":
            variants.extend(("on next Tuesday", "on the next tuesday"))
        if phrase == "in october":
            variants.extend(("in October",))
        if phrase == "at noon":
            variants.extend(("at midday", "at noon today"))
        if phrase == "from next wednesday":
            variants.extend(("from next Wednesday", "from the next wednesday"))

    if seed.family == "ordinal_weekday":
        if phrase == "the first Monday in May":
            variants.extend(
                (
                    "first Monday in May",
                    "the first Monday of May",
                    "first Monday of May",
                )
            )
        if phrase == "the last Friday in June":
            variants.extend(
                (
                    "last Friday in June",
                    "the last Friday of June",
                    "last Friday of June",
                )
            )
        if phrase == "the last Sunday of the year":
            variants.extend(("last Sunday of the year", "the last Sunday in the year"))

    if seed.family == "alias":
        if phrase == "2moro @ noonish":
            variants.extend(
                (
                    "tomorrow @ noonish",
                    "2moz at noonish",
                    "tmrw at noonish",
                    "2moro at midday",
                )
            )
        if phrase == "tmrw@7":
            variants.extend(("tmr@7", "tomo@7", "tmro@7", "tmmrw@7"))
        if phrase == "2day@noon":
            variants.extend(("tdy@noon",))
        if phrase == "tmrw@midnite":
            variants.extend(("tmr@midnite", "tomo@midnite"))
        if phrase == "frdy":
            variants.extend(("fri",))
        if phrase == "wknd":
            variants.extend(("weekend",))
        if phrase == "1d from now":
            variants.extend(("1d hence",))
        if phrase == "1y from now":
            variants.extend(("1y hence",))
        if phrase == "T-minus 5 minutes":
            variants.extend(("t minus 5 minutes", "t-minus 5 minutes"))

    if phrase == "right now":
        variants.extend(("now", "here and now", "immediately", "at once"))

    if seed.family == "business":
        if phrase == "end of business tomorrow":
            variants.extend(
                (
                    "eob tomorrow",
                    "cob tomorrow",
                    "close of business tomorrow",
                    "end of business on the morrow",
                )
            )
        if phrase == "EOP":
            variants.extend(("end of play", "close of play", "eop today"))
        if phrase == "close of year":
            variants.extend(("end of year", "close of the year", "the close of year"))
        if phrase == "start of next quarter":
            variants.extend(
                (
                    "start of the next quarter",
                    "first day of next quarter",
                    "the start of next quarter",
                )
            )

    if seed.family == "relative_day":
        if phrase == "the other day":
            variants.extend(("other day",))
        if phrase == "the day before yesterday":
            variants.extend(("day before yesterday", "before yesterday", "the day b4 yesterday"))
        if phrase == "the day after tomorrow":
            variants.extend(("day after tomorrow", "after tomorrow", "the day after 2moro"))
        if phrase == "in the morrow":
            variants.extend(("on the morrow", "the morrow"))

    if seed.family == "week_period":
        if phrase == "the 2nd week of january":
            variants.extend(("2nd week of january", "the second week of january"))
        if phrase == "the day before the 2nd week of january":
            variants.extend(
                (
                    "day before the 2nd week of january",
                    "the day before the second week of january",
                )
            )

    if seed.family == "day_of_year":
        if phrase == "the hundredth day of the year":
            variants.extend(("hundredth day of the year", "the 100th day of the year"))
        if phrase == "the hundreth day of the year":
            variants.extend(("hundreth day of the year", "the hundredth day of the year"))

    if seed.family == "mealtime":
        if phrase == "at dinner time":
            variants.extend(("dinner time", "at dinnertime", "dinnertime"))
        if phrase == "tea time":
            variants.extend(("teatime", "at tea time", "at teatime"))
        if phrase == "Sunday @ about lunch time":
            variants.extend(
                (
                    "Sunday at lunch time",
                    "Sunday @ lunchtime",
                    "Sunday at lunchtime",
                    "Sunday @ around lunch time",
                )
            )

    if seed.family == "timezone":
        if phrase == "tomorrow at 5pm UTC":
            variants.extend(
                (
                    "tomorrow at 5 pm UTC",
                    "tomorrow 5pm UTC",
                    "tomorrow at 5pm utc",
                    "tomorrow at 17:00 UTC",
                )
            )
        if phrase == "next Friday 9am PST":
            variants.extend(
                (
                    "next Friday at 9am PST",
                    "next Friday 9 am PST",
                    "next Friday 9am pst",
                    "next Friday at 9 a.m. PST",
                )
            )
        if phrase == "tomorrow at 5pm UTC+2":
            variants.extend(
                (
                    "tomorrow at 5 pm UTC+2",
                    "tomorrow at 17:00 UTC+2",
                    "tomorrow at 5pm utc+2",
                )
            )
        if phrase == "tomorrow at 5 p.m. UTC":
            variants.extend(
                (
                    "tomorrow at 5pm UTC",
                    "tomorrow at 5 pm UTC",
                    "tomorrow at 5 post meridiem UTC",
                )
            )

    if seed.family == "quarter":
        if phrase == "start of Q2":
            variants.extend(("start of q2", "the start of Q2"))
        if phrase == "mid Q1 2027":
            variants.extend(("mid q1 2027", "middle of Q1 2027"))

    if seed.family == "leap_year":
        if phrase == "the next leap year":
            variants.extend(("next leap year",))
        if phrase == "a day before the next leap year":
            variants.extend(("1 day before the next leap year",))

    if seed.family == "moon":
        if phrase == "full moon":
            variants.extend(("the full moon", "next full moon", "on the next full moon"))
        if phrase == "next new moon":
            variants.extend(("the next new moon", "on the next new moon", "new moon"))
        if phrase == "harvest moon":
            variants.extend(("the harvest moon", "next harvest moon"))
        if phrase == "blue moon":
            variants.extend(("the blue moon", "next blue moon"))

    if seed.family == "anchor_registry":
        if phrase == "3 days after start of Q2":
            variants.extend(("3 days after the start of Q2", "3 days from start of Q2"))
        if phrase == "at dusk on end of month":
            variants.extend(("dusk on end of month", "at dusk on the end of month"))
        if phrase == "2 days after the first Monday in May":
            variants.extend(("2 days after first Monday in May",))
        if phrase == "at dawn on the 2nd week of january":
            variants.extend(("dawn on the 2nd week of january", "at dawn on the second week of january"))
        if phrase == "the first business day after the hundredth day of the year":
            variants.extend(("first business day after the hundredth day of the year",))

    if seed.family == "season":
        if phrase == "next summer":
            variants.extend(("next Summer", "next summer"))

    if seed.family == "solstice_equinox":
        if phrase == "spring equinox":
            variants.extend(("vernal equinox", "the spring equinox", "next spring equinox"))

    if seed.family == "fiscal":
        if phrase == "fiscal year end":
            variants.extend(("end of fiscal year", "this fiscal year end"))
        if phrase == "month close":
            variants.extend(("the month close",))

    if seed.family == "recurring_week":
        if phrase == "start of week":
            variants.extend(("start of the week",))

    if seed.family == "named_lunar":
        if phrase == "wolf moon":
            variants.extend(("the wolf moon", "next wolf moon"))

    if seed.family == "stacked_anchor":
        if phrase == "the last tuesday before the end of last autumn":
            variants.extend(
                (
                    "last tuesday before the end of last autumn",
                    "the last tuesday before end of last autumn",
                )
            )
        if phrase == "the first business day after fiscal year end":
            variants.extend(
                (
                    "first business day after fiscal year end",
                    "the first business day after end of fiscal year",
                )
            )
        if phrase == "the first business day after month close":
            variants.extend(("first business day after month close",))
        if phrase == "at dusk on the spring equinox":
            variants.extend(("dusk on the spring equinox", "at dusk on spring equinox"))
        if phrase == "at dawn on wolf moon":
            variants.extend(("dawn on wolf moon", "at dawn on the wolf moon"))
        if phrase == "the first business day after the wolf moon":
            variants.extend(("first business day after the wolf moon",))
        if phrase == "the last tuesday before the next summer":
            variants.extend(("last tuesday before the next summer",))
        if phrase == "2 fridays after spring equinox":
            variants.extend(("two fridays after spring equinox", "2 fridays after the spring equinox"))

    if seed.family == "ordinal_month_year":
        if phrase == "the 7th of the 6th eighty one":
            variants.extend(
                (
                    "7th of the 6th eighty one",
                    "the 7th of the 6th 81",
                    "7th of the 6th 81",
                    "the seventh of the 6th 81",
                    "the 7th of the sixth 81",
                )
            )
        if phrase == "the first of the 3rd 22 @ 3pm":
            variants.extend(
                (
                    "first of the 3rd 22 @ 3pm",
                    "the 1st of the 3rd 22 @ 3pm",
                    "the first of the 3rd 22 at 3pm",
                    "1st of the 3rd 22 at 3pm",
                    "the first of the third 22 at 3pm",
                    "the 1st of the third 22 @ 3pm",
                )
            )
        if phrase == "7th of the 6th 81":
            variants.extend(
                (
                    "7th of the sixth 81",
                    "the 7th of the 6th 81",
                    "the 7th of the sixth 81",
                )
            )

    if seed.family == "month_anchor":
        if phrase == "the twelfth month":
            variants.extend(("twelfth month", "the 12th month"))
        if phrase == "the day before the twelfth month":
            variants.extend(
                (
                    "day before the twelfth month",
                    "the day before the 12th month",
                )
            )
        if phrase == "the middle of september":
            variants.extend(("middle of september", "mid september", "mid-september"))

    if seed.family == "relative_weekday":
        if phrase == "Tuesday gone":
            variants.extend(("tuesday gone", "the Tuesday gone"))
        if phrase == "Tuesday past":
            variants.extend(("tuesday past", "the Tuesday past"))

    if seed.family == "recurring_weekday":
        if phrase == "on wednesdays":
            variants.extend(("wednesdays", "every wednesday"))

    if seed.family == "counted_weekday":
        if phrase == "two Fridays from now":
            variants.extend(
                (
                    "2 Fridays from now",
                    "two fridays from now",
                    "two Fridays hence",
                )
            )
        if phrase == "5 fridays ago":
            variants.extend(
                (
                    "five fridays ago",
                )
            )
        if phrase == "in 6 fridays time":
            variants.extend(
                (
                    "6 fridays time",
                    "six fridays time",
                )
            )

    if seed.family == "counted_holiday":
        if phrase == "3 easters ago":
            variants.extend(
                (
                    "three easters ago",
                )
            )

    if seed.family == "relative_subsecond":
        if phrase == "half a second after 12pm":
            variants.extend(
                (
                    "half second after 12pm",
                    "half a second after noon",
                )
            )

    if seed.family == "long_composition":
        if phrase == "the friday after the second week in june at quarter to six":
            variants.extend(
                (
                    "friday after the second week in june at quarter to six",
                    "the friday after the second week of june at quarter to six",
                )
            )
        if phrase == "at five past ten on the second friday after christmas":
            variants.extend(
                (
                    "five past ten on the second friday after christmas",
                    "at five past ten on second friday after christmas",
                )
            )
        if phrase == "five to midnight on the last day in february next year":
            variants.extend(
                (
                    "five to midnight on the last day of february next year",
                )
            )
        if phrase == "the middle of december at quarter past eight in the evening":
            variants.extend(
                (
                    "middle of december at quarter past eight in the evening",
                )
            )
        if phrase == "the last working day before fiscal year end at noon":
            variants.extend(
                (
                    "last working day before fiscal year end at noon",
                    "the last business day before fiscal year end at noon",
                )
            )
        if phrase == "the first tuesday before the harvest moon at half past seven":
            variants.extend(
                (
                    "first tuesday before the harvest moon at half past seven",
                )
            )
        if phrase == "twenty seconds after dusk on the last friday in march":
            variants.extend(
                (
                    "20 seconds after dusk on the last friday in march",
                )
            )
        if phrase == "the second business day after the first full moon in may":
            variants.extend(
                (
                    "second business day after the first full moon in may",
                )
            )
        if phrase == "quarter to midnight on the penultimate day of next month":
            variants.extend(
                (
                    "quarter to midnight on penultimate day of next month",
                )
            )
        if phrase == "5 past 10 on the first business day after fiscal q1":
            variants.extend(
                (
                    "five past ten on the first business day after fiscal q1",
                )
            )
        if phrase == "the first monday in may five past ten":
            variants.extend(
                (
                    "the first monday of may five past ten",
                )
            )
        if phrase == "quarter past eight the first business day after christmas":
            variants.extend(
                (
                    "quarter past eight on the first business day after christmas",
                )
            )
        if phrase == "the last working day of next month at end of business":
            variants.extend(
                (
                    "last working day of next month at end of business",
                )
            )
        if phrase == "ten seconds to noon the penultimate friday in november":
            variants.extend(
                (
                    "10 seconds to noon the penultimate friday in november",
                    "ten seconds to noon on the penultimate friday in november",
                )
            )
        if phrase == "friday after the last full moon @ 2:30:12":
            variants.extend(
                (
                    "friday after the last full moon at 2:30:12",
                )
            )
        if phrase == "5pm in december 2027":
            variants.extend(
                (
                    "5 pm in december 2027",
                    "5pm on december 2027",
                )
            )
        if phrase == "10 seconds to midnight the first monday in may":
            variants.extend(
                (
                    "10 seconds to midnight on the first monday in may",
                )
            )
        if phrase == "friday the 1st of last december @ 2":
            variants.extend(
                (
                    "friday the first of last december @ 2",
                    "friday the 1st of last december at 2",
                )
            )
        if phrase == "last september 22nd @ 3:30pm":
            variants.extend(
                (
                    "next september 22nd @ 3:30pm",
                    "last september 22nd at 3:30pm",
                    "last september 22nd @ 3:30 pm",
                )
            )

    if seed.family == "reordered_composition":
        if phrase == "10 seconds to midnight on the first Monday in May":
            variants.extend(
                (
                    "10 seconds to midnight on the first Monday of May",
                    "the first Monday in May at 10 seconds to midnight",
                    "the first Monday in May @ 10 seconds to midnight",
                )
            )
        if phrase == "on the first Monday in May at 10 seconds to midnight":
            variants.extend(
                (
                    "the first Monday in May at 10 seconds to midnight",
                    "on the first Monday of May at 10 seconds to midnight",
                )
            )
        if phrase == "5 past 10 on the first Monday in May":
            variants.extend(
                (
                    "5 past 10 on the first Monday of May",
                    "on the first Monday in May at 5 past 10",
                )
            )
        if phrase == "on the first Monday in May at 5 past 10":
            variants.extend(
                (
                    "the first Monday in May at 5 past 10",
                    "on the first Monday of May at 5 past 10",
                )
            )

    if seed.family == "mixed_precision":
        if phrase == "10 seconds to midnight on the middle of september":
            variants.extend(
                (
                    "10 seconds to midnight on mid september",
                    "10 seconds to midnight on mid-september",
                    "the middle of september at 10 seconds to midnight",
                )
            )
        if phrase == "the middle of september at 10 seconds to midnight":
            variants.extend(
                (
                    "middle of september at 10 seconds to midnight",
                    "mid september at 10 seconds to midnight",
                )
            )

    return _dedupe_keep_order([variant for variant in variants if variant != seed.phrase or True])


def _generate_composition_template_cases():
    cases = []

    for anchor in COMPOSITION_ANCHORS:
        anchor_dt = _parse_expected_datetime(anchor.expected)

        previous_tuesday = _previous_weekday(anchor_dt, 1)
        cases.append(
            VariantCase(
                phrase=f"the last tuesday before {anchor.phrase}",
                expected=_format_expected_datetime(previous_tuesday),
                family="composition_template",
                source_phrase=anchor.phrase,
            )
        )

        previous_friday = _previous_weekday(anchor_dt, 4)
        cases.append(
            VariantCase(
                phrase=f"the Friday before {anchor.phrase}",
                expected=_format_expected_datetime(previous_friday),
                family="composition_template",
                source_phrase=anchor.phrase,
            )
        )

        second_friday = _nth_weekday_after(anchor_dt, 4, 2)
        cases.append(
            VariantCase(
                phrase=f"2 fridays after {anchor.phrase}",
                expected=_format_expected_datetime(second_friday),
                family="composition_template",
                source_phrase=anchor.phrase,
            )
        )

        first_business = _first_business_day_after(anchor_dt)
        cases.append(
            VariantCase(
                phrase=f"the first business day after {anchor.phrase}",
                expected=_format_expected_datetime(first_business),
                family="composition_template",
                source_phrase=anchor.phrase,
            )
        )

        three_days_after = _apply_day_offset(anchor_dt, 3)
        cases.append(
            VariantCase(
                phrase=f"3 days after {anchor.phrase}",
                expected=_format_expected_datetime(three_days_after),
                family="composition_template",
                source_phrase=anchor.phrase,
            )
        )

        two_days_before = _apply_day_offset(anchor_dt, -2)
        cases.append(
            VariantCase(
                phrase=f"2 days before {anchor.phrase}",
                expected=_format_expected_datetime(two_days_before),
                family="composition_template",
                source_phrase=anchor.phrase,
            )
        )

        dusk = _set_solar_time(anchor_dt, "dusk")
        cases.append(
            VariantCase(
                phrase=f"at dusk on {anchor.phrase}",
                expected=_format_expected_datetime(dusk),
                family="composition_template",
                source_phrase=anchor.phrase,
            )
        )

        dawn = _set_solar_time(anchor_dt, "dawn")
        cases.append(
            VariantCase(
                phrase=f"at dawn on {anchor.phrase}",
                expected=_format_expected_datetime(dawn),
                family="composition_template",
                source_phrase=anchor.phrase,
            )
        )

        noon = _set_clock_time(anchor_dt, 12, 0)
        cases.append(
            VariantCase(
                phrase=f"noon on {anchor.phrase}",
                expected=_format_expected_datetime(noon),
                family="composition_template",
                source_phrase=anchor.phrase,
            )
        )

        evening = _set_clock_time(anchor_dt, 19, 0)
        cases.append(
            VariantCase(
                phrase=f"in the evening on {anchor.phrase}",
                expected=_format_expected_datetime(evening),
                family="composition_template",
                source_phrase=anchor.phrase,
            )
        )

        five_past_hour = anchor_dt.replace(minute=5, second=0)
        cases.append(
            VariantCase(
                phrase=f"5 minutes past the hour on {anchor.phrase}",
                expected=_format_expected_datetime(five_past_hour),
                family="composition_template",
                source_phrase=anchor.phrase,
            )
        )

        ten_four = _set_clock_time(_nth_weekday_after(anchor_dt, 4, 1), 10, 4)
        cases.append(
            VariantCase(
                phrase=f"at 4 past 10 on friday after {anchor.phrase}",
                expected=_format_expected_datetime(ten_four),
                family="composition_template",
                source_phrase=anchor.phrase,
            )
        )

    return cases


def _generate_supported_ladder_cases():
    cases = []
    for step in LADDER_STEPS:
        if step.expected is None:
            continue
        cases.append(
            VariantCase(
                phrase=step.phrase,
                expected=step.expected,
                family=step.family,
                source_phrase=step.source_phrase,
            )
        )
    return cases


def generate_variant_cases():
    cases = []
    for seed in SEED_CASES:
        for variant in _family_variants(seed):
            cases.append(
                VariantCase(
                    phrase=variant,
                    expected=seed.expected,
                    family=seed.family,
                    source_phrase=seed.phrase,
                )
            )
    cases.extend(_generate_composition_template_cases())
    cases.extend(_generate_supported_ladder_cases())
    expanded_cases = []
    for case in cases:
        expanded_cases.append(case)
        expanded_cases.extend(_positional_axis_cases(case))
    cases = expanded_cases
    unique = []
    seen = set()
    for case in cases:
        key = (case.phrase.lower(), case.expected, case.family, case.source_phrase)
        if key in seen:
            continue
        seen.add(key)
        unique.append(case)
    return unique


def generate_extraction_cases():
    wrappers = (
        "let's do it {phrase} please",
        "we should do {phrase} for the plan",
        "i think {phrase} works best",
    )
    cases = []
    for variant in generate_variant_cases():
        # Keep extraction cases focused on phrases that should be captured as one span.
        if len(variant.phrase.split()) < 2:
            continue
        for wrapper in wrappers:
            text = wrapper.format(phrase=variant.phrase)
            cases.append(
                ExtractionCase(
                    text=text,
                    expected_text=variant.phrase,
                    expected=variant.expected,
                    family=variant.family,
                    source_phrase=variant.source_phrase,
                )
            )

    unique = []
    seen = set()
    for case in cases:
        key = (case.text.lower(), case.expected_text.lower(), case.expected, case.family)
        if key in seen:
            continue
        seen.add(key)
        unique.append(case)
    return unique


def run_variant_sweep(reference=DEFAULT_REFERENCE):
    failures = []
    successes = []

    for case in generate_variant_cases():
        try:
            actual = str(Date(case.phrase, relative_to=reference))
        except Exception as exc:  # pragma: no cover
            failures.append(
                {
                    **asdict(case),
                    "actual": None,
                    "error": str(exc),
                }
            )
            continue

        record = {
            **asdict(case),
            "actual": actual,
        }
        if actual == case.expected:
            successes.append(record)
        else:
            failures.append(record)

    return {
        "reference": reference,
        "seed_count": len(SEED_CASES),
        "variant_count": len(successes) + len(failures),
        "success_count": len(successes),
        "failure_count": len(failures),
        "failures": failures,
    }


def run_extraction_sweep(reference=DEFAULT_REFERENCE):
    from stringtime import extract_dates

    failures = []
    successes = []

    for case in generate_extraction_cases():
        try:
            matches = extract_dates(case.text, relative_to=reference)
        except Exception as exc:  # pragma: no cover
            failures.append(
                {
                    **asdict(case),
                    "actual_text": None,
                    "actual": None,
                    "error": str(exc),
                }
            )
            continue

        if len(matches) != 1:
            failures.append(
                {
                    **asdict(case),
                    "actual_text": [match.text for match in matches],
                    "actual": [str(match.date) for match in matches],
                }
            )
            continue

        actual_text = matches[0].text
        actual = str(matches[0].date)
        record = {
            **asdict(case),
            "actual_text": actual_text,
            "actual": actual,
        }
        if actual_text == case.expected_text and actual == case.expected:
            successes.append(record)
        else:
            failures.append(record)

    return {
        "reference": reference,
        "seed_count": len(SEED_CASES),
        "extraction_variant_count": len(successes) + len(failures),
        "success_count": len(successes),
        "failure_count": len(failures),
        "failures": failures,
    }


def run_range_glue_sweep(reference=DEFAULT_REFERENCE):
    from stringtime import extract_dates, parse_natural_date_strict

    results = []
    supported_count = 0

    for seed in RANGE_GLUE_SEEDS:
        strict = parse_natural_date_strict(seed.phrase, relative_to=reference)
        strict_supported = strict is not None
        if strict_supported:
            supported_count += 1

        extraction_matches = extract_dates(seed.phrase, relative_to=reference)
        results.append(
            {
                "phrase": seed.phrase,
                "family": seed.family,
                "strict_supported": strict_supported,
                "strict_actual": str(strict) if strict is not None else None,
                "extracted_texts": [match.text for match in extraction_matches],
                "extracted_values": [str(match.date) for match in extraction_matches],
            }
        )

    return {
        "reference": reference,
        "seed_count": len(RANGE_GLUE_SEEDS),
        "supported_count": supported_count,
        "unsupported_count": len(RANGE_GLUE_SEEDS) - supported_count,
        "results": results,
    }


def run_ladder_sweep(reference=DEFAULT_REFERENCE):
    from stringtime import extract_dates, parse_natural_date_strict

    results = []
    supported_count = 0
    exploratory_count = 0

    for step in LADDER_STEPS:
        if step.expected is None:
            strict = parse_natural_date_strict(step.phrase, relative_to=reference)
            actual = str(strict) if strict is not None else None
            direct_supported = strict is not None
        else:
            try:
                actual = str(Date(step.phrase, relative_to=reference))
                direct_supported = True
            except Exception:  # pragma: no cover
                actual = None
                direct_supported = False
        extraction_matches = extract_dates(step.phrase, relative_to=reference)
        record = {
            "phrase": step.phrase,
            "family": step.family,
            "source_phrase": step.source_phrase,
            "expected": step.expected,
            "direct_supported": direct_supported,
            "direct_actual": actual,
            "extracted_texts": [match.text for match in extraction_matches],
            "extracted_values": [str(match.date) for match in extraction_matches],
        }

        if step.expected is None:
            exploratory_count += 1
        elif actual == step.expected:
            supported_count += 1

        results.append(record)

    return {
        "reference": reference,
        "seed_count": len(LADDER_STEPS),
        "supported_count": supported_count,
        "exploratory_count": exploratory_count,
        "results": results,
    }


def run_exploratory_structure_sweep(reference=DEFAULT_REFERENCE):
    from stringtime import extract_dates, parse_natural_date_strict

    results = []
    exact_count = 0

    for seed in EXPLORATORY_SEEDS:
        strict = parse_natural_date_strict(seed.phrase, relative_to=reference)
        extraction_matches = extract_dates(seed.phrase, relative_to=reference)
        if strict is not None:
            exact_count += 1
        results.append(
            {
                "phrase": seed.phrase,
                "family": seed.family,
                "expectation": seed.expectation,
                "strict_supported": strict is not None,
                "strict_actual": str(strict) if strict is not None else None,
                "extracted_texts": [match.text for match in extraction_matches],
                "extracted_values": [str(match.date) for match in extraction_matches],
            }
        )

    return {
        "reference": reference,
        "seed_count": len(EXPLORATORY_SEEDS),
        "exact_count": exact_count,
        "non_exact_count": len(EXPLORATORY_SEEDS) - exact_count,
        "results": results,
    }


def write_variant_failures(output_path, reference=DEFAULT_REFERENCE):
    result = run_variant_sweep(reference=reference)
    Path(output_path).write_text(json.dumps(result, indent=2) + "\n")
    return result


def write_extraction_failures(output_path, reference=DEFAULT_REFERENCE):
    result = run_extraction_sweep(reference=reference)
    Path(output_path).write_text(json.dumps(result, indent=2) + "\n")
    return result


def write_range_glue_failures(output_path, reference=DEFAULT_REFERENCE):
    result = run_range_glue_sweep(reference=reference)
    Path(output_path).write_text(json.dumps(result, indent=2) + "\n")
    return result


def write_ladder_failures(output_path, reference=DEFAULT_REFERENCE):
    result = run_ladder_sweep(reference=reference)
    Path(output_path).write_text(json.dumps(result, indent=2) + "\n")
    return result


def write_exploratory_structure_failures(output_path, reference=DEFAULT_REFERENCE):
    result = run_exploratory_structure_sweep(reference=reference)
    Path(output_path).write_text(json.dumps(result, indent=2) + "\n")
    return result
