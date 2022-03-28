# coding: utf8
"""
    test_stringtime
    ~~~~~~~~~~~~~~~
    unit tests for stringtime

"""

import os
import unittest
# from unittest.mock import Mock

# import requests
# from mock import patch
# from inspect import stack

from stringtime import get_date


def check_phrase(p: str):
    print('check_phrase:', p)
    d = get_date(p)
    # print('  - The year is:::', d[0].get_year())
    # print('  - The month is:::', d[0].get_month(to_string=True))
    # print('  - The day is:::', d[0].get_date())
    # print('  - The hour is:::', d[0].get_hours())
    # print('  - The minute is:::', d[0].get_minutes())
    # print('  - The second is:::', d[0].get_seconds())
    print('- The date is :::', str(d[0]))
    return d[0]


class TestCase(unittest.TestCase):

    def test_phrases(self):
        # test any single phrases
        check_phrase("In a minute")
        check_phrase("In an hour")
        check_phrase("20hrs from now")
        check_phrase("20mins in the future")
        check_phrase("In 15 minutes")
        check_phrase("5 hours from now")
        check_phrase("In the future 12 hours")

        # check_phrase(f"20 minutes hence") # fails
        # check_phrase(f"10 minutes ago") # fails when has to tick over

        check_phrase("2 hours ago")
        # check_phrase(f"24 hours ago") # fails - so only at tick over
        # check_phrase(f"3 weeks ago") # fails - probably same reasons
        # check_phrase(f"30 seconds ago") # fails
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
        times = ['year', 'month', 'week', 'day', 'hour', 'minute', 'second']
        for n in range(100):
            print(n)
            for t in times:
                check_phrase(f"{n} {t} from now")
                check_phrase(f"{n} {t}s from now")  # plurals

        # bad grammars (allowed)
        # check_phrase("One day")

        # : x {time} time : i.e. '5 days time'
        for n in range(100):
            for t in times:
                # plural
                check_phrase(f"{n} {t}s time")
                # w/o plural (bad grammar allowed)
                check_phrase(f"{n} {t} time")

        for n in range(100):
            for t in times:
                check_phrase(f"{n} {t}s in the future")
                check_phrase(f"{n} {t}s after now")
                check_phrase(f"{n} {t}s after now beyond this current moment")

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

        # TODO
        # for n in range(100):
            # for t in times:
        # check_phrase(f"1 hour")
        # check_phrase(f"1 day")
        # check_phrase(f"1 week")

        check_phrase("Today plus 1 hours")  # hmmm would this be 1 hour into next day? not current time?
        check_phrase("now add 1 hours")

        check_phrase("In a minute")
        check_phrase("In an hour")

        # TODO - maybe drop parsing when have enough info rather than create more conditions?
        # check_phrase(f"In an hour from now") # fails
        # check_phrase(f"In 10 minutes from now") #fails

        check_phrase("In 10 mins")
        check_phrase("In 10mins")
        check_phrase("In 10 dys")
        check_phrase("In 10 secs")  # fails??

        # check_phrase(f"5 secs from now") # fails

    def test_phrases_past(self):
        # tests for phrases that retrieve dates in the past

        # check_phrase("A minutes ago")  # fails when ticked over
        check_phrase("1 minutes ago")  # fails when ticked over

        # check_phrase(f"20 mins ago")  # works
        # check_phrase(f"10 secs ago")  # works?
        # check_phrase(f"10 hrs ago")  # works
        # check_phrase(f"10 wks ago")  # works - large day negation
        times = ['yr', 'mnth', 'wk', 'dy', 'hr', 'min', 'sec']
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
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for d in days:
            check_phrase(f"{d}")
            check_phrase(f"{d} at 5")
            check_phrase(f"{d} at 5pm")
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
            check_phrase(f"On {d}")

            # check_phrase(f"Last {d} @ 11:15am")  #fails


if __name__ == '__main__':
    unittest.main()
