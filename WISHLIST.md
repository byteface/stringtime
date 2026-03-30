# Wishlist

Things that still feel meaningfully unfinished in `stringtime`.

1. Ambiguity controls

Add caller settings for ambiguous phrases such as `tomorrow at 3`, for example a meridiem preference like `am` vs `pm` when no stronger cue exists.

2. Date ranges

Handle ranges like:

- `from next Friday to Sunday`
- `between 3pm and 5pm tomorrow`
- `June 1st-3rd`
- recurring ranges such as `each november 1st since 2020 until today`

3. Parsing context from surrounding tense

Phrases like `I did it at 5` should not lean future by default. Use surrounding tense cues like `did`, `was`, `going`, `will` to bias interpretation.

4. BC dates

Decide whether `BC` / negative-year support is worth adding and what the API and arithmetic model should be.

5. Defuzzing and extract ranking

Extraction still needs smarter ranking and phrase preference in ambiguous text, for example:

- `around 12 i reckon on wednesday`

6. Astrology / novelty calendars

Still open if wanted:

- astrological signs
- chinese astrology

7. Regional holidays and regional event logic

Support region-specific holidays and maybe other regional logic such as UK-specific observances. This likely needs a region setting in the API.

8. Phrase generation from dates

There is still room for a proper “date to phrase” system, but it needs a rethink rather than incremental patching.

9. Demo fallback / clarification UX

The demo could surface clarification behavior for underspecified phrases such as `friday in august` instead of silently choosing a representative interpretation.

10. Localisation

Decide the real direction:

- language packs / canonical internal translation before parse
- or leave translation to callers before they pass phrases in
