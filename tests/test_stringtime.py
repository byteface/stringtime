"""
    test_stringtime
    ~~~~~~~~~~~~~~~
    unit tests for stringtime

"""

import datetime
import os

import pytest

import stringtime
from stringtime import Date, after, extract_dates, is_after, is_before, is_same_day, is_same_time, until


def check_phrase(p: str):
    print("check_phrase:", p)
    d = Date(p)
    # print('  - The year is:::', d[0].get_year())
    # print('  - The month is:::', d[0].get_month(to_string=True))
    # print('  - The day is:::', d[0].get_date())
    # print('  - The hour is:::', d[0].get_hours())
    # print('  - The minute is:::', d[0].get_minutes())
    # print('  - The second is:::', d[0].get_seconds())
    print("- The date is :::", str(d))
    return d


REAL_DATETIME = datetime.datetime
FAKE_NOW = REAL_DATETIME(2020, 12, 25, 17, 5, 55)


class FrozenDateTime(REAL_DATETIME):
    @classmethod
    def now(cls, tz=None):
        if tz is not None:
            return FAKE_NOW.astimezone(tz)
        return FAKE_NOW

    @classmethod
    def utcnow(cls):
        return FAKE_NOW

    @classmethod
    def fromtimestamp(cls, ts, tz=None):
        if tz is not None:
            return REAL_DATETIME.fromtimestamp(ts, tz)
        return REAL_DATETIME.fromtimestamp(ts)


@pytest.fixture(autouse=True)
def freeze_now(monkeypatch):
    monkeypatch.setattr("stringtime.date.datetime.datetime", FrozenDateTime)


@pytest.fixture(autouse=True)
def clear_custom_holiday_registry():
    stringtime.clear_custom_holidays()
    yield
    stringtime.clear_custom_holidays()


def test_until_defaults_from_now_and_returns_plain_english():
    assert until(Date("valentines")) == "1 month, 2 weeks and 6 days"


def test_until_formats_compound_duration_between_two_values():
    assert (
        until(
            from_="2020-01-01 10:00:00",
            to="2024-04-15 10:05:00",
        )
        == "4 years, 3 months, 2 weeks and 5 minutes"
    )


def test_after_formats_duration_between_two_dates():
    assert (
        after(
            from_=Date("valentines"),
            to=Date("the last friday in March"),
        )
        == "1 month, 1 week and 6 days"
    )


def test_until_returns_zero_seconds_for_identical_datetimes():
    assert until(from_="2020-01-01 00:00:00", to="2020-01-01 00:00:00") == "0 seconds"


def test_is_before_returns_true_for_earlier_values():
    assert is_before("2020-01-01 00:00:00", "2020-01-01 00:00:01") is True


def test_is_after_returns_true_for_later_values():
    assert is_after(Date("tomorrow"), Date("today")) is True


def test_is_same_day_ignores_time_component():
    assert is_same_day("2020-12-25 01:00:00", "2020-12-25 23:59:59") is True


def test_is_same_time_ignores_date_component():
    assert is_same_time("2020-12-25 17:05:55", "2021-02-14 17:05:55") is True


