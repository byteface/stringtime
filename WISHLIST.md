# Wishlist

Top 10 ideas for where `stringtime` could go next.


1. Add recurring schedule phrases

Handle `every Monday`, `every weekday at 9am`, `the first Friday of each month`, and similar repeating patterns.

2. Improve ambiguity reporting


3. Add ISO and machine-friendly output helpers

Expose methods for intervals, ranges, timezone-aware ISO strings, and easy conversion to Python `datetime` or JSON payloads.

4. Add strict and fuzzy parsing modes

Let callers choose between permissive behavior and a strict mode that rejects ambiguous or conflicting phrases.


5. Add date ranges

Handle phrases like `from next Friday to Sunday`, `between 3pm and 5pm tomorrow`, and `June 1st-3rd`.


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