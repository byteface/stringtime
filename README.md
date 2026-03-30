# stringtime

[![PyPI version](https://badge.fury.io/py/stringtime.svg)](https://badge.fury.io/py/stringtime.svg)
[![Downloads](https://pepy.tech/badge/stringtime)](https://pepy.tech/project/stringtime)
[![Python version](https://img.shields.io/pypi/pyversions/stringtime.svg?style=flat)](https://img.shields.io/pypi/pyversions/stringtime.svg?style=flat)
[![Python package](https://github.com/byteface/stringtime/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/byteface/stringtime/actions/workflows/python-package.yml)

A grammar for deriving `Date` objects from natural-language phrases.

## Usage

```python
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

# bias ambiguous bare-hour phrases when there is no stronger cue
d = Date("tomorrow at 3", ambiguous_meridiem="pm")
str(d)  # '2020-12-26 15:00:00'

# explicit meridiems and stronger cues still win
Date("tomorrow at 3am", ambiguous_meridiem="pm")
Date("tomorrow at 3 in the afternoon", ambiguous_meridiem="am")

# bias ambiguous weekday/month phrases toward the past, future, or nearest match
d = Date("Wednesday", ambiguous_direction="past")
str(d)  # e.g. '2020-12-23 17:05:55'

Date("in February", ambiguous_direction="future")
Date("Friday", ambiguous_direction="nearest")

# control how slash dates are interpreted when needed
d = Date("26/7/2027 at 2pm")
str(d)  # '2027-07-26 14:00:00'

Date("7/8/99", date_order="dmy")
Date("7/8/99", date_order="mdy")

# unbounded sentinel dates are available too
d = Date("forever")
str(d)  # '∞'
d.parse_metadata.semantic_kind  # 'infinity'

# a few equivalent phrases resolve to the same sentinel
Date("the end of time")
Date("eternity")

# extract date phrases from longer sentences
matches = Date("I will do it in an hour from now.", extract=True)
matches[0].text  # 'in an hour from now'
str(matches[0].date)  # '2020-12-25 18:05:55'

# each parsed Date includes parse metadata
d = Date("Sat Oct 11 17:13:46 UTC 2003")
d.parse_metadata.used_dateutil  # True
d.parse_metadata.exact  # False
```

There's also various utilities.

```python
from stringtime import until, after

# plain-English durations between two dates
until(Date("valentines"))
# '1 month, 2 weeks and 6 days'

# Python reserves "from", so the keyword form is from_=
until(from_="2020-01-01 10:00:00", to="2024-04-15 10:05:00")
# '4 years, 3 months, 2 weeks and 5 minutes'

after(from_=Date("valentines"), to=Date("the last friday in March"))
# '1 month, 1 week and 6 days'


from stringtime import is_after, is_before, is_same_day, is_same_time

# readable comparisons
is_before("2020-01-01 00:00:00", "2020-01-01 00:00:01")
is_after(Date("tomorrow"), Date("today"))
is_same_day("2020-12-25 01:00:00", "2020-12-25 23:59:59")
is_same_time("2020-12-25 17:05:55", "2021-02-14 17:05:55")
```

## Installation

```bash
python3 -m pip install stringtime
# python3 -m pip install stringtime --upgrade
```

Tested in CI on Python 3.10 through 3.14. Requires Python 3.10 or newer.

## CLI

```bash
stringtime "an hour from now"
stringtime --relative-to "2020-12-25 17:05:55" "tomorrow night"
stringtime --extract "I will do it in 5 days from tomorrow."
stringtime --metadata --json "Friday"
echo "2 days from now" | stringtime --relative-to "2020-12-25 17:05:55"
```

Useful flags:

```bash
--extract         find date phrases inside longer text
--all             return all matches in extract mode
--relative-to     set the reference datetime for relative phrases
--timezone-aware  keep timezone info when the phrase includes a timezone suffix
--metadata        include parse metadata in the output
--json            print structured JSON output
```

## Demo App

There is also a small local demo app in [demo/README.md](demo/README.md). It is
not part of the deployed package; it is just there to make it easier to show
what the parser is doing.

Run it from the project root:

```bash
python3 -m pip install -r requirements-dev.txt
make demo
```

It runs on `http://127.0.0.1:5050` by default.

The demo gives you:

- a phrase input with parse and extract modes
- a simple calendar that jumps to the resolved date
- a metadata panel showing parse semantics directly
- a raw JSON log showing metadata and extraction matches

There is also some functionality for uses a best guess when a phrase can't be parsed as a single string. Which is explained in the README for the demo.

## Usage and API

`stringtime` is not limited to one narrow phrase style. It handles a mix of:

- relative offsets: `an hour from now`, `3 weeks ago`, `10 minutes hence`
- weekdays and ordinals: `Friday`, `the first Monday in May`, `the penultimate Wednesday of the month`
- times and spoken clocks: `7:15pm`, `quarter past 5`, `10 seconds to midnight`
- combined date/time forms: `2pm september 1st 2029`, `at 5 pm on Wednesday`
- business and boundary phrases: `end of month`, `end of play`, `the first business day after fiscal year end`
- seasonal, holiday, solar, and lunar anchors: `next summer`, `xmas eve`, `dusk on Friday`, `the next full moon`
- recurring and sentinel phrases: `every Wednesday`, `forever`
- chained relative offsets: `plus 1 week 2 days 4 hours 2 seconds`
- signed offset chains: `+1 week 2 days 4 hours 2 seconds`
- separator variants: `+1 week, 2 days, 4 hours` and `+1 week +2 days`
- compact date anchors with relative math: `20080229 -1 year`
- dashed date anchors with relative math: `2008-02-29 -1 year`
- short year phrases like `back in 82`

For 2-digit years:
- `00` to `69` map to the 2000s
- `70` to `99` map to the 1900s

A few quick examples:

```bash
"an hour from now"
"Tuesday"
"quarter past 5"
"today at noon"
"the first Monday in May"
"end of business tomorrow"
"the last Friday in June"
"next Tuesday evening"
"3 days from next Wednesday"
"2pm september 1st 2029"
"tomorrow at 5pm UTC"
"the next full moon"
"every Wednesday"
"forever"
# Let's go even further!
"the day before the twelfth second of the 14th minute on the 2nd week of the first month 2321 plus 1 hour"
```

For a broader real-world sample, look through:

- [tests/test_stringtime.py](/Users/byteface/Desktop/projects/stringtime/tests/test_stringtime.py)
- [demo/README.md](/Users/byteface/Desktop/projects/stringtime/demo/README.md)

For longer text, use `extract=True` or call `extract_dates(text)` directly to get
all matching spans back with their parsed dates.

Relative phrases are based on the current time by default, but you can override
that with `relative_to=`. It accepts a `stringtime.Date`, Python
`datetime.datetime`, `datetime.date`, string, or timestamp integer.

If you want ambiguous bare-hour phrases such as `tomorrow at 3` to lean one way,
you can pass `ambiguous_meridiem="am"` or `ambiguous_meridiem="pm"`. This only
applies when the phrase does not already contain a stronger cue such as `am`,
`pm`, `morning`, `afternoon`, `noon`, or `midnight`.

If you want ambiguous calendar phrases such as `Wednesday`, `on Wednesday`, or
`in February` to lean one way, you can pass
`ambiguous_direction="past"`, `"future"`, or `"nearest"`. This only applies to
phrases that do not already contain an explicit directional cue such as `next`,
`last`, or an explicit year.

For slash-separated numeric dates, you can pass `date_order="dmy"` or
`date_order="mdy"` to force day-first or month-first parsing. If you leave
`date_order` unset, stringtime only parses slash dates natively when the order
is already unambiguous, such as `26/7/99`. If either side is greater than `12`,
that impossible month/day check wins regardless of the chosen `date_order`.

Each returned `Date` also exposes `parse_metadata` with the original input,
what matched, whether the parse was exact or fuzzy, and whether parsing fell
back to `dateutil`.

Useful fields on `parse_metadata` include:

- `input_text`: the original phrase
- `matched_text`: the span that actually matched
- `normalized_text`: the normalized phrase string used by the parser
- `exact`: `True` for native exact parses, `False` for fuzzy or fallback paths
- `fuzzy`: `True` when the parser matched a phrase inside larger text
- `used_dateutil`: `True` when parsing fell back to `dateutil`
- `semantic_kind`: the kind of thing the phrase represents, such as `date`,
  `boundary`, `period`, `relative_offset`, `recurring`, or `infinity`
- `representative_granularity`: the main grain of the result, such as `second`,
  `day`, `week`, `month`, `quarter`, `season`, `part_of_day`, or `unbounded`

That metadata is also what the local demo uses in its dedicated metadata panel,
so you can see when a phrase was interpreted as recurring, boundary-like, or a
fuzzy extracted match instead of a plain exact date.

`Date("forever")` returns an infinite sentinel date rather than a normal finite
timestamp. It compares after any finite date and carries `semantic_kind` of
`infinity` in its metadata.

Business-day phrases currently treat Monday-Friday as working days and skip
weekends only.


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

The test suite freezes the reference date to `2020-12-25 17:05:55` so relative phrases produce stable test results.

## License

Do what you want with this code.

Uses David Beazley's PLY parser.

## Disclaimer

If you hit a phrase that stringtime cannot parse yet, please feel free to raise an issue or open a pull request.

See WISHLIST.md for upcoming features.