# pytest -s -v tests/test_stringtime.py::TestCaseStrict::test_assert_phrases
class TestCaseStrict:

    # note - if you change this the test will fail as they are relative to this date
    # it was arbitrarily chosen. Feel free to test other dates/times.
    FAKE_NOW = FAKE_NOW

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            ("In a minute", "2020-12-25 17:06:55"),
            ("In an hour", "2020-12-25 18:05:55"),
            ("20hrs from now", "2020-12-26 13:05:55"),
            # create a bit of a roadmap # be careful. copilot made these stub dates.
            # you'll lose time if its wrong so double check first
            ("In a day", "2020-12-26 17:05:55"),
            ("In a week", "2021-01-01 17:05:55"),
            (
                "In a month",
                "2021-01-25 17:05:55",
            ),  # bugs for me on local using todays date. not mocked.
            ("In a year", "2021-12-25 17:05:55"),
            ("In 2 years", "2022-12-25 17:05:55"),
            ("20mins in the future", "2020-12-25 17:25:55"),
            ("20mins in the past", "2020-12-25 16:45:55"),
            ("10mins in the past", "2020-12-25 16:55:55"),
            ("In 15 minutes", "2020-12-25 17:20:55"),
            ("5 hours from now", "2020-12-25 22:05:55"),
            ("20 minutes hence", "2020-12-25 17:25:55"),
            ("10 minutes ago", "2020-12-25 16:55:55"),
            ("2 hours ago", "2020-12-25 15:05:55"),
            ("24 hours ago", "2020-12-24 17:05:55"),
            ("1 weeks ago", "2020-12-18 17:05:55"),
            ("2 weeks ago", "2020-12-11 17:05:55"),
            ("3 weeks ago", "2020-12-04 17:05:55"),
            ("30 seconds ago", "2020-12-25 17:05:25"),
            ("1 hour before now", "2020-12-25 16:05:55"),
            ("1 hour after now", "2020-12-25 18:05:55"),
            ("1 hour ago", "2020-12-25 16:05:55"),
            ("right now", "2020-12-25 17:05:55"),
            ("now", "2020-12-25 17:05:55"),
            ("right away", "2020-12-25 17:05:55"),
            ("immediately", "2020-12-25 17:05:55"),
            ("straight away", "2020-12-25 17:05:55"),
            ("at once", "2020-12-25 17:05:55"),
            ("as soon as possible", "2020-12-25 17:05:55"),
            ("asap", "2020-12-25 17:05:55"),
            ("here and now", "2020-12-25 17:05:55"),
            ("2 weeks from now", "2021-01-08 17:05:55"),
            ("3 business days from now", "2020-12-30 17:05:55"),
            ("3 more sleeps", "2020-12-28 17:05:55"),
            ("next working day", "2020-12-28 17:05:55"),
            ("chinese dentist", "2020-12-25 02:30:00"),
            ("cowboy time", "2020-12-25 09:50:00"),
            ("y2k", "2000-01-01 17:05:55"),
            ("when the clock strikes 6", "2020-12-25 06:00:00"),
            ("4 and twenty past 7", "2020-12-25 07:24:00"),
            ("quarter past 5", "2020-12-25 05:15:00"),
            ("half past 5", "2020-12-25 05:30:00"),
            ("quarter to 6", "2020-12-25 05:45:00"),
            ("today at noon", "2020-12-25 12:00:00"),
            ("2moro @ noonish", "2020-12-26 12:00:00"),
            ("the beginning of june", "2021-06-01 17:05:55"),
            ("today at midnight", "2020-12-25 00:00:00"),
            ("at first light tomorrow", "2020-12-26 07:25:00"),
            ("tomorrow noon", "2020-12-26 12:00:00"),
            ("tomorrow midnight", "2020-12-26 00:00:00"),
            ("midday", "2020-12-25 12:00:00"),
            ("noon tomorrow", "2020-12-26 12:00:00"),
            ("midnight on Friday", "2020-12-25 00:00:00"),
            ("midnight Friday", "2020-12-25 00:00:00"),
            ("the first Monday in May", "2020-05-04 17:05:55"),
            ("the 2nd Tuesday of next month", "2021-01-12 17:05:55"),
            ("the last Friday in June", "2020-06-26 17:05:55"),
            ("third Thursday of 2026", "2026-01-15 17:05:55"),
            ("the last Tuesday in 2026", "2026-12-29 17:05:55"),
            ("the last Wednesday in 2026", "2026-12-30 17:05:55"),
            ("the last Thursday in 2026", "2026-12-31 17:05:55"),
            ("the last Friday in 2026", "2026-12-25 17:05:55"),
            ("16th of december 76", "1976-12-16 17:05:55"),
            ("16th of december 06", "2006-12-16 17:05:55"),
            ("the 16th of december 1997", "1997-12-16 17:05:55"),
            ("7th of the 6th 81", "1981-06-07 17:05:55"),
            ("the 7th of the 6th eighty one", "1981-06-07 17:05:55"),
            ("the first of the 3rd 22 @ 3pm", "2022-03-01 15:00:00"),
            ("on the 5th day of the 6th month of year at 1pm", "2020-06-05 13:00:00"),
            ("dawn", "2020-12-26 07:25:00"),
            ("the 12th of the 12th @ dawn", "2020-12-12 07:25:00"),
            ("twilight on the 12th of the 12th", "2020-12-12 16:30:00"),
            ("twilight on the wednesday", "2020-12-30 16:30:00"),
            ("T minus 5 minutes", "2020-12-25 17:00:55"),
            ("T-minus 5 minutes", "2020-12-25 17:00:55"),
            (
                "1992 on the second tuesday of the first month at about 3ish",
                "1992-01-14 03:00:00",
            ),
            ("the penultimate Wednesday of the month", "2020-12-23 17:05:55"),
            ("start of Q2", "2020-04-01 17:05:55"),
            ("the start of Q2", "2020-04-01 17:05:55"),
            ("end of Q4", "2020-12-31 17:05:55"),
            ("mid Q1 2027", "2027-02-15 17:05:55"),
            ("middle of Q1 2027", "2027-02-15 17:05:55"),
            ("first day of next quarter", "2021-01-01 17:05:55"),
            ("last day of this quarter", "2020-12-31 17:05:55"),
            ("in the morning", "2020-12-26 09:00:00"),
            ("in the afternoon", "2020-12-26 15:00:00"),
            ("in the evening", "2020-12-25 19:00:00"),
            ("in the night", "2020-12-25 21:00:00"),
            ("tomorrow night", "2020-12-26 21:00:00"),
            ("half five tomorrow night", "2020-12-26 05:30:00"),
            ("5pm tomorrow night", "2020-12-26 17:00:00"),
            ("2moro night", "2020-12-26 21:00:00"),
            ("2mrw morning", "2020-12-26 09:00:00"),
            ("2day at noon", "2020-12-25 12:00:00"),
            ("tdy at noon", "2020-12-25 12:00:00"),
            ("tmrw nite", "2020-12-26 21:00:00"),
            ("tmoro night", "2020-12-26 21:00:00"),
            ("tomo night", "2020-12-26 21:00:00"),
            ("tonight", "2020-12-25 21:00:00"),
            ("2nite", "2020-12-25 21:00:00"),
            ("tonite", "2020-12-25 21:00:00"),
            ("tnite", "2020-12-25 21:00:00"),
            ("Friday afternoon", "2020-12-25 15:00:00"),
            ("Friday arvo", "2020-12-25 15:00:00"),
            ("on Tuesday afternoon", "2020-12-29 15:00:00"),
            ("on Friday evening", "2020-12-25 19:00:00"),
            ("lunchtime tomorrow", "2020-12-26 12:30:00"),
            ("on lunchtime tomorrow", "2020-12-26 12:30:00"),
            ("this evening", "2020-12-25 19:00:00"),
            ("next Tuesday evening", "2020-12-29 19:00:00"),
            ("the Wednesday after next", "2021-01-06 17:05:55"),
            ("Tuesday before last", "2020-12-15 17:05:55"),
            ("mid-morning", "2020-12-26 10:00:00"),
            ("early in the morning", "2020-12-26 06:00:00"),
            ("half five", "2020-12-25 05:30:00"),
            ("in a fortnight", "2021-01-08 17:05:55"),
            ("a fortnight ago", "2020-12-11 17:05:55"),
            ("bank holiday", "2020-12-25 17:05:55"),
            ("next bank holiday", "2020-12-28 17:05:55"),
            ("valentines", "2020-02-14 17:05:55"),
            ("next valentines", "2021-02-14 17:05:55"),
            ("pancake day", "2020-02-25 17:05:55"),
            ("shrove tuesday", "2020-02-25 17:05:55"),
            ("end of month", "2020-12-31 17:05:55"),
            ("end of the month", "2020-12-31 17:05:55"),
            ("the end of june", "2021-06-30 17:05:55"),
            ("the start of june", "2021-06-01 17:05:55"),
            ("the second to last day of the month", "2020-12-30 17:05:55"),
            ("the second-last day of the month", "2020-12-30 17:05:55"),
            ("the penultimate day of the month", "2020-12-30 17:05:55"),
            ("the last Sunday of the year", "2020-12-27 17:05:55"),
            ("the hundredth day of the year", "2020-04-09 17:05:55"),
            ("the hundreth day of the year", "2020-04-09 17:05:55"),
            ("the last day of the year", "2020-12-31 17:05:55"),
            ("a week before the last day of the year", "2020-12-24 17:05:55"),
            ("last day of February next year", "2021-02-28 17:05:55"),
            ("in the morrow", "2020-12-26 17:05:55"),
            ("on the morrow", "2020-12-26 17:05:55"),
            ("a week 2moro", "2021-01-02 17:05:55"),
            ("a week on monday", "2021-01-04 17:05:55"),
            ("a month on tuesday", "2021-01-29 17:05:55"),
            ("2 weeks on friday", "2021-01-08 17:05:55"),
            ("one month today", "2021-01-25 17:05:55"),
            ("at dinner time", "2020-12-25 18:00:00"),
            ("tea time", "2020-12-26 17:00:00"),
            ("Sunday @ about lunch time", "2020-12-27 12:30:00"),
            ("two Fridays from now", "2021-01-08 17:05:55"),
            ("Tuesday gone", "2020-12-22 17:05:55"),
            ("Tuesday past", "2020-12-22 17:05:55"),
            ("eom", "2020-12-31 17:05:55"),
            ("start of next quarter", "2021-01-01 17:05:55"),
            ("start of the next quarter", "2021-01-01 17:05:55"),
            ("close of year", "2020-12-31 17:05:55"),
            ("eoy", "2020-12-31 17:05:55"),
            ("the next leap year", "2024-01-01 17:05:55"),
            ("a day before the next leap year", "2023-12-31 17:05:55"),
            ("5 days from tomorrow", "2020-12-31 17:05:55"),
            ("2 days b4 monday", "2020-12-26 17:05:55"),
            ("3 days from next wednesday", "2021-01-02 17:05:55"),
            ("2 days before next wednesday", "2020-12-28 17:05:55"),
            ("3 years and 2 months before the 16th of december", "2017-10-16 17:05:55"),
            (
                "3 years and 2 months a week and a day after the 16th of december 1997",
                "2001-02-24 17:05:55",
            ),
            ("3 weeks ago at 2am", "2020-12-04 02:00:00"),
            ("3 weeks ago at 2 am", "2020-12-04 02:00:00"),
            ("3 weeks ago at 2 in the morning", "2020-12-04 02:00:00"),
            ("10 hours and 30 minutes before midnight", "2020-12-24 13:30:00"),
            ("an hour after 3 oclock", "2020-12-25 04:00:00"),
            ("15 minutes before midnight", "2020-12-24 23:45:00"),
            ("15 minutes before midnite", "2020-12-24 23:45:00"),
            ("1 second before midnight", "2020-12-24 23:59:59"),
            ("1 minute after the clock strikes 1", "2020-12-25 01:01:00"),
            ("when the clock strikes six", "2020-12-25 06:00:00"),
            ("end of business tomorrow", "2020-12-26 17:00:00"),
            ("eob tomorrow", "2020-12-26 17:00:00"),
            ("cob tomorrow", "2020-12-26 17:00:00"),
            ("close of business tomorrow", "2020-12-26 17:00:00"),
            ("end of play", "2020-12-25 17:00:00"),
            ("close of play", "2020-12-25 17:00:00"),
            ("EOP", "2020-12-25 17:00:00"),
            ("first thing in the morning", "2020-12-26 09:00:00"),
            ("first thing", "2020-12-26 09:00:00"),
            ("Christmas", "2020-12-25 17:05:55"),
            ("Christmas Eve", "2020-12-24 17:05:55"),
            ("New Year's Day", "2020-01-01 17:05:55"),
            ("Easter", "2020-04-12 17:05:55"),
            ("Easter next year", "2021-04-04 17:05:55"),
            ("Thanksgiving", "2020-11-26 17:05:55"),
            ("Black Friday", "2020-11-27 17:05:55"),
            ("Halloween", "2020-10-31 17:05:55"),
            ("Labor Day", "2020-09-07 17:05:55"),
            ("12th", "2020-12-12 17:05:55"),
            ("the other day", "2020-12-23 17:05:55"),
            ("the other night", "2020-12-24 21:00:00"),
            ("last night", "2020-12-24 21:00:00"),
            ("the night before last", "2020-12-23 21:00:00"),
            ("the night b4 last", "2020-12-23 21:00:00"),
            ("the night b4 yesterday", "2020-12-23 21:00:00"),
            ("the day before yesterday", "2020-12-23 17:05:55"),
            ("after tomorrow", "2020-12-27 17:05:55"),
            ("before yesterday", "2020-12-23 17:05:55"),
            ("the day after tomorrow", "2020-12-27 17:05:55"),
            ("3 days", "2020-12-28 17:05:55"),
            ("couple of weeks", "2021-01-08 17:05:55"),
            ("couple of weeks ago", "2020-12-11 17:05:55"),
            ("couple of minutes ago", "2020-12-25 17:03:55"),
            ("couple of hours ago", "2020-12-25 15:05:55"),
            ("couple of months ago", "2020-10-25 17:05:55"),
            ("couple of years ago", "2018-12-25 17:05:55"),
            ("few weeks ago", "2020-12-04 17:05:55"),
            ("few minutes ago", "2020-12-25 17:02:55"),
            ("few hours ago", "2020-12-25 14:05:55"),
            ("few months ago", "2020-09-25 17:05:55"),
            ("few years ago", "2017-12-25 17:05:55"),
            ("several weeks ago", "2020-12-07 17:05:55"),
            ("several years ago", "2013-12-25 17:05:55"),
            ("3 leap years ago", "2008-01-01 17:05:55"),
            ("several leap years ago", "1992-01-01 17:05:55"),
            ("few seconds ago", "2020-12-25 17:05:52"),
            ("few centuries ago", "1720-12-25 17:05:55"),
            ("couple of weeks before december", "2021-11-17 17:05:55"),
            ("few days after february finishes", "2021-03-03 17:05:55"),
            ("the 2nd week of january", "2021-01-08 17:05:55"),
            ("the day before the 2nd week of january", "2021-01-07 17:05:55"),
            ("the first week of last century", "1900-01-01 17:05:55"),
            ("the twelth second of the 14th minute", "2020-12-25 17:14:12"),
            ("the twelfth second of the 14th minute", "2020-12-25 17:14:12"),
            ("the 11th hour", "2020-12-25 11:00:00"),
            ("the eleventh hour", "2020-12-25 11:00:00"),
            (
                "the 14th minute on the 2nd week of the first month 2321",
                "2321-01-08 17:14:00",
            ),
            (
                "the twelth second of the 14th minute on the 2nd week of the first month 2321",
                "2321-01-08 17:14:12",
            ),
            (
                "the day before the twelth second of the 14th minute on the 2nd week of the first month 2321",
                "2321-01-07 17:14:12",
            ),
            ("on the morning of the 14th", "2020-12-14 09:00:00"),
            ("on the evening of the 14th", "2020-12-14 19:00:00"),
            (
                "in the evening on the first day of the month of December 2021",
                "2021-12-01 19:00:00",
            ),
            ("the fourteenth week after xmas", "2021-04-02 17:05:55"),
            ("the twelfth month", "2021-12-01 17:05:55"),
            ("the day before the twelfth month", "2021-11-30 17:05:55"),
            ("the day before the twelth month", "2021-11-30 17:05:55"),
            ("next wednsday", "2020-12-30 17:05:55"),
            ("16th of decemeber 76", "1976-12-16 17:05:55"),
            ("the 16th of janurary 1997", "1997-01-16 17:05:55"),
            ("A few days", "2020-12-28 17:05:55"),
            ("A few hours", "2020-12-25 20:05:55"),
            ("A few months away", "2021-03-25 17:05:55"),
            ("A few days ago", "2020-12-22 17:05:55"),
            ("A few days from now", "2020-12-28 17:05:55"),
            ("A few weeks ago", "2020-12-04 17:05:55"),
            ("A few weeks from now", "2021-01-15 17:05:55"),
            # ("The 12th of last month", "2020-11-12 17:05:55"),
            # ("12th of last month", "2020-12-12 17:05:55"),
            ("In a decade", "2030-12-25 17:05:55"),
            ("In a century", "2120-12-25 17:05:55"),
            # ("2 centuries", "2220-12-25 17:05:55"),
            ("In a millennium", "3020-12-25 17:05:55"),
            # ("In a century and a half", "2120-12-25 17:05:55"),
            # ("In a millennium and a half", "2300-12-25 17:05:55"),
            # ("In a decade and a half", "2220-12-25 17:05:55"),
            # ("The first of September", "2020-09-01 17:05:55"),
            # ("The 29th of jly lst yr", "2019-07-29 17:05:55"),
            # ("The 29th of jly this yr", "2020-07-29 17:05:55"),
            # ("The 29th of jly next yr", "2021-07-29 17:05:55"),
            # ("The 29th of jly last yr", "2018-07-29 17:05:55"),
            # ("The 12 th of last month", "2020-11-12 17:05:55"), #? allow errors like this?
            # ("Easter 2yrs ago", "2020-12-26 13:05:55"),
            # ("Easter 2yrs from now", "2020-12-26 13:05:55"),
            ("today", "2020-12-25 17:05:55"),
            ("tomorrow", "2020-12-26 17:05:55"),
            ("yesterday", "2020-12-24 17:05:55"),
            ("last week", "2020-12-18 17:05:55"),
            ("next week", "2021-01-01 17:05:55"),
            ("last month", "2020-11-25 17:05:55"),
            ("next month", "2021-01-25 17:05:55"),
            ("last year", "2019-12-25 17:05:55"),
            ("next year", "2021-12-25 17:05:55"),
            ("12 AM", "2020-12-25 00:00:00"),
            ("12pm", "2020-12-25 12:00:00"),
            ("at 5AM", "2020-12-25 05:00:00"),
            ("at 5 pm", "2020-12-25 17:00:00"),
            ("5 a.m.", "2020-12-25 05:00:00"),
            ("5 p.m.", "2020-12-25 17:00:00"),
            ("2:30 p.m.", "2020-12-25 14:30:00"),
            ("5 ante meridiem", "2020-12-25 05:00:00"),
            ("5 post meridiem", "2020-12-25 17:00:00"),
            (
                "Wednesday",
                "2020-12-30 17:05:55",
            ),  # first WEDNESDAY relative to FAKE DATE
            ("Thursday", "2020-12-31 17:05:55"),  # first THURSDAY relative to FAKE DATE
            ("Friday", "2020-12-25 17:05:55"),  # first FRIDAY relative to FAKE DATE
            ("on Wednesday", "2020-12-30 17:05:55"),
            (
                "2 days time at 4pm",
                "2020-12-27 16:00:00",
            ),  # DOUBLE DATE TEST (2days,at4pm). parses 2 phrases and merges
            ("2moro at 1", "2020-12-26 01:00:00"),
            ("at 5", "2020-12-25 05:00:00"),
            ("@1", "2020-12-25 01:00:00"),
            ("5", "2020-12-25 05:00:00"),
            ("5 oclock", "2020-12-25 05:00:00"),
            ("at 5 oclock", "2020-12-25 05:00:00"),
            (
                "wednesday at 5 pm",
                "2020-12-30 17:00:00",
            ),  # ? should this be 5:00:00? - does if parsed by double phrase
            # ("at 5 pm on Wednesday", "2020-12-30 17:00:00"),
            ("Thursday at 2am", "2020-12-31 02:00:00"),
            ("Friday at 5am", "2020-12-25 05:00:00"),
            ("Friday at 5 PM", "2020-12-25 17:00:00"),
            ("Last Thursday at 4am", "2020-12-24 04:00:00"),
            # ("last century", "2100-12-25 17:05:55"),
            # ("next century", "2200-12-25 17:05:55"),
            ("this current moment", "2020-12-25 17:05:55"),
            ("here and now", "2020-12-25 17:05:55"),
            ("a month ago", "2020-11-25 17:05:55"),
            ("a week ago", "2020-12-18 17:05:55"),
            ("a year ago", "2019-12-25 17:05:55"),
            # ("a decade ago", "2010-12-25 17:05:55"),
            # ("a century ago", "2100-12-25 17:05:55"),
            # ("a millennium ago", "3000-12-25 17:05:55"),
            # ("a decade from now", "2030-12-25 17:05:55"),
            # ("a century from now", "2200-12-25 17:05:55"),
            ("a hour from now", "2020-12-25 18:05:55"),
            ("a year from now", "2021-12-25 17:05:55"),
            ("a month from now", "2021-01-25 17:05:55"),
            ("a week from now", "2021-01-01 17:05:55"),
            ("2:57", "2020-12-25 02:57:00"),
            ("2:57pm", "2020-12-25 14:57:00"),
            ("at 5:52 pm", "2020-12-25 17:52:00"),
            ("at 5:52 am", "2020-12-25 05:52:00"),
            ("10 hours and 30 minutes from now", "2020-12-26 03:35:55"),
            ("10 hours and 30 minutes ago", "2020-12-25 06:35:55"),
            ("In a minute and 10 seconds", "2020-12-25 17:07:05"),
            ("In a minute and a half", "2020-12-25 17:07:25"),
            ("In an hour and a half", "2020-12-25 18:35:55"),
            ("an hour and a half", "2020-12-25 18:35:55"),
            ("an hour and a half ago", "2020-12-25 15:35:55"),
            ("two and a half hours", "2020-12-25 19:35:55"),
            ("1.5 days", "2020-12-27 05:05:55"),
            ("1.5 days ago", "2020-12-24 05:05:55"),
            ("1.5 hours from now", "2020-12-25 18:35:55"),
            ("a quarter of an hour", "2020-12-25 17:20:55"),
            ("three quarters of an hour", "2020-12-25 17:50:55"),
            ("2.5 weeks", "2021-01-12 05:05:55"),
            ("Next Monday @ 7:15", "2020-12-28 07:15:00"),
            ("7:15 Next Monday", "2020-12-28 07:15:00"),
            ("Next Monday @ 7:15pm", "2020-12-28 19:15:00"),
            # ("Last Friday @ 7:15pm", "2020-12-25 19:15:55"),
            # ("lst thurs @ nine fifteen", "2020-12-25 19:15:55"),
            # ("the 20th @ 4", "2020-12-20 16:04:55"),
            ("last month on the 16th @ 2am", "2020-11-16 02:00:00"),
            ("next month on 1st", "2021-01-01 17:05:55"),
            ("next month on the first @ 3pm", "2021-01-01 15:00:00"),
            ("friday at 5:30", "2020-12-25 05:30:00"),
            ("tomorrow at 5pm UTC", "2020-12-26 17:00:00"),
            ("next Friday 9am PST", "2021-01-01 09:00:00"),
            ("tomorrow at 5pm UTC+2", "2020-12-26 17:00:00"),
            # ("In 4 hours time", "2020-12-25 21:05:55"),
            # ("In 4 hours and 30 minutes time", "2020-12-25 21:35:55"),
            # ("In 4 hours and 30 minutes and 10 seconds time", "2020-12-25 21:35:15"),
            # ("2 days time at 5", "2020-12-27 17:05:55"),
            # ("4 today", "2020-12-25 16:00:00"),
            ("2moro at 3", "2020-12-26 03:00:00"),
            ("at 5 pm on Wednesday", "2020-12-30 17:00:00"),
            ("at 5:52 pm on Wednesday", "2020-12-30 17:52:00"),
            # ("Monday before last", "2020-12-22 17:05:55"),?date
        ],
    )
    def test_assert_phrases(self, test_input, expected):
        assert str(check_phrase(test_input)) == expected

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            ("12th", "2020-12-12 17:05:55"),
            ("12 th", "2020-12-12 17:05:55"),
            ("The 8th", "2020-12-08 17:05:55"),
            ("On the 14th", "2020-12-14 17:05:55"),
            ("January 14th", "2020-01-14 17:05:55"),
            ("April the 1st", "2020-04-01 17:05:55"),
            ("April the 14th", "2020-04-14 17:05:55"),
            ("November 2nd", "2020-11-02 17:05:55"),
            ("1st", "2020-12-01 17:05:55"),
            ("31st", "2020-12-31 17:05:55"),
            ("32nd", "2021-01-01 17:05:55"),  # cheeky!
            ("The 12th", "2020-12-12 17:05:55"),
            ("The 18th of March", "2020-03-18 17:05:55"),
            ("The first of September", "2020-09-01 17:05:55"),
            ("third of May", "2020-05-03 17:05:55"),
            ("twenty first", "2020-12-21 17:05:55"),
            ("thirtieth", "2020-12-30 17:05:55"),
            ("The 12th of last month", "2020-11-12 17:05:55"),
            ("12th of last month", "2020-11-12 17:05:55"),
            # ("The first of Feb last year", "2020-03-18 17:05:55"),
        ],
    )
    def test_assert_dates(self, test_input, expected):
        assert str(check_phrase(test_input)) == expected

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            ("19:35:55", "2020-12-25 19:35:55"),  # timestamps only
            ("2020-12-23", "2020-12-23 00:00:00"),  # datestamps only
            ("", "2020-12-25 17:05:55"),  # no date returns today
            (
                "Sat Oct 11 17:13:46 UTC 2003",
                "2003-10-11 17:13:46",
            ),  # test fallover nicely to dateutil
        ],
    )
    def test_assert_DEBUG_OFF(self, mocker, test_input, expected):
        mocker.patch("stringtime.DEBUG", False)
        assert str(check_phrase(test_input)) == expected

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            ("nOw", "2020-12-25 17:05:55"),
            ("todaY", "2020-12-25 17:05:55"),
            ("riGhT Now", "2020-12-25 17:05:55"),
            ("ImmeDiaTely", "2020-12-25 17:05:55"),
        ],
    )
    def test_present(self, mocker, test_input, expected):
        # mocker.patch("stringtime.DEBUG", False)
        assert str(check_phrase(test_input)) == expected

    def test_timezone_aware_output_utc(self):
        d = Date("tomorrow at 5pm UTC", timezone_aware=True)

        assert d.to_datetime().isoformat() == "2020-12-26T17:00:00+00:00"
        assert d.tzinfo.utcoffset(None) == datetime.timedelta(0)

    def test_timezone_aware_output_named_zone(self):
        d = Date("next Friday 9am PST", timezone_aware=True)

        assert d.to_datetime().isoformat() == "2021-01-01T09:00:00-08:00"
        assert d.tzinfo.tzname(None) == "PST"

    def test_timezone_aware_output_with_offset_suffix(self):
        d = Date("tomorrow at 5pm UTC+2", timezone_aware=True)

        assert d.to_datetime().isoformat() == "2020-12-26T17:00:00+02:00"

    def test_extract_dates_single_phrase_from_sentence(self):
        matches = extract_dates("I will do it in an hour from now after lunch.")

        assert len(matches) == 1
        assert matches[0].text == "in an hour from now"
        assert str(matches[0].date) == "2020-12-25 18:05:55"

    def test_extract_dates_prefers_full_anchor_offset_phrase(self):
        matches = extract_dates(
            "I will take a big walk in 5 days from tomorrow i think."
        )

        assert len(matches) == 1
        assert matches[0].text == "in 5 days from tomorrow"
        assert str(matches[0].date) == "2020-12-31 17:05:55"

    def test_extract_dates_prefers_full_anchor_offset_phrase_with_alias(self):
        matches = extract_dates("2 days b4 monday sounds fine")

        assert len(matches) == 1
        assert matches[0].text == "2 days b4 monday"
        assert str(matches[0].date) == "2020-12-26 17:05:55"

    def test_extract_dates_prefers_full_compound_anchor_offset_phrase(self):
        matches = extract_dates(
            "3 years and 2 months before the 16th of december sounds right."
        )

        assert len(matches) == 1
        assert matches[0].text == "3 years and 2 months before the 16th of december"
        assert str(matches[0].date) == "2017-10-16 17:05:55"

    def test_extract_dates_prefers_full_compound_anchor_offset_phrase_with_year(self):
        matches = extract_dates(
            "3 years and 2 months a week and a day after the 16th of december 1997"
        )

        assert len(matches) == 1
        assert (
            matches[0].text
            == "3 years and 2 months a week and a day after the 16th of december 1997"
        )
        assert str(matches[0].date) == "2001-02-24 17:05:55"

    def test_extract_dates_prefers_full_relative_phrase_with_specific_morning_time(self):
        matches = extract_dates("3 weeks ago at 2 in the morning")

        assert len(matches) == 1
        assert matches[0].text == "3 weeks ago at 2 in the morning"
        assert str(matches[0].date) == "2020-12-04 02:00:00"

    def test_extract_dates_prefers_full_before_midnight_phrase(self):
        matches = extract_dates("1 second before midnight")

        assert len(matches) == 1
        assert matches[0].text == "1 second before midnight"
        assert str(matches[0].date) == "2020-12-24 23:59:59"

    def test_extract_dates_prefers_full_clock_strikes_anchor_phrase(self):
        matches = extract_dates("1 minute after the clock strikes 1")

        assert len(matches) == 1
        assert matches[0].text == "1 minute after the clock strikes 1"
        assert str(matches[0].date) == "2020-12-25 01:01:00"

    def test_extract_dates_prefers_full_relative_weekday_phrase(self):
        matches = extract_dates(
            "Tuesday before last is good for me I think."
        )

        assert len(matches) == 1
        assert matches[0].text == "Tuesday before last"
        assert str(matches[0].date) == "2020-12-15 17:05:55"

    def test_extract_dates_handles_slang_aliases(self):
        matches = extract_dates("can you come 2moz at 7ish")

        assert len(matches) == 1
        assert matches[0].text == "2moz at 7ish"
        assert str(matches[0].date) == "2020-12-26 07:00:00"

    def test_extract_dates_handles_named_time_ish_alias(self):
        matches = extract_dates("2moro @ noonish works for me")

        assert len(matches) == 1
        assert matches[0].text == "2moro @ noonish"
        assert str(matches[0].date) == "2020-12-26 12:00:00"

    def test_extract_dates_handles_more_alias_variants(self):
        matches = extract_dates("let's catch up tmrw nite or at eob tomorrow")

        assert [match.text for match in matches] == [
            "tmrw nite",
            "eob tomorrow",
        ]
        assert [str(match.date) for match in matches] == [
            "2020-12-26 21:00:00",
            "2020-12-26 17:00:00",
        ]

    def test_extract_dates_handles_alias_sweep_variants(self):
        matches = extract_dates(
            "tonite works, or cob tomorrow, or maybe next wednsday arvo"
        )

        assert [match.text for match in matches] == [
            "tonite",
            "cob tomorrow",
            "next wednsday arvo",
        ]
        assert [str(match.date) for match in matches] == [
            "2020-12-25 21:00:00",
            "2020-12-26 17:00:00",
            "2020-12-30 15:00:00",
        ]

    def test_extract_dates_prefers_full_anchor_offset_with_article(self):
        matches = extract_dates("a week before the 15th works for me")

        assert len(matches) == 1
        assert matches[0].text == "a week before the 15th"
        assert str(matches[0].date) == "2020-12-08 17:05:55"

    def test_extract_dates_prefers_full_couple_anchor_offset_phrase(self):
        matches = extract_dates("let's aim for couple of weeks before december")

        assert len(matches) == 1
        assert matches[0].text == "couple of weeks before december"
        assert str(matches[0].date) == "2021-11-17 17:05:55"

    def test_extract_dates_prefers_full_ordinal_month_anchor_phrase(self):
        matches = extract_dates("the day before the twelth month works")

        assert len(matches) == 1
        assert matches[0].text == "the day before the twelth month"
        assert str(matches[0].date) == "2021-11-30 17:05:55"

    def test_extract_dates_prefers_full_ordinal_holiday_offset_phrase(self):
        matches = extract_dates("the fourteenth week after xmas sounds right")

        assert len(matches) == 1
        assert matches[0].text == "the fourteenth week after xmas"
        assert str(matches[0].date) == "2021-04-02 17:05:55"

    def test_extract_dates_prefers_full_week_of_month_anchor_phrase(self):
        matches = extract_dates("the day before the 2nd week of january works")

        assert len(matches) == 1
        assert matches[0].text == "the day before the 2nd week of january"
        assert str(matches[0].date) == "2021-01-07 17:05:55"

    def test_extract_dates_prefers_full_other_night_phrase(self):
        matches = extract_dates("the other night sounded good")

        assert len(matches) == 1
        assert matches[0].text == "the other night"
        assert str(matches[0].date) == "2020-12-24 21:00:00"

    def test_extract_dates_prefers_full_night_before_last_phrase(self):
        matches = extract_dates("the night b4 last sounded good")

        assert len(matches) == 1
        assert matches[0].text == "the night b4 last"
        assert str(matches[0].date) == "2020-12-23 21:00:00"

    def test_extract_dates_prefers_full_next_valentines_phrase(self):
        matches = extract_dates("next valentines")

        assert len(matches) == 1
        assert matches[0].text == "next valentines"
        assert str(matches[0].date) == "2021-02-14 17:05:55"

    def test_extract_dates_prefers_full_pancake_day_phrase(self):
        matches = extract_dates("pancake day")

        assert len(matches) == 1
        assert matches[0].text == "pancake day"
        assert str(matches[0].date) == "2020-02-25 17:05:55"

    def test_extract_dates_prefers_full_shrove_tuesday_phrase(self):
        matches = extract_dates("shrove tuesday")

        assert len(matches) == 1
        assert matches[0].text == "shrove tuesday"
        assert str(matches[0].date) == "2020-02-25 17:05:55"

    def test_extract_dates_prefers_full_night_before_yesterday_phrase(self):
        matches = extract_dates("the night b4 yesterday sounded good")

        assert len(matches) == 1
        assert matches[0].text == "the night b4 yesterday"
        assert str(matches[0].date) == "2020-12-23 21:00:00"

    def test_extract_dates_prefers_full_y2k_phrase(self):
        matches = extract_dates("y2k happened already")

        assert len(matches) == 1
        assert matches[0].text == "y2k"
        assert str(matches[0].date) == "2000-01-01 17:05:55"

    def test_extract_dates_prefers_full_four_and_twenty_past_phrase(self):
        matches = extract_dates("4 and twenty past 7 sounds fine")

        assert len(matches) == 1
        assert matches[0].text == "4 and twenty past 7"
        assert str(matches[0].date) == "2020-12-25 07:24:00"

    def test_extract_dates_prefers_full_on_part_of_day_phrase(self):
        matches = extract_dates("how about on tuesday afternoon")

        assert len(matches) == 1
        assert matches[0].text == "on tuesday afternoon"
        assert str(matches[0].date) == "2020-12-29 15:00:00"

    def test_extract_dates_handles_in_the_part_of_day_phrase(self):
        matches = extract_dates("let's do it in the afternoon")

        assert len(matches) == 1
        assert matches[0].text == "in the afternoon"
        assert str(matches[0].date) == "2020-12-26 15:00:00"

    def test_extract_dates_prefers_full_part_of_day_of_ordinal_phrase(self):
        matches = extract_dates("on the evening of the 14th sounds right")

        assert len(matches) == 1
        assert matches[0].text == "on the evening of the 14th"
        assert str(matches[0].date) == "2020-12-14 19:00:00"

    def test_extract_dates_prefers_full_part_of_day_on_boundary_phrase(self):
        matches = extract_dates(
            "in the evening on the first day of the month of December 2021"
        )

        assert len(matches) == 1
        assert (
            matches[0].text
            == "in the evening on the first day of the month of December 2021"
        )
        assert str(matches[0].date) == "2021-12-01 19:00:00"

    def test_extract_dates_prefers_full_numeric_ordinal_month_year_phrase(self):
        matches = extract_dates("the 7th of the 6th eighty one sounded good")

        assert len(matches) == 1
        assert matches[0].text == "the 7th of the 6th eighty one"
        assert str(matches[0].date) == "1981-06-07 17:05:55"

    def test_extract_dates_prefers_full_word_ordinal_month_year_time_phrase(self):
        matches = extract_dates("the first of the 3rd 22 @ 3pm")

        assert len(matches) == 1
        assert matches[0].text == "the first of the 3rd 22 @ 3pm"
        assert str(matches[0].date) == "2022-03-01 15:00:00"

    def test_extract_dates_prefers_full_ordinal_day_of_ordinal_month_phrase(self):
        matches = extract_dates("on the 5th day of the 6th month of year at 1pm")

        assert len(matches) == 1
        assert matches[0].text == "on the 5th day of the 6th month of year at 1pm"
        assert str(matches[0].date) == "2020-06-05 13:00:00"

    def test_extract_dates_handles_now_phrase(self):
        matches = extract_dates("now")

        assert len(matches) == 1
        assert matches[0].text == "now"
        assert str(matches[0].date) == "2020-12-25 17:05:55"

    def test_extract_dates_handles_right_now_phrase(self):
        matches = extract_dates("right now")

        assert len(matches) == 1
        assert matches[0].text == "right now"
        assert str(matches[0].date) == "2020-12-25 17:05:55"

    def test_extract_dates_prefers_full_month_boundary_phrase(self):
        matches = extract_dates("the end of june")

        assert len(matches) == 1
        assert matches[0].text == "the end of june"
        assert str(matches[0].date) == "2021-06-30 17:05:55"

    def test_extract_dates_prefers_full_month_start_phrase(self):
        matches = extract_dates("the start of june")

        assert len(matches) == 1
        assert matches[0].text == "the start of june"
        assert str(matches[0].date) == "2021-06-01 17:05:55"

    def test_extract_dates_prefers_full_second_to_last_day_phrase(self):
        matches = extract_dates("the second to last day of the month")

        assert len(matches) == 1
        assert matches[0].text == "the second to last day of the month"
        assert str(matches[0].date) == "2020-12-30 17:05:55"

    def test_extract_dates_prefers_full_last_weekday_of_year_phrase(self):
        matches = extract_dates("the last Sunday of the year")

        assert len(matches) == 1
        assert matches[0].text == "the last Sunday of the year"
        assert str(matches[0].date) == "2020-12-27 17:05:55"

    def test_extract_dates_prefers_full_last_day_of_year_phrase(self):
        matches = extract_dates("the last day of the year")

        assert len(matches) == 1
        assert matches[0].text == "the last day of the year"
        assert str(matches[0].date) == "2020-12-31 17:05:55"

    def test_extract_dates_prefers_full_hundredth_day_of_year_phrase(self):
        matches = extract_dates("the hundredth day of the year")

        assert len(matches) == 1
        assert matches[0].text == "the hundredth day of the year"
        assert str(matches[0].date) == "2020-04-09 17:05:55"

    def test_extract_dates_prefers_full_hundreth_day_of_year_phrase(self):
        matches = extract_dates("the hundreth day of the year")

        assert len(matches) == 1
        assert matches[0].text == "the hundreth day of the year"
        assert str(matches[0].date) == "2020-04-09 17:05:55"

    def test_extract_dates_prefers_full_last_day_of_month_next_year_phrase(self):
        matches = extract_dates("last day of February next year")

        assert len(matches) == 1
        assert matches[0].text == "last day of February next year"
        assert str(matches[0].date) == "2021-02-28 17:05:55"

    def test_extract_dates_prefers_full_a_week_tomorrow_phrase(self):
        matches = extract_dates("a week 2moro")

        assert len(matches) == 1
        assert matches[0].text == "a week 2moro"
        assert str(matches[0].date) == "2021-01-02 17:05:55"

    def test_extract_dates_prefers_full_a_week_on_monday_phrase(self):
        matches = extract_dates("a week on monday")

        assert len(matches) == 1
        assert matches[0].text == "a week on monday"
        assert str(matches[0].date) == "2021-01-04 17:05:55"

    def test_extract_dates_prefers_full_week_before_last_day_of_year_phrase(self):
        matches = extract_dates("a week before the last day of the year")

        assert len(matches) == 1
        assert matches[0].text == "a week before the last day of the year"
        assert str(matches[0].date) == "2020-12-24 17:05:55"

    def test_extract_dates_prefers_full_one_month_today_phrase(self):
        matches = extract_dates("one month today")

        assert len(matches) == 1
        assert matches[0].text == "one month today"
        assert str(matches[0].date) == "2021-01-25 17:05:55"

    def test_extract_dates_prefers_full_dinner_time_phrase(self):
        matches = extract_dates("at dinner time")

        assert len(matches) == 1
        assert matches[0].text == "at dinner time"
        assert str(matches[0].date) == "2020-12-25 18:00:00"

    def test_extract_dates_prefers_full_about_lunch_time_phrase(self):
        matches = extract_dates("Sunday @ about lunch time")

        assert len(matches) == 1
        assert matches[0].text == "Sunday @ about lunch time"
        assert str(matches[0].date) == "2020-12-27 12:30:00"

    def test_extract_dates_prefers_full_two_fridays_from_now_phrase(self):
        matches = extract_dates("two Fridays from now")

        assert len(matches) == 1
        assert matches[0].text == "two Fridays from now"
        assert str(matches[0].date) == "2021-01-08 17:05:55"

    def test_extract_dates_prefers_full_tuesday_gone_phrase(self):
        matches = extract_dates("Tuesday gone")

        assert len(matches) == 1
        assert matches[0].text == "Tuesday gone"
        assert str(matches[0].date) == "2020-12-22 17:05:55"

    def test_extract_dates_prefers_full_tuesday_past_phrase(self):
        matches = extract_dates("Tuesday past")

        assert len(matches) == 1
        assert matches[0].text == "Tuesday past"
        assert str(matches[0].date) == "2020-12-22 17:05:55"

    def test_extract_dates_prefers_full_t_minus_phrase(self):
        matches = extract_dates("T minus 5 minutes")

        assert len(matches) == 1
        assert matches[0].text == "T minus 5 minutes"
        assert str(matches[0].date) == "2020-12-25 17:00:55"

    def test_extract_dates_prefers_full_t_minus_hyphen_phrase(self):
        matches = extract_dates("T-minus 5 minutes")

        assert len(matches) == 1
        assert matches[0].text == "T-minus 5 minutes"
        assert str(matches[0].date) == "2020-12-25 17:00:55"

    def test_extract_dates_prefers_full_solar_event_phrase(self):
        matches = extract_dates("twilight on the 12th of the 12th")

        assert len(matches) == 1
        assert matches[0].text == "twilight on the 12th of the 12th"
        assert str(matches[0].date) == "2020-12-12 16:30:00"

    def test_extract_dates_prefers_full_solar_event_weekday_phrase(self):
        matches = extract_dates("twilight on the wednesday")

        assert len(matches) == 1
        assert matches[0].text == "twilight on the wednesday"
        assert str(matches[0].date) == "2020-12-30 16:30:00"

    def test_extract_dates_prefers_full_solar_event_at_date_phrase(self):
        matches = extract_dates("the 12th of the 12th @ dawn")

        assert len(matches) == 1
        assert matches[0].text == "the 12th of the 12th @ dawn"
        assert str(matches[0].date) == "2020-12-12 07:25:00"

    def test_extract_dates_prefers_full_first_light_phrase(self):
        matches = extract_dates("at first light tomorrow")

        assert len(matches) == 1
        assert matches[0].text == "at first light tomorrow"
        assert str(matches[0].date) == "2020-12-26 07:25:00"

    def test_extract_dates_prefers_full_year_prefixed_ordinal_weekday_phrase(self):
        matches = extract_dates(
            "1992 on the second tuesday of the first month at about 3ish"
        )

        assert len(matches) == 1
        assert (
            matches[0].text
            == "1992 on the second tuesday of the first month at about 3ish"
        )
        assert str(matches[0].date) == "1992-01-14 03:00:00"

    def test_extract_dates_prefers_full_week_of_last_century_phrase(self):
        matches = extract_dates("the first week of last century")

        assert len(matches) == 1
        assert matches[0].text == "the first week of last century"
        assert str(matches[0].date) == "1900-01-01 17:05:55"

    def test_extract_dates_prefers_full_ordinal_second_of_minute_phrase(self):
        matches = extract_dates("the twelth second of the 14th minute")

        assert len(matches) == 1
        assert matches[0].text == "the twelth second of the 14th minute"
        assert str(matches[0].date) == "2020-12-25 17:14:12"

    def test_extract_dates_prefers_full_ordinal_hour_phrase(self):
        matches = extract_dates("the 11th hour")

        assert len(matches) == 1
        assert matches[0].text == "the 11th hour"
        assert str(matches[0].date) == "2020-12-25 11:00:00"

    def test_extract_dates_prefers_full_ordinal_second_minute_on_anchor_phrase(self):
        matches = extract_dates(
            "the twelth second of the 14th minute on the 2nd week of the first month 2321"
        )

        assert len(matches) == 1
        assert (
            matches[0].text
            == "the twelth second of the 14th minute on the 2nd week of the first month 2321"
        )
        assert str(matches[0].date) == "2321-01-08 17:14:12"

    def test_extract_dates_prefers_full_day_before_nested_ordinal_time_phrase(self):
        matches = extract_dates(
            "the day before the twelth second of the 14th minute on the 2nd week of the first month 2321"
        )

        assert len(matches) == 1
        assert (
            matches[0].text
            == "the day before the twelth second of the 14th minute on the 2nd week of the first month 2321"
        )
        assert str(matches[0].date) == "2321-01-07 17:14:12"

    def test_extract_dates_prefers_full_explicit_time_then_part_of_day_phrase(self):
        matches = extract_dates("half five tomorrow night")

        assert len(matches) == 1
        assert matches[0].text == "half five tomorrow night"
        assert str(matches[0].date) == "2020-12-26 05:30:00"

    def test_extract_dates_prefers_full_leap_year_anchor_phrase(self):
        matches = extract_dates("a day before the next leap year")

        assert len(matches) == 1
        assert matches[0].text == "a day before the next leap year"
        assert str(matches[0].date) == "2023-12-31 17:05:55"

    def test_extract_dates_prefers_full_leap_year_offset_phrase(self):
        matches = extract_dates("several leap years ago")

        assert len(matches) == 1
        assert matches[0].text == "several leap years ago"
        assert str(matches[0].date) == "1992-01-01 17:05:55"

    def test_extract_dates_multiple_phrases_from_sentence(self):
        matches = extract_dates(
            "Let's meet next Friday at 9am PST, or Christmas Eve at 5pm UTC."
        )

        assert [match.text for match in matches] == [
            "next Friday at 9am PST",
            "Christmas Eve at 5pm UTC",
        ]
        assert [str(match.date) for match in matches] == [
            "2021-01-01 09:00:00",
            "2020-12-24 17:00:00",
        ]

    def test_extract_dates_can_return_timezone_aware_matches(self):
        matches = extract_dates(
            "Let's meet tomorrow at 5pm UTC.",
            timezone_aware=True,
        )

        assert len(matches) == 1
        assert matches[0].date.to_datetime().isoformat() == "2020-12-26T17:00:00+00:00"

    def test_date_extract_mode_returns_matches(self):
        matches = Date("I will do it in an hour from now.", extract=True)

        assert len(matches) == 1
        assert matches[0].text == "in an hour from now"

    def test_extract_dates_returns_empty_when_no_phrase_found(self):
        assert extract_dates("There are no schedules in this sentence.") == []

    def test_relative_to_string_changes_reference_now(self):
        d = Date("an hour from now", relative_to="2021-06-01 10:30:00")

        assert str(d) == "2021-06-01 11:30:00"

    def test_relative_to_datetime_changes_reference_now(self):
        d = Date(
            "tomorrow at 5pm",
            relative_to=datetime.datetime(2021, 6, 1, 10, 30, 0),
        )

        assert str(d) == "2021-06-02 17:00:00"

    def test_relative_to_applies_to_sentence_extraction(self):
        matches = extract_dates(
            "I will do it in an hour from now.",
            relative_to="2021-06-01 10:30:00",
        )

        assert len(matches) == 1
        assert str(matches[0].date) == "2021-06-01 11:30:00"

    def test_empty_string_uses_relative_to_reference(self):
        d = Date("", relative_to="2021-06-01 10:30:00")

        assert str(d) == "2021-06-01 10:30:00"

    def test_sleeps_until_christmas(self):
        d = Date("10 sleeps til xmas", relative_to="2020-12-15 17:05:55")

        assert str(d) == "2020-12-15 17:05:55"

    def test_parse_metadata_for_exact_parser_match(self):
        d = Date("an hour from now")

        assert d.parse_metadata.matched_text == "an hour from now"
        assert d.parse_metadata.exact is True
        assert d.parse_metadata.fuzzy is False
        assert d.parse_metadata.used_dateutil is False
        assert d.parse_metadata.semantic_kind == "relative_offset"
        assert d.parse_metadata.representative_granularity == "second"

    def test_parse_metadata_for_dateutil_fallback(self):
        d = Date("Sat Oct 11 17:13:46 UTC 2003")

        assert d.parse_metadata.matched_text == "Sat Oct 11 17:13:46 UTC 2003"
        assert d.parse_metadata.exact is False
        assert d.parse_metadata.fuzzy is False
        assert d.parse_metadata.used_dateutil is True

    def test_parse_metadata_for_extracted_match(self):
        matches = extract_dates("I will do it in an hour from now after lunch.")

        assert matches[0].date.parse_metadata.matched_text == "in an hour from now"
        assert matches[0].date.parse_metadata.exact is False
        assert matches[0].date.parse_metadata.fuzzy is True
        assert matches[0].date.parse_metadata.used_dateutil is False

    def test_parse_metadata_marks_day_phrase_as_period(self):
        d = Date("Friday")

        assert d.parse_metadata.semantic_kind == "period"
        assert d.parse_metadata.representative_granularity == "day"

    def test_parse_metadata_marks_boundary_phrase(self):
        d = Date("end of month", relative_to="2020-12-25 17:05:55")

        assert d.parse_metadata.semantic_kind == "boundary"
        assert d.parse_metadata.representative_granularity == "month"

    def test_parse_metadata_marks_part_of_day_phrase(self):
        d = Date("tomorrow night", relative_to="2020-12-25 17:05:55")

        assert d.parse_metadata.semantic_kind == "period"
        assert d.parse_metadata.representative_granularity == "part_of_day"


