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
    print('inputted phrase:', p)
    d = get_date(p)
    # print('  - The year is:::', d[0].get_year())
    # print('  - The month is:::', d[0].get_month(to_string=True))
    # print('  - The day is:::', d[0].get_date())
    # print('  - The hour is:::', d[0].get_hours())
    # print('  - The minute is:::', d[0].get_minutes())
    # print('  - The second is:::', d[0].get_seconds())
    print('  - The date is :::', str(d[0]))
    return d[0]


class TestCase(unittest.TestCase):

    def test_phrases(self):
        # : x {time} from now : i.e. '5 weeks from now'
        # normal/expected grammars
        times = ['year', 'month', 'week', 'day', 'hour', 'minute', 'second']
        # times = ['second']
        # times = ['day']
        # times = ['year', 'month', 'week', 'day']
        # times = ['month']
        # times = ['day']
        # times = ['week']
        # times = ['hour']
        # times = ['year', 'month', 'week', 'day', 'hour', 'minute']
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
                check_phrase(f"{n} {t}s time")  # plural
                check_phrase(f"{n} {t} time")  # w/o plural (bad grammar allowed)

        check_phrase(f"8 days in the future")
        check_phrase(f"8 minutes in the future")
        # check_phrase(f"29 seconds in the future") # fails???
        check_phrase(f"8 minutes after now")
        check_phrase(f"6 hours beyond this current moment")

        check_phrase(f"In three days")
        check_phrase(f"In 3 days")
        check_phrase(f"In 5 minutes")
        check_phrase(f"In 12 hours")
        check_phrase(f"In the future 12 hours")
        # check_phrase(f"20 minutes hence") # fails
        # check_phrase(f"10 minutes ago") # fails when has to tick over
        check_phrase(f"2 hours ago")
        # check_phrase(f"24 hours ago") # fails - so only at tick over
        # check_phrase(f"3 weeks ago") # fails - probably same reasons
        # check_phrase(f"30 seconds ago") # fails
        check_phrase(f"1 hour before now")
        check_phrase(f"+ 1 hour")
        # check_phrase(f"+1 hour before now") # SHOULD fail as it forces 2 conflicting choices
        check_phrase(f"- 1 hour")
        check_phrase(f"+1 hour")
        check_phrase(f"-1 hour")

        # TODO
        # check_phrase(f"1 hour")
        # check_phrase(f"1 day")
        # check_phrase(f"1 week")

        check_phrase(f"In a minute")
        check_phrase(f"Today plus 1 hours")  # hmmm would this be 1 hour into next day? not current time?
        check_phrase(f"now add 1 hours")
        # check_phrase(f"now minus 1 hours") # no handlers for that yet

        check_phrase(f"In 15 minutes")
        check_phrase(f"5 hours from now")
        # check_phrase(f"several hours from now") # several to generate random number
        check_phrase(f"In a minute")
        check_phrase(f"In an hour")

        # TODO - maybe drop parseing when have enough info rather than create more conditions?
        # check_phrase(f"In an hour from now") # fails
        # check_phrase(f"In 10 minutes from now") #fails

        # check_phrase(f"right now") # fails
        # check_phrase(f"now") # fails
        check_phrase(f"1 minutes ago") # fails when ticked over

        check_phrase(f"In 10 mins") # works
        check_phrase(f"In 10mins") # works
        check_phrase(f"In 10 secs") # fails??
        check_phrase(f"In 10 dys") # works

        # check_phrase(f"5 secs from now") # fails

        check_phrase(f"10 mins ago") #works
        check_phrase(f"20 mins ago") #works
        check_phrase(f"10 secs ago") #works?
        check_phrase(f"10 hrs ago") #works
        check_phrase(f"10 wks ago") #works - large day negation
        # check_phrase(f"10s ago") # fails
        # check_phrase(f"10m ago") # fails
        # check_phrase(f"10H ago") # fails not doing 'H' yet
        check_phrase(f"10hrs ago") # fails
        # check_phrase(f"10ms ago") # fails millisecond unexpected
        check_phrase(f"20hrs from now") # works
        check_phrase(f"20mins in the future") # works

        check_phrase(f"yesterday") # works - 2moro reverse days is not working
        check_phrase(f"tomorrow") # works
        check_phrase(f"tomorrow at 5") # works
        check_phrase(f"yesterday at 3") # works

        check_phrase(f"Monday") # works
        check_phrase(f"Tuesday") # works
        check_phrase(f"Wednesday") # works
        check_phrase(f"Thursday") # works
        # check_phrase(f"Friday") # works
        # check_phrase(f"Saturday") # works

        check_phrase(f"Last Monday") # works
        check_phrase(f"Last Tuesday") # works
        check_phrase(f"Last Wednesday") # works
        check_phrase(f"Last Thursday") # works
        check_phrase(f"Last Friday") # works
        check_phrase(f"Last Saturday") # works

        check_phrase(f"Next Monday") # works
        check_phrase(f"Next Tuesday") # works
        check_phrase(f"Next Wednesday") # works
        check_phrase(f"Next Thursday") # works
        # check_phrase(f"Last Friday") # works
        # check_phrase(f"Last Saturday") # works

        check_phrase(f"Mon") # works
        check_phrase(f"Tues") # works
        check_phrase(f"Wed") # works
        check_phrase(f"Thurs") # works
        # check_phrase(f"Fri") # works
        # check_phrase(f"Sat") # works

        # check_phrase(f"On Mon") # works
        # check_phrase(f"On Tues") # works
        # check_phrase(f"On Wed") # works
        # check_phrase(f"On Thurs") # works
        # check_phrase(f"On Fri") # works
        # check_phrase(f"On Sat") # works

        # check_phrase(f"yeserday at 3:15") # fails

        # forgotton space
        # check_phrase(f"10days ago") # fails - cant go backwards that far yet


if __name__ == '__main__':
    unittest.main()
