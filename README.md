# stringtime

[![PyPI version](https://badge.fury.io/py/stringtime.svg)](https://badge.fury.io/py/stringtime.svg)
[![Downloads](https://pepy.tech/badge/stringtime)](https://pepy.tech/project/stringtime)
[![Python version](https://img.shields.io/pypi/pyversions/stringtime.svg?style=flat)](https://img.shields.io/pypi/pyversions/stringtime.svg?style=flat)
[![Python package](https://github.com/byteface/stringtime/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/byteface/stringtime/actions/workflows/python-package.yml)

A grammar for deriving Date objects from phrases.

## Usage

```bash
from stringtime import Date, Phrase, after, is_after, is_before, is_same_day, is_same_time, nearest_phrase_for, nearest_phrases_for, phrase_for, phrases_for, until

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

# reverse lookup from a datetime/date string to a known phrase
Phrase("2021-01-01 17:05:55", relative_to="2020-12-25 17:05:55")
# 'start of next quarter'

phrase_for("2021-01-01 17:05:55", relative_to="2020-12-25 17:05:55")
phrases_for("2021-01-01 17:05:55", relative_to="2020-12-25 17:05:55")

# nearest lookup is available for datetimes that do not have an exact registry hit
nearest_phrase_for("2021-01-01 12:34:56", relative_to="2020-12-25 17:05:55")
nearest_phrases_for("2037-06-01 12:34:56", relative_to="2020-12-25 17:05:55")

# plain-English durations between two dates
until(Date("valentines"))
# '1 month, 2 weeks and 6 days'

# Python reserves "from", so the keyword form is from_=
until(from_="2020-01-01 10:00:00", to="2024-04-15 10:05:00")
# '4 years, 3 months, 2 weeks and 5 minutes'

after(from_=Date("valentines"), to=Date("the last friday in March"))
# '1 month, 1 week and 6 days'

# readable comparisons
is_before("2020-01-01 00:00:00", "2020-01-01 00:00:01")
is_after(Date("tomorrow"), Date("today"))
is_same_day("2020-12-25 01:00:00", "2020-12-25 23:59:59")
is_same_time("2020-12-25 17:05:55", "2021-02-14 17:05:55")

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

## CLI

```bash
stringtime "an hour from now"
stringtime --relative-to "2020-12-25 17:05:55" "tomorrow night"
stringtime --extract "I will do it in 5 days from tomorrow."
stringtime --reverse --relative-to "2020-12-25 17:05:55" "2021-01-01 17:05:55"
stringtime --nearest --all --json "2021-01-01 12:34:56"
stringtime --metadata --json "Friday"
```

Useful flags:

```bash
--extract         find date phrases inside longer text
--reverse         reverse an exact datetime into a known phrase
--nearest         find the nearest known reverse phrase
--all             return all matches/candidates in extract or reverse modes
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

- a phrase input with parse, extract, reverse, and nearest-reverse modes
- a simple calendar that jumps to the resolved date
- a metadata panel showing parse semantics directly
- a raw JSON log showing metadata and extraction matches

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
"next Tuesday evening"
"the Wednesday after next"
"mid-morning"
"early in the morning"
"half five"
"in a fortnight"
"a fortnight ago"
"bank holiday"
"next bank holiday"
"end of month"
"start of next quarter"
"close of year"
"5 days from tomorrow"
"3 days from next Wednesday"
"2 days before next Wednesday"
"an hour after 3 oclock"
"15 minutes before midnight"
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

Useful fields on `parse_metadata` include:

- `input_text`: the original phrase
- `matched_text`: the span that actually matched
- `normalized_text`: the normalized phrase string used by the parser
- `exact`: `True` for native exact parses, `False` for fuzzy or fallback paths
- `fuzzy`: `True` when the parser matched a phrase inside larger text
- `used_dateutil`: `True` when parsing fell back to `dateutil`
- `semantic_kind`: the kind of thing the phrase represents, such as `date`,
  `boundary`, `period`, `relative_offset`, or `recurring`
- `representative_granularity`: the main grain of the result, such as `second`,
  `day`, `week`, `month`, `quarter`, `season`, or `part_of_day`

That metadata is also what the local demo uses in its dedicated metadata panel,
so you can see when a phrase was interpreted as recurring, boundary-like, or a
fuzzy extracted match instead of a plain exact date.

Business-day phrases currently treat Monday-Friday as working days and skip
weekends only.

## Phrase Registry

There is now a phrase-registry builder that expands many known template
families, parses them against a fixed reference date, and writes out both a
flat corpus and a reverse map of `datetime -> phrases`.

Generate it with:

```bash
make registry
```

That produces:

```bash
data/phrase_registry.json
data/phrase_reverse_map.json
data/phrase_reverse_records.json
data/phrase_registry_failures.json
```

The default build uses `relative_to="2020-12-25 17:05:55"` so relative phrases
are deterministic. The reverse outputs now include a canonical phrase choice
per datetime along with the full set of known variants, which is the starting
point for turning datetimes back into natural phrases. The runtime helpers
`Phrase(...)`, `phrase_for(...)`, and `phrases_for(...)` use that same exact
registry data for reverse lookup. `nearest_phrase_for(...)` and
`nearest_phrases_for(...)` provide an in-memory nearest-date search on top of
the same registry when there is no exact match.

The registry also now distinguishes between semantic kinds such as `instant`,
`period`, `boundary`, and `relative_offset`. See
[SEMANTIC_REGISTRY.md](/Users/byteface/Desktop/projects/stringtime/SEMANTIC_REGISTRY.md)
for the current model and next steps.

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
