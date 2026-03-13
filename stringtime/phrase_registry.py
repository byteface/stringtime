from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from itertools import product


@dataclass(frozen=True)
class PhraseTemplate:
    name: str
    category: str
    pattern: str
    dimensions: dict[str, tuple[str, ...]]
    preferred: dict[str, str] = field(default_factory=dict)
    locale: str = "en"
    style: str = "natural"
    semantic_kind: str = "instant"
    representative_granularity: str = "second"
    tags: tuple[str, ...] = ()

    def expand(self) -> list[dict[str, object]]:
        keys = list(self.dimensions.keys())
        phrases = []
        for values in product(*(self.dimensions[key] for key in keys)):
            context = dict(zip(keys, values))
            phrase = " ".join(self.pattern.format(**context).split())
            is_canonical = all(
                context.get(key) == value for key, value in self.preferred.items()
            )
            phrases.append(
                {
                    "family": self.name,
                    "category": self.category,
                    "phrase": phrase,
                    "pattern": self.pattern,
                    "dimensions": context,
                    "locale": self.locale,
                    "style": self.style,
                    "semantic_kind": self.semantic_kind,
                    "representative_granularity": self.representative_granularity,
                    "tags": list(self.tags),
                    "is_canonical": is_canonical,
                }
            )
        return phrases


WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)

WEEKDAY_ALIASES = (
    ("monday", "mon"),
    ("tuesday", "tues"),
    ("wednesday", "wed"),
    ("thursday", "thurs"),
    ("friday", "fri"),
    ("saturday", "sat"),
    ("sunday", "sun"),
)

MONTHS = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)

MONTH_ALIASES = (
    ("january", "jan"),
    ("february", "feb"),
    ("march", "mar"),
    ("april", "apr"),
    ("may", "may"),
    ("june", "jun"),
    ("july", "jul"),
    ("august", "aug"),
    ("september", "sept"),
    ("october", "oct"),
    ("november", "nov"),
    ("december", "dec"),
)

ORDINALS = (
    ("1st", "first"),
    ("2nd", "second"),
    ("3rd", "third"),
    ("4th", "fourth"),
    ("5th", "fifth"),
    ("8th", "eighth"),
    ("12th", "twelfth"),
    ("14th", "fourteenth"),
    ("16th", "sixteenth"),
    ("18th", "eighteenth"),
    ("20th", "twentieth"),
    ("21st", "twenty first"),
    ("29th", "twenty ninth"),
    ("31st", "thirty first"),
)

PARTS_OF_DAY = (
    "morning",
    "afternoon",
    "evening",
    "night",
    "lunchtime",
    "mid-morning",
    "early in the morning",
)

TIME_FORMS = (
    "1",
    "2am",
    "3pm",
    "5",
    "5am",
    "5 pm",
    "5:30",
    "7:15",
    "7:15pm",
    "9am",
)

SPECIAL_PHRASES = (
    ("now", "natural", "instant", "second", ("relative",)),
    ("today", "natural", "period", "day", ("relative",)),
    ("tomorrow", "natural", "period", "day", ("relative",)),
    ("yesterday", "natural", "period", "day", ("relative",)),
    ("after tomorrow", "natural", "period", "day", ("relative",)),
    ("before yesterday", "natural", "period", "day", ("relative",)),
    ("midday", "natural", "instant", "minute", ("named_time",)),
    ("noon", "natural", "instant", "minute", ("named_time",)),
    ("midnight", "natural", "boundary", "minute", ("named_time",)),
    ("today at noon", "natural", "instant", "minute", ("named_time", "composed")),
    ("today at midnight", "natural", "boundary", "minute", ("named_time", "composed")),
    ("tomorrow noon", "natural", "instant", "minute", ("named_time", "composed")),
    ("tomorrow midnight", "natural", "boundary", "minute", ("named_time", "composed")),
    ("midnight tomorrow", "natural", "boundary", "minute", ("named_time", "composed")),
    ("noon on friday", "natural", "instant", "minute", ("named_time", "composed")),
    ("next tuesday evening", "natural", "period", "part_of_day", ("part_of_day", "composed")),
    ("the wednesday after next", "natural", "period", "day", ("weekday", "composed")),
    ("chinese dentist", "colloquial", "instant", "minute", ("idiom",)),
    ("cowboy time", "colloquial", "instant", "minute", ("idiom",)),
    ("when the clock strikes 6", "colloquial", "boundary", "hour", ("idiom",)),
    ("quarter past 5", "natural", "instant", "minute", ("clock_phrase",)),
    ("half past 5", "natural", "instant", "minute", ("clock_phrase",)),
    ("quarter to 6", "natural", "instant", "minute", ("clock_phrase",)),
    ("3 more sleeps", "colloquial", "relative_offset", "day", ("relative", "idiom")),
    ("10 sleeps til xmas", "colloquial", "relative_offset", "day", ("relative", "holiday")),
    ("christmas", "natural", "period", "day", ("holiday",)),
    ("christmas eve", "natural", "period", "day", ("holiday",)),
    ("new year's day", "natural", "period", "day", ("holiday",)),
    ("easter", "natural", "period", "day", ("holiday",)),
    ("thanksgiving", "natural", "period", "day", ("holiday",)),
    ("black friday", "natural", "period", "day", ("holiday",)),
    ("halloween", "natural", "period", "day", ("holiday",)),
    ("labor day", "natural", "period", "day", ("holiday",)),
)

