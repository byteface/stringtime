# stringtime

[![PyPI version](https://badge.fury.io/py/stringtime.svg)](https://badge.fury.io/py/stringtime.svg)
[![Downloads](https://pepy.tech/badge/stringtime)](https://pepy.tech/project/stringtime)
[![Python version](https://img.shields.io/pypi/pyversions/stringtime.svg?style=flat)](https://img.shields.io/pypi/pyversions/stringtime.svg?style=flat)
[![Python package](https://github.com/byteface/stringtime/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/byteface/stringtime/actions/workflows/python-package.yml)

A grammar for deriving Date objects from phrases.

## Usage

```bash
from stringtime import Date

d = Date('an hour from now')
d.day  # the day of the week 0-6
d.get_day(to_string=True) # the day name, e.g. 'Monday'
d.month  # the month 0-11
d.hour  # the hour 0-23
d.get_month(to_string=True) # the month name, e.g. 'January'

# also wraps dateutil.parser so can parse full date strings
d = Date("Sat Oct 11 17:13:46 UTC 2003")

# opt into timezone-aware output when the phrase includes a timezone suffix
d = Date("tomorrow at 5pm UTC", timezone_aware=True)
d.to_datetime().isoformat()  # '2020-12-26T17:00:00+00:00'

# change what relative phrases are based on instead of using "now"
d = Date("an hour from now", relative_to="2021-06-01 10:30:00")
str(d)  # '2021-06-01 11:30:00'

# relative_to can also be another parsed Date
d = Date("an hour from now", relative_to=Date("47 hours ago"))

# extract date phrases from longer sentences
matches = Date("I will do it in an hour from now.", extract=True)
matches[0].text  # 'in an hour from now'
str(matches[0].date)  # '2020-12-25 18:05:55'

# each parsed Date includes parse metadata
d = Date("Sat Oct 11 17:13:46 UTC 2003")
d.parse_metadata.used_dateutil  # True
d.parse_metadata.exact  # False

```

## Installation

```bash
python3 -m pip install stringtime
# python3 -m pip install stringtime --upgrade
```

Requires Python 3.10 or newer.

## Usage and API

Here's a list of example phrases that can be used...

```bash
"an hour from now"
"1 hour from now"
"1 hour ago"
"Today"
"Yesterday"
"Tomorrow"
"Tuesday"
"On Wednesday"
"In a minute"
"In an hour"
"20hrs from now"
"In a day/week/month/year"
"In 2 years"
"20mins in the future"
"20mins in the past"
"In 15 minutes"
"5 hours from now"
"20 minutes hence"
"10 minutes ago"
"3 business days from now"
"3 more sleeps"
"10 sleeps til xmas"
"next working day"
"chinese dentist"
"cowboy time"
"when the clock strikes 6"
"quarter past 5"
"half past 5"
"quarter to 6"
"today at noon"
"today at midnight"
"tomorrow noon"
"tomorrow midnight"
"midday"
"noon tomorrow"
"midnight on Friday"
"the first Monday in May"
"the 2nd Tuesday of next month"
"the last Friday in June"
"third Thursday of 2026"
"the penultimate Wednesday of the month"
"start of Q2"
"end of Q4"
"mid Q1 2027"
"first day of next quarter"
"last day of this quarter"
"end of business tomorrow"
"end of play"
"EOP"
"first thing in the morning"
"first thing"
"in the morning"
"tomorrow night"
"2moro night"
"Friday afternoon"
"lunchtime tomorrow"
"this evening"
"10 hours and 30 minutes from now"
"In a minute and 10 seconds"
"In a minute and a half"
"an hour and a half ago"
"two and a half hours"
"1.5 days"
"a quarter of an hour"
"three quarters of an hour"
"2.5 weeks"
"24 hours ago"
"3 weeks ago"
"30 seconds ago"
"1 hour before now"
"1 hour after now"
"1 hour ago"
"This Friday at 1"
"Last Wednesday at 5"
"Next Monday @ 7:15"
"7:15 Next Monday"
"Next Monday @ 7:15pm"
"Friday at 5:30"
"at 5 pm on Wednesday"
"at 5:52 pm"
# dates without a month specified will use the current month
"12th"
"twenty first"
"The 8th"
"On the 14th"
"January 14th"
"April the 1st"
"third of May"
"The first of September"
"The 12th of last month"
"next month on the first"
"last month on the 16th at 2am"
"tomorrow at 5pm UTC"
"next Friday 9am PST"
"tomorrow at 5pm UTC+2"
"32nd", # would move into the next month
"The 18th of March"
```

To see what else is underway check the tests/test_stringtime.py file.

For longer text, use `extract=True` or call `extract_dates(text)` directly to get
all matching spans back with their parsed dates.

Relative phrases are based on the current time by default, but you can override
that with `relative_to=`. It accepts a `stringtime.Date`, Python
`datetime.datetime`, `datetime.date`, string, or timestamp integer. The test
suite uses the same idea by freezing the reference date to
`2020-12-25 17:05:55` so relative phrases produce stable results.

Each returned `Date` also exposes `parse_metadata` with the original input,
what matched, whether the parse was exact or fuzzy, and whether parsing fell
back to `dateutil`.

Business-day phrases currently treat Monday-Friday as working days and skip
weekends only.

If anything is broken or you feel is missing please raise an issue or make a pull request.

## CLI

Use stringtime from the command line:

```bash
stringtime -p 2 days from now
```

## Dev

Clone the repo and install dev requirements:

```bash
python3 -m venv venv
. venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

to dev see the tests and add more or uncomment some that are not passing yet.

## Run tests

See the make file...

```bash
make test
```

## License

Do what you want with this code.

Uses David Beazley's PLY parser.

## Disclaimer

Might be buggy... still only recent
