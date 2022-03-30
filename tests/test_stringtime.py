"""
    test_stringtime
    ~~~~~~~~~~~~~~~
    unit tests for stringtime

"""

import datetime
import os

import pytest
import time_machine

import stringtime
from stringtime import Date


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


# pytest -s -v tests/test_stringtime.py::TestCaseStrict::test_assert_phrases
class TestCaseStrict:

    # note - if you change this the test will fail as they are relative to this date
    # it was arbitrarily chosen. Feel free to test other dates/times.
    FAKE_NOW = datetime.datetime(2020, 12, 25, 17, 5, 55)

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
            ("In a month", "2021-01-25 17:05:55"),
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
            ("12th", "2020-12-12 17:05:55"),
            ("the other day", "2020-12-23 17:05:55"),
            ("the day before yesterday", "2020-12-23 17:05:55"),
            ("after tomorrow", "2020-12-27 17:05:55"),
            ("before yesterday", "2020-12-23 17:05:55"),
            ("the day after tomorrow", "2020-12-27 17:05:55"),
            ("3 days", "2020-12-28 17:05:55"),
            ("A few days", "2020-12-28 17:05:55"),
            ("A few hours", "2020-12-25 20:05:55"),
            ("A few months away", "2021-03-25 17:05:55"),
            ("A few days ago", "2020-12-22 17:05:55"),
            ("A few days from now", "2020-12-28 17:05:55"),
            # ("A few weeks ago", "2020-12-04 17:05:55"),
            # ("A few weeks from now", "2021-01-04 17:05:55"),
            # ("The 12th of last month", "2020-11-12 17:05:55"),
            # ("12th of last month", "2020-11-12 17:05:55"),
            ("In a decade", "2030-12-25 17:05:55"),
            ("In a century", "2120-12-25 17:05:55"),
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
            ("at 5 pm", "2020-12-25 05:00:00"),
            # ("Friday at 5am", "2020-12-25 05:05:55"),
            # ("Friday at 5 PM", "2020-12-25 17:05:55"),
            # ("last century", "2100-12-25 17:05:55"),
            # ("next century", "2200-12-25 17:05:55"),
            ("this current moment", "2020-12-25 17:05:55"),
            ("here and now", "2020-12-25 17:05:55"),
            # ("Next Monday @ 7:15pm", "2020-12-29 19:15:55"),
            # ("Last Friday @ 7:15pm", "2020-12-25 19:15:55"),
            # ("lst thurs @ nine fifteen", "2020-12-25 19:15:55"),
            # ("the 20th @ 4", "2020-12-20 16:04:55"),
            # ("last month on the 16th @ 2am", "2020-11-16 02:05:55"),
            # ("next month on the first @ 3pm", "2020-12-01 15:03:55"),
            # ("friday at 5:30", "2020-12-25 17:30:55"),
            # ("10 hours and 30 minutes from now", "2020-12-25 19:35:55"),
            # ("10 hours and 30 minutes ago", "2020-12-25 15:25:55"),
            # ("In a minute and 10 seconds", "2020-12-25 17:06:15"),
            # ("In a minute and a half", "2020-12-25 17:06:55"),
            # ("In an hour and a half", "2020-12-25 18:06:55"),
            # ("In 4 hours time", "2020-12-25 21:05:55"),
            # ("In 4 hours and 30 minutes time", "2020-12-25 21:35:55"),
            # ("In 4 hours and 30 minutes and 10 seconds time", "2020-12-25 21:35:15"),
            # ("2 days time at 5", "2020-12-27 17:05:55"),
            # ("4 today", "2020-12-25 16:00:00"),
            # ("2moro at 3", "2020-12-27 03:00:00"),
        ],
    )
    @time_machine.travel(FAKE_NOW)
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
            # ("The 12th of last month", "2020-11-12 17:05:55"),
            # ("12th of last month", "2020-11-12 17:05:55"),
            # ("The first of Feb last year", "2020-03-18 17:05:55"),
        ],
    )
    @time_machine.travel(FAKE_NOW)
    def test_assert_dates(self, test_input, expected):
        assert str(check_phrase(test_input)) == expected

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (
                "Sat Oct 11 17:13:46 UTC 2003",
                "2003-10-11 17:13:46",
            ),  # test fallover nicely to dateutil
        ],
    )
    @time_machine.travel(FAKE_NOW)
    def test_assert_DEBUG_OFF(self, mocker, test_input, expected):
        mocker.patch("stringtime.DEBUG", False)
        assert str(check_phrase(test_input)) == expected


class TestCaseLazy:
    # tests that are not asserting anything

    def test_phrases(self):
        # test any single phrases
        check_phrase("In a minute")
        check_phrase("In an hour")
        check_phrase("20hrs from now")
        check_phrase("20mins in the future")
        check_phrase("In 15 minutes")
        check_phrase("5 hours from now")
        check_phrase("In the future 12 hours")
        check_phrase("20 minutes hence")
        check_phrase("10 minutes ago")
        check_phrase("2 hours ago")
        check_phrase("24 hours ago")
        check_phrase("3 weeks ago")
        check_phrase("30 seconds ago")
        check_phrase("1 hour before now")

        # check_phrase(f"now minus 1 hours") # no handlers for that yet
        # check_phrase(f"several hours from now") # several to generate random number

    def test_phrases_present(self):
        # tests for any possible phrases that get 'now' as a date

        # check_phrase(f"right now") # fails
        # check_phrase(f"now") # fails
        # check_phrase(f"this current moment") # fails
        # check_phrase(f"here and now") # fails
        # check_phrase(f"Immediatley") # fails
        pass

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

        # check_phrase(f"In 3 days")
        # check_phrase(f"In 5 minutes")
        # check_phrase(f"In 12 hours")
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

        # check_phrase(f"20 mins ago")  # works
        # check_phrase(f"10 secs ago")  # works?
        # check_phrase(f"10 hrs ago")  # works
        # check_phrase(f"10 wks ago")  # works - large day negation
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

        # check_phrase(f"Monday")
        # check_phrase(f"Last Tuesday")
        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
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