BOUNDARY_PHRASES = (
    ("end of month", True, "natural", "boundary", "month", ("boundary",)),
    ("end of the month", False, "natural", "boundary", "month", ("boundary", "article_variant")),
    ("close of year", True, "natural", "boundary", "year", ("boundary",)),
    ("start of next quarter", True, "natural", "boundary", "quarter", ("boundary", "quarter")),
    (
        "start of the next quarter",
        False,
        "natural",
        "boundary",
        "quarter",
        ("boundary", "quarter", "article_variant"),
    ),
    ("first day of next quarter", False, "formal", "boundary", "day", ("boundary", "quarter")),
    ("last day of this quarter", True, "formal", "boundary", "day", ("boundary", "quarter")),
)

BUSINESS_AND_LOCALE = (
    ("3 business days from now", True, "en", "natural", "relative_offset", "day", ("business_day",)),
    ("next working day", True, "en", "natural", "period", "day", ("business_day",)),
    ("end of business tomorrow", True, "en", "natural", "boundary", "hour", ("business_day",)),
    ("end of play", False, "en-GB", "colloquial", "boundary", "hour", ("business_day", "locale_variant")),
    ("eop", False, "en", "compact", "boundary", "hour", ("business_day", "shorthand")),
    ("first thing", True, "en", "colloquial", "period", "part_of_day", ("part_of_day",)),
    (
        "first thing in the morning",
        False,
        "en",
        "natural",
        "period",
        "part_of_day",
        ("part_of_day", "expanded_variant"),
    ),
    ("half five", True, "en-GB", "colloquial", "instant", "minute", ("clock_phrase", "locale_variant")),
    ("in a fortnight", True, "en-GB", "natural", "relative_offset", "day", ("duration", "locale_variant")),
    ("a fortnight ago", True, "en-GB", "natural", "relative_offset", "day", ("duration", "locale_variant")),
    ("bank holiday", True, "en-GB", "natural", "period", "day", ("holiday", "locale_variant")),
    ("next bank holiday", True, "en-GB", "natural", "period", "day", ("holiday", "locale_variant")),
)

DEFAULT_REFERENCE = "2020-12-25 17:05:55"
STYLE_PRIORITY = {
    "natural": 0,
    "formal": 1,
    "compact": 2,
    "colloquial": 3,
    "variant": 4,
}
ABBREVIATION_TOKENS = {
    "mon",
    "tues",
    "wed",
    "thurs",
    "fri",
    "sat",
    "sun",
    "jan",
    "feb",
    "mar",
    "apr",
    "jun",
    "jul",
    "aug",
    "sept",
    "oct",
    "nov",
    "dec",
    "eop",
}


