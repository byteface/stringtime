# Wishlist

Top 10 ideas for where `stringtime` could go next.

1. Support fractional durations

Allow phrases like `an hour and a half`, `1.5 days`, and `two and a half weeks`.

2. Parse ordinal words

Handle `the first of September`, `twenty first`, `third of May`, and similar natural date phrases.

3. Add month-relative dates

Support phrases like `the 12th of last month`, `next month on the first`, and `last month on the 16th at 2am`.

4. Improve composed date-time phrases

Handle more combinations such as `next Monday at 7:15pm`, `7:15 next Monday`, and `Friday at 5:30`.

5. Add named periods of day

Support `this evening`, `tomorrow morning`, `Friday afternoon`, and conflict detection for bad combinations.

6. Add holiday support

Recognize phrases like `Christmas`, `New Year's Day`, `Easter`, and relative forms like `Easter next year`.

7. Introduce timezone parsing

Allow phrases such as `tomorrow at 5pm UTC`, `next Friday 9am PST`, and optional timezone-aware output.

8. Return parse metadata

Expose what matched, whether the parse was exact or fuzzy, and whether parsing fell back to `dateutil`.

9. Add strict and fuzzy parsing modes

Let callers choose between permissive behavior and a strict mode that rejects ambiguous or conflicting phrases.

10. Ship a phrase corpus and fuzz tests

Build a larger regression suite from real examples so grammar changes are safer and easier to evolve.
