# Wishlist

Top 10 ideas for where `stringtime` could go next.


1. Add recurring schedule phrases

Handle `every Monday`, `every weekday at 9am`, `the first Friday of each month`, and similar repeating patterns.


Still missing or only partly covered:

multi-day recurrence
every monday and wednesday
tuesdays and thursdays at 9
bounded recurrence
every friday until christmas
every monday through june
start/end windows
every day from 9 to 5
nth-interval with anchor detail
every 2nd tuesday
every 3rd month on the 14th
richer yearly rules
the last friday of every year
every first monday in april
recurrence with exclusions
every weekday except friday
business/calendar hybrids
every last business day of the quarter at 6pm
natural group recurrence
weeknights at 8
every morning
proper rule metadata
frequency
interval
byday lists
until
count
exclusions




2. Improve ambiguity reporting

also just ambiguity in general.

if I say in reality.. '2moro at 3' i don't mean 3am generally. So we need to be able to set it to favour afternoons if ambiguity occurs as a setting.


3. Add ISO and machine-friendly output helpers

Expose methods for intervals, ranges, timezone-aware ISO strings, and easy conversion to Python `datetime` or JSON payloads.

4. Add strict and fuzzy parsing modes

Let callers choose between permissive behavior and a strict mode that rejects ambiguous or conflicting phrases.


5. Add date ranges

Handle phrases like `from next Friday to Sunday`, `between 3pm and 5pm tomorrow`, and `June 1st-3rd`.

recurring with a range:
> each november 1st since 2020 until today  


6. 'I did it at 5'. would fail by putting a time in the future. so parsing
context of past or future from surrounding text could be useful bump.
We should be able to use some words to guess. did, was etc vs going, will

7. consideration around BC dates 
    - considered milliseconds backwards?


8. complex phrases
>>> matches = Date("the day before the twelth second of the 14th minute on the 2nd week of the first month 2321", extract=True)

- defuzzing
>>> matches = Date("around 12 i reckon on wednesday", extract=True)
>>> print(matches)
[DateMatch(text='12', start=7, end=9, date=<Date: 2026-03-13 12:00:00>), DateMatch(text='on wednesday', start=19, end=31, date=<Date: 2026-03-18 05:50:22>)]


10. astrological signs? chinese astrology


12. regional holidays or events

i.e. UK mothers day. maybe need to set region in API
regional working out high tides etc


20. phrases are generated from dates

there's a branch where this was started. but needs a lot of rework

21.
Demo fallsback when missing data. i.e. friday in august. (which) default to first and ask the question.

22. lots of repeated terms. need to clean code