def build_phrase_templates() -> tuple[PhraseTemplate, ...]:
    weekday_variants = tuple(
        canonical for canonical, _ in WEEKDAY_ALIASES
    ) + tuple(alias for _, alias in WEEKDAY_ALIASES)
    month_variants = tuple(
        canonical for canonical, _ in MONTH_ALIASES
    ) + tuple(alias for _, alias in MONTH_ALIASES)
    numeric_ordinals = tuple(numeric for numeric, _ in ORDINALS)
    word_ordinals = tuple(word for _, word in ORDINALS)

    return (
        PhraseTemplate(
            name="weekday_only",
            category="weekday",
            pattern="{weekday}",
            dimensions={"weekday": weekday_variants},
            preferred={"weekday": "monday"},
            semantic_kind="period",
            representative_granularity="day",
            tags=("absolute",),
        ),
        PhraseTemplate(
            name="weekday_prefixed",
            category="weekday",
            pattern="{prefix} {weekday}",
            dimensions={"prefix": ("next", "last", "on"), "weekday": weekday_variants},
            preferred={"prefix": "next", "weekday": "monday"},
            semantic_kind="period",
            representative_granularity="day",
            tags=("relative",),
        ),
        PhraseTemplate(
            name="weekday_at_time",
            category="composed_time",
            pattern="{weekday} at {time}",
            dimensions={"weekday": WEEKDAYS, "time": TIME_FORMS},
            preferred={"weekday": "monday", "time": "5 pm"},
            semantic_kind="instant",
            representative_granularity="minute",
            tags=("absolute", "time"),
        ),
        PhraseTemplate(
            name="at_time_on_weekday",
            category="composed_time",
            pattern="at {time} on {weekday}",
            dimensions={"time": ("5 pm", "5:52 pm"), "weekday": WEEKDAYS},
            preferred={"time": "5 pm", "weekday": "monday"},
            style="formal",
            semantic_kind="instant",
            representative_granularity="minute",
            tags=("absolute", "time"),
        ),
        PhraseTemplate(
            name="weekday_part_of_day",
            category="part_of_day",
            pattern="{weekday} {part}",
            dimensions={"weekday": WEEKDAYS + ("next tuesday",), "part": PARTS_OF_DAY},
            preferred={"weekday": "monday", "part": "morning"},
            semantic_kind="period",
            representative_granularity="part_of_day",
            tags=("absolute", "time"),
        ),
        PhraseTemplate(
            name="part_of_day_relative",
            category="part_of_day",
            pattern="{date} {part}",
            dimensions={
                "date": ("today", "tomorrow", "yesterday", "this"),
                "part": ("morning", "evening", "night", "lunchtime"),
            },
            preferred={"date": "tomorrow", "part": "morning"},
            semantic_kind="period",
            representative_granularity="part_of_day",
            tags=("relative", "time"),
        ),
        PhraseTemplate(
            name="part_of_day_reversed",
            category="part_of_day",
            pattern="{part} {date}",
            dimensions={
                "part": ("morning", "evening", "night", "lunchtime"),
                "date": ("today", "tomorrow", "yesterday") + WEEKDAYS,
            },
            preferred={"part": "morning", "date": "tomorrow"},
            style="variant",
            semantic_kind="period",
            representative_granularity="part_of_day",
            tags=("relative", "time", "word_order_variant"),
        ),
        PhraseTemplate(
            name="ordinal_month_numeric",
            category="ordinal_date",
            pattern="{article}{ordinal} of {month}",
            dimensions={
                "article": ("", "the "),
                "ordinal": numeric_ordinals,
                "month": month_variants,
            },
            preferred={"article": "", "ordinal": "1st", "month": "january"},
            semantic_kind="period",
            representative_granularity="day",
            tags=("absolute",),
        ),
        PhraseTemplate(
            name="ordinal_month_words",
            category="ordinal_date",
            pattern="{article}{ordinal} of {month}",
            dimensions={
                "article": ("", "the "),
                "ordinal": word_ordinals,
                "month": MONTHS,
            },
            preferred={"article": "the ", "ordinal": "first", "month": "january"},
            semantic_kind="period",
            representative_granularity="day",
            tags=("absolute", "word_variant"),
        ),
        PhraseTemplate(
            name="month_day",
            category="ordinal_date",
            pattern="{month} {article}{ordinal}",
            dimensions={
                "month": month_variants,
                "article": ("", "the "),
                "ordinal": numeric_ordinals,
            },
            preferred={"month": "january", "article": "", "ordinal": "1st"},
            style="formal",
            semantic_kind="period",
            representative_granularity="day",
            tags=("absolute",),
        ),
        PhraseTemplate(
            name="month_relative",
            category="month_relative",
            pattern="{article}{ordinal} of {period}",
            dimensions={
                "article": ("", "the "),
                "ordinal": ("1st", "12th", "16th", "21st"),
                "period": ("last month", "next month"),
            },
            preferred={"article": "the ", "ordinal": "1st", "period": "next month"},
            semantic_kind="period",
            representative_granularity="day",
            tags=("relative",),
        ),
        PhraseTemplate(
            name="ordinal_weekday_period",
            category="ordinal_weekday",
            pattern="{article}{occurrence} {weekday} in {period}",
            dimensions={
                "article": ("", "the "),
                "occurrence": ("first", "2nd", "third", "last", "penultimate"),
                "weekday": ("monday", "tuesday", "wednesday", "thursday", "friday"),
                "period": ("may", "june", "next month", "the month", "2026"),
            },
            preferred={
                "article": "the ",
                "occurrence": "first",
                "weekday": "monday",
                "period": "may",
            },
            semantic_kind="period",
            representative_granularity="day",
            tags=("absolute",),
        ),
        PhraseTemplate(
            name="quarter_named",
            category="quarter",
            pattern="{phrase}",
            dimensions={
                "phrase": (
                    "start of q2",
                    "end of q4",
                    "mid q1 2027",
                    "first day of next quarter",
                    "last day of this quarter",
                )
            },
            preferred={"phrase": "start of q2"},
            semantic_kind="boundary",
            representative_granularity="quarter",
            tags=("absolute", "boundary"),
        ),
        PhraseTemplate(
            name="durations",
            category="duration",
            pattern="{phrase}",
            dimensions={
                "phrase": (
                    "an hour from now",
                    "10 minutes ago",
                    "10 hours and 30 minutes from now",
                    "in a minute and a half",
                    "an hour and a half ago",
                    "two and a half hours",
                    "1.5 days",
                    "a quarter of an hour",
                    "three quarters of an hour",
                    "2.5 weeks",
                )
            },
            preferred={"phrase": "an hour from now"},
            semantic_kind="relative_offset",
            representative_granularity="second",
            tags=("relative",),
        ),
        PhraseTemplate(
            name="timezone",
            category="timezone",
            pattern="{phrase}",
            dimensions={
                "phrase": (
                    "tomorrow at 5pm utc",
                    "next friday 9am pst",
                    "tomorrow at 5pm utc+2",
                )
            },
            preferred={"phrase": "tomorrow at 5pm utc"},
            style="formal",
            semantic_kind="instant",
            representative_granularity="minute",
            tags=("relative", "timezone"),
        ),
    )


def iter_phrase_families():
    for template in build_phrase_templates():
        yield template.expand()

    yield [
        {
            "family": "boundaries",
            "category": "boundary",
            "phrase": phrase,
            "pattern": "{phrase}",
            "dimensions": {"phrase": phrase},
            "locale": "en",
            "style": style,
            "semantic_kind": semantic_kind,
            "representative_granularity": granularity,
            "tags": list(tags),
            "is_canonical": is_canonical,
        }
        for phrase, is_canonical, style, semantic_kind, granularity, tags in BOUNDARY_PHRASES
    ]

    yield [
        {
            "family": "business_locale",
            "category": "business_locale",
            "phrase": phrase,
            "pattern": "{phrase}",
            "dimensions": {"phrase": phrase},
            "locale": locale,
            "style": style,
            "semantic_kind": semantic_kind,
            "representative_granularity": granularity,
            "tags": list(tags),
            "is_canonical": is_canonical,
        }
        for phrase, is_canonical, locale, style, semantic_kind, granularity, tags in BUSINESS_AND_LOCALE
    ]

    yield [
        {
            "family": "special",
            "category": "special",
            "phrase": phrase,
            "pattern": "{phrase}",
            "dimensions": {"phrase": phrase},
            "locale": "en",
            "style": style,
            "semantic_kind": semantic_kind,
            "representative_granularity": granularity,
            "tags": list(tags),
            "is_canonical": True,
        }
        for phrase, style, semantic_kind, granularity, tags in SPECIAL_PHRASES
    ]