class TestCaseLazy:
    # tests that are not asserting anything

    def test_phrases_future(self):
        # tests for phrases that retrieve dates in the past
        # : x {time} from now : i.e. '5 weeks from now'
        # normal/expected grammars
        # times = ['second']
        # times = ['day']
        # times = ['month']
        # times = ['day']
        # times = ['week']
        # times = ['hour']
        # times = ['year', 'month', 'week', 'day']
        # times = ['year', 'month', 'week', 'day', 'hour', 'minute']
        times = ["year", "month", "week", "day", "hour", "minute", "second"]
        for n in range(100):
            # print(n)
            for t in times:
                check_phrase(f"{n} {t} from now")
                check_phrase(f"{n} {t}s from now")  # plurals

        # bad grammars (allowed)
        # check_phrase("One day")

        # : x {time} time : i.e. '5 days time'
        for n in range(100):
            for t in times:
                # plural
                check_phrase(f"{n} {t}s time")
                # w/o plural (bad grammar allowed)
                check_phrase(f"{n} {t} time")

        for n in range(100):
            for t in times:
                check_phrase(f"{n} {t}s in the future")
                check_phrase(f"{n} {t}s after now")
                # check_phrase(f"{n} {t}s after now beyond this current moment") # starting failing?

        # check_phrase(f"29 seconds in the future") # fails???

        # In 3 days, In 5 minutes, In 12 hours
        for n in range(100):
            for t in times:
                check_phrase(f"In {n} {t}s")

        for n in range(100):
            for t in times:
                check_phrase(f"+ {n} {t}")
                check_phrase(f"- {n} {t}")
                check_phrase(f"+{n} {t}")
                check_phrase(f"-{n} {t}")

        # check_phrase(f"+1 hour before now") # SHOULD fail as it forces 2 conflicting choices

        # TODO - check results of these
        for n in range(100):
            for t in times:
                check_phrase(f"{n} {t}")

        check_phrase(
            "Today plus 1 hours"
        )  # hmmm would this be 1 hour into next day? not current time?
        check_phrase("now add 1 hours")
        check_phrase("In a minute")
        check_phrase("In an hour")
        check_phrase("In 10 mins")
        check_phrase("In 10mins")
        check_phrase("In 10 dys")
        check_phrase("In 10 secs")
        check_phrase("5 secs from now")

    def test_phrases_past(self):
        # tests for phrases that retrieve dates in the past

        # check_phrase("A minutes ago")  # fails when ticked over
        check_phrase("1 minutes ago")  # fails when ticked over

        # 20 mins ago, 10 secs ago, 10 hrs ago, 10 wks ago
        times = ["yr", "mnth", "wk", "dy", "hr", "min", "sec"]
        for n in range(100):
            for t in times:
                check_phrase(f"{n} {t} ago")  # works
                check_phrase(f"{n} {t}s ago")  # works

        # check_phrase(f"10ms ago")  # fails millisecond unexpected
        # check_phrase(f"10s ago")  # fails
        # check_phrase(f"10m ago")  # fails
        # check_phrase(f"10H ago")  # fails not doing 'H' yet

        # check_phrase(f"yeserday at 3:15") # fails. typo

        # forgotton space
        # check_phrase(f"10days ago") # fails - cant go backwards that far yet

        # check_phrase(f"A moment ago")  # a moment is a specific unit of time. i think 90secs?

    def test_phrases_yesterday_2moro_2day(self):
        # yesterday/2moro/2day
        check_phrase("yesterday")
        check_phrase("tomorrow")
        check_phrase("tomorrow at 5")
        check_phrase("yesterday at 3")
        # check_phrase(f"2moro")  # fails
        # check_phrase(f"today")  # fails
        # check_phrase(f"2day @ 5pm")  # fails

    def test_phrases_days_of_the_week(self):
        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        # Monday, Last Tuesday, Next Wednesday... etc
        for d in days:
            check_phrase(f"{d}")
            # check_phrase(f"{d} at 5") # TODO
            # check_phrase(f"{d} at 5pm") # TODO
            check_phrase(f"Next {d}")
            # check_phrase(f"Next Monday @ 7:15pm in the afteroon")  #TODO
            # check_phrase(f"Next Monday @ 9:15pm in the evening")  #TODO
            # check_phrase(f"Next Monday @ 9:15pm in the morning")  # SHOULD ERROR DUE TO CONFLICTING CONDITIONS
            # find previous nearest day
            check_phrase(f"Last {d}")

        # slang day names...
        days = ["Mon", "tues", "Wed", "Thurs", "Fri", "Sat", "Sun"]
        for d in days:
            check_phrase(f"{d}")
            check_phrase(f"Next {d}")
            # check_phrase(f"On {d}") # TODO
            # check_phrase(f"Last {d} @ 11:15am")  #fails

    # def test_quick_check(self):
    # TODO - maybe drop parsing when have enough info rather than create more conditions?
    # check_phrase(f"In an hour from now") # fails
    # check_phrase(f"In 10 minutes from now") #fails


def test_builtin_holiday_catalog_is_large():
    assert stringtime.builtin_holiday_definition_count() >= 80
    assert stringtime.builtin_holiday_alias_count() >= 300


def test_custom_holiday_registration_supports_fixed_and_year_specific_sources():
    stringtime.register_holiday_date(
        "founders day",
        7,
        15,
        aliases=("founders", "foundation day"),
    )
    stringtime.register_holiday_dates(
        "launch day",
        {
            2020: "2020-03-20",
            2021: "2021-03-19",
        },
        aliases=("product launch day",),
    )

    assert str(Date("founders day")) == "2020-07-15 17:05:55"
    assert str(Date("foundation day")) == "2020-07-15 17:05:55"
    assert str(Date("launch day")) == "2020-03-20 17:05:55"

    matches = extract_dates("maybe product launch day and founders")
    assert [match.text for match in matches] == ["product launch day", "founders"]
    assert [str(match.date) for match in matches] == [
        "2020-03-20 17:05:55",
        "2020-07-15 17:05:55",
    ]
