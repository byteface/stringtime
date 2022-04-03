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

```

## Installation

```bash
python3 -m pip install stringtime
# python3 -m pip install stringtime --upgrade
```

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
"24 hours ago"
"3 weeks ago"
"30 seconds ago"
"1 hour before now"
"1 hour after now"
"1 hour ago"
"This Friday at 1"
"Last Wednesday at 5"
# dates without a month specified will use the current month
"12th"
"The 8th"
"On the 14th"
"January 14th"
"April the 1st"
"32nd", # would move into the next month
"The 18th of March"
```

To see what else is underway check the tests/test_stringtime.py file.

If anything is broken or you feel is missing please raise an issue or make a pull request.

## CLI

Use stringtime from the command line:

```bash
stringtime -p 2 days from now
```

## Dev

Clone the repo and install dev requirements:

```bash
python3 -m ven venv
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
