# Semantic Registry

The phrase registry started as a flat `phrase -> representative datetime`
corpus. That is still useful, but it loses too much meaning for phrases that
name periods or boundaries instead of exact instants.

Examples:

- `friday`
  - not a point in time
  - it names a day-period
- `morning`
  - not a point in time
  - it names a fuzzy part-of-day period
- `end of month`
  - not a normal datetime phrase
  - it names a boundary
- `xmas`
  - potentially ambiguous between a day and a season

## Current Model

Registry rows now include:

- `semantic_kind`
  - `instant`
  - `period`
  - `boundary`
  - `relative_offset`
- `representative_granularity`
  - `second`
  - `minute`
  - `hour`
  - `day`
  - `part_of_day`
  - `month`
  - `quarter`
  - `year`

This means a parsed timestamp in the registry should be read as a
representative value for that phrase, not always the full meaning of it.

For example:

- `friday`
  - `semantic_kind = period`
  - `representative_granularity = day`
- `tomorrow at 5pm`
  - `semantic_kind = instant`
  - `representative_granularity = minute`
- `end of month`
  - `semantic_kind = boundary`
  - `representative_granularity = month`

## Why This Matters

This gives reverse phrasing a better foundation:

- exact reverse lookup can still use representative timestamps
- nearest lookup can prefer phrases with the right semantic kind
- future rendering can distinguish:
  - exact instant phrases
  - containing periods
  - boundaries
  - ambiguous phrases

## Next Steps

Likely follow-on improvements:

1. Add `ambiguous` as a first-class semantic kind where needed.
2. Add optional `range_start` / `range_end` fields for period phrases.
3. Teach nearest reverse lookup to score by semantic kind as well as time.
4. Only later, consider a DB or CSV strategy if registry scale demands it.