def generate_phrase_records() -> list[dict[str, object]]:
    records = []
    seen = set()

    for family_entries in iter_phrase_families():
        for entry in family_entries:
            normalized = " ".join(str(entry["phrase"]).strip().split())
            if normalized in seen:
                continue
            seen.add(normalized)
            record = dict(entry)
            record["phrase"] = normalized
            records.append(record)

    return records


def variant_penalty(record):
    phrase_tokens = set(record["phrase"].split())
    penalty = 0

    if phrase_tokens & ABBREVIATION_TOKENS:
        penalty += 2
    if "article_variant" in record["tags"]:
        penalty += 1
    if "word_order_variant" in record["tags"]:
        penalty += 1
    if "shorthand" in record["tags"]:
        penalty += 2
    if record["style"] == "variant":
        penalty += 1

    return penalty


def canonical_sort_key(record):
    return (
        0 if record["is_canonical"] else 1,
        STYLE_PRIORITY.get(record["style"], 99),
        variant_penalty(record),
        0 if record["locale"] == "en" else 1,
        len(record["phrase"]),
        record["phrase"],
    )


def build_reverse_records(successful_records):
    from collections import defaultdict

    grouped = defaultdict(list)
    for record in successful_records:
        grouped[record["parsed"]].append(record)

    reverse_map = {}
    reverse_records = []

    for parsed_value in sorted(grouped):
        variants = sorted(grouped[parsed_value], key=canonical_sort_key)
        canonical = variants[0]

        reverse_map[parsed_value] = {
            "canonical_phrase": canonical["phrase"],
            "phrases": [variant["phrase"] for variant in variants],
        }
        reverse_records.append(
            {
                "parsed": parsed_value,
                "canonical_phrase": canonical["phrase"],
                "canonical_locale": canonical["locale"],
                "canonical_style": canonical["style"],
                "semantic_kinds": sorted(
                    {variant["semantic_kind"] for variant in variants}
                ),
                "representative_granularities": sorted(
                    {
                        variant["representative_granularity"]
                        for variant in variants
                    }
                ),
                "phrase_count": len(variants),
                "phrases": [variant["phrase"] for variant in variants],
                "families": sorted({variant["family"] for variant in variants}),
                "categories": sorted({variant["category"] for variant in variants}),
                "locales": sorted({variant["locale"] for variant in variants}),
                "styles": sorted({variant["style"] for variant in variants}),
            }
        )

    return reverse_map, reverse_records


@lru_cache(maxsize=16)
def build_registry(relative_to: str = DEFAULT_REFERENCE):
    from stringtime import Date

    records = []
    failures = []
    successful_records = []

    for entry in generate_phrase_records():
        phrase = entry["phrase"]
        parsed = Date(phrase, relative_to=relative_to)
        metadata = parsed.parse_metadata
        success = not metadata.used_dateutil

        record = {
            **entry,
            "relative_to": relative_to,
            "parsed": str(parsed),
            "exact": metadata.exact,
            "fuzzy": metadata.fuzzy,
            "used_dateutil": metadata.used_dateutil,
            "normalized_text": metadata.normalized_text,
            "matched_text": metadata.matched_text,
        }
        records.append(record)

        if success:
            successful_records.append(record)
        else:
            failures.append(record)

    reverse_map, reverse_records = build_reverse_records(successful_records)

    summary = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "relative_to": relative_to,
        "phrase_count": len(records),
        "successful_phrase_count": len(successful_records),
        "failed_phrase_count": len(failures),
        "distinct_datetime_count": len(reverse_records),
        "families": sorted({record["family"] for record in records}),
        "categories": sorted({record["category"] for record in records}),
        "locales": sorted({record["locale"] for record in records}),
        "semantic_kinds": sorted({record["semantic_kind"] for record in records}),
        "representative_granularities": sorted(
            {record["representative_granularity"] for record in records}
        ),
        "styles": sorted({record["style"] for record in records}),
    }

    return {
        "summary": summary,
        "records": records,
        "reverse_map": reverse_map,
        "reverse_records": reverse_records,
        "failures": failures,
    }
