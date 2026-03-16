# Wishlist

Top 10 ideas for where `stringtime` could go next.

1. phrases are generated from dates

Pass 1. Build the phrase registry

Generate a deterministic corpus of known phrases and parse them against a fixed
reference date so we have a reproducible `phrase -> representative datetime`
map plus grouped reverse buckets.

Pass 2. Add reverse lookup APIs

Support exact reverse lookup with helpers like `Phrase(...)`,
`phrase_for(...)`, and `phrases_for(...)`, then add nearest-match lookup for
non-exact datetimes.

Pass 3. Preserve semantic meaning in parser output

Make parser results expose semantic kinds such as `instant`, `period`,
`boundary`, and `relative_offset` so reverse phrasing is not relying only on
flat timestamps.

Pass 4. Unify parser semantics and registry semantics

Stop duplicating intuition across parser and registry layers. Each parse path
should declare its semantics directly, and the registry should become an export
of that parser-emitted meaning.

Pass 5. Distinguish representative timestamps from true meaning

Support phrases that are really periods or boundaries, such as `Friday`,
`morning`, `end of month`, and holiday phrases, without pretending they are
just exact instants.

Pass 6. Introduce ambiguity-aware reverse phrasing

Handle phrases like `xmas`, `Friday`, or `morning` as potentially ambiguous or
multi-interpretation concepts instead of forcing a single exact datetime.

Pass 7. Improve canonical phrase selection

Rank reverse candidates using semantic kind, locale, style, and naturalness so
generated phrases feel intentional and human.

Pass 8. Add fallback phrase synthesis

When there is no exact registry hit, generate best-effort phrases from semantic
structure instead of only returning nearest known examples.

Pass 9. Decide on storage strategy only if scale demands it

Keep JSON and maybe CSV while the model is evolving. Consider SQLite only after
query patterns and corpus size prove it is worth the added complexity.

Pass 10. Build evaluation and regression tooling

Add corpora, golden reverse-phrase cases, and fuzz/property-style tests so we
can measure whether reverse generation is actually getting better.


2. Add recurring schedule phrases

Handle `every Monday`, `every weekday at 9am`, `the first Friday of each month`, and similar repeating patterns.

3. Improve ambiguity reporting

Detect phrases like `next Thursday night` or `Friday morning` and surface clearer warnings or alternate interpretations.


8. Add ISO and machine-friendly output helpers

Expose methods for intervals, ranges, timezone-aware ISO strings, and easy conversion to Python `datetime` or JSON payloads.

9. Add strict and fuzzy parsing modes

Let callers choose between permissive behavior and a strict mode that rejects ambiguous or conflicting phrases.

10. Ship a phrase corpus and fuzz tests

Build a larger regression suite from real examples so grammar changes are safer and easier to evolve.

11. Add date ranges

Handle phrases like `from next Friday to Sunday`, `between 3pm and 5pm tomorrow`, and `June 1st-3rd`.


12. I did it at 5. would fail by putting a time in the future. so parsing
context of past or future from surrounding text could be useful bump.
We should be able to use some words to guess. did, was etc vs going, will

13. consideration around BC dates 
- considered milliseconds backwards


14. Add a defuzzer / cleanup pipeline

Pass 1. Define the scope of defuzzing

Keep this layer about cleanup, not interpretation. It should remove wrappers,
quotes, repeated punctuation, and obvious filler without silently changing the
meaning of a phrase.

Pass 2. Add safe built-in cleanup rules

Start with low-risk transforms such as stripping surrounding quotes,
normalizing repeated punctuation, trimming brackets, and collapsing noisy
whitespace.

Pass 3. Handle common conversational wrappers

Support phrases embedded in soft framing like `about`, `maybe`, `roughly`,
`around`, `on`, and lightweight chat wrappers so extraction gets cleaner
candidate spans.

Pass 4. Separate cleanup from normalization

Keep defuzzing distinct from aliasing and semantic rewrites. Cleanup should
prepare the text, while alias rules and parser helpers should still own actual
date meaning.

Pass 5. Add parser-facing hooks

Let `Date(...)` and `extract_dates(...)` run through a defuzzer stage before
strict parsing so we get the benefit everywhere without duplicating logic.

Pass 6. Add caller-provided defuzzer rules

Allow users to pass their own cleanup rules or callbacks so applications can
strip domain-specific wrappers without forking `stringtime`.

Pass 7. Make the behavior configurable

Support flags like `defuzz=True/False` and maybe rule presets so callers can
choose between conservative cleanup and more aggressive cleanup.

Pass 8. Preserve metadata about cleanup

Expose what the defuzzer changed in parse metadata so users can tell whether a
phrase was parsed directly or after cleanup.

Pass 9. Add regression tests for noisy real-world inputs

Cover quoted phrases, punctuation-heavy text, chatty wording, and extraction
from longer messy sentences to make sure cleanup does not overreach.

Pass 10. Document the extension model

Show the built-in cleanup behavior, the boundary between defuzzing and parsing,
and how users can add their own custom defuzzer rules safely.


>>> matches = Date("the day before the twelth second of the 14th minute on the 2nd week of the first month 2321", extract=True)

>>> matches = Date("around 12 i reckon on wednesday", extract=True)
>>> print(matches)
[DateMatch(text='12', start=7, end=9, date=<Date: 2026-03-13 12:00:00>), DateMatch(text='on wednesday', start=19, end=31, date=<Date: 2026-03-18 05:50:22>)]


14. forever, infinity, forever and a day


16. astrological signs? chinese astrology

the second business day after Easter
the week commencing 14 September 2026
three days shy of a month from now
the first trading day of next quarter
between noon and 2pm on Friday
the 29th of February next leap year
close of business two Fridays from now
the Tuesday fortnight after next
sometime late next summer



Top ones I’d add next are the event families that are naturally anchor-like and compose well:

Recurring week-structure anchors
weekend
midweek



Church/clock anchors
matins
vespers
compline
Only if you want older/liturgical phrasing.

first light
last light
first light is partly there already.

Election / civic anchors
election day
inauguration day
budget day
Useful if you want modern public-language anchors.
School/work anchors
start of term
end of term
pay day
closing bell


