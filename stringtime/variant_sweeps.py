import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from stringtime import Date

DEFAULT_REFERENCE = "2020-12-25 17:05:55"


@dataclass(frozen=True)
class VariantSeed:
    phrase: str
    expected: str
    family: str


@dataclass(frozen=True)
class VariantCase:
    phrase: str
    expected: str
    family: str
    source_phrase: str


@dataclass(frozen=True)
class ExtractionCase:
    text: str
    expected_text: str
    expected: str
    family: str
    source_phrase: str


SEED_CASES = (
    VariantSeed("tomorrow night", "2020-12-26 21:00:00", "parts_of_day"),
    VariantSeed("next Tuesday evening", "2020-12-29 19:00:00", "parts_of_day"),
    VariantSeed("end of month", "2020-12-31 17:05:55", "boundary"),
    VariantSeed("the start of june", "2021-06-01 17:05:55", "boundary"),
    VariantSeed("today at noon", "2020-12-25 12:00:00", "named_time"),
    VariantSeed("midnight on Friday", "2020-12-25 00:00:00", "named_time"),
    VariantSeed("3 days from next Wednesday", "2021-01-02 17:05:55", "anchor_offset"),
    VariantSeed("15 minutes before midnight", "2020-12-24 23:45:00", "anchor_offset"),
    VariantSeed("the first Monday in May", "2020-05-04 17:05:55", "ordinal_weekday"),
    VariantSeed("the last Friday in June", "2020-06-26 17:05:55", "ordinal_weekday"),
    VariantSeed("the 12th of last month", "2020-11-12 17:05:55", "ordinal_date"),
    VariantSeed("next month on the first", "2021-01-01 17:05:55", "ordinal_date"),
    VariantSeed("next valentines", "2021-02-14 17:05:55", "holiday"),
    VariantSeed("pancake day", "2020-02-25 17:05:55", "holiday"),
    VariantSeed("New Year's Day", "2020-01-01 17:05:55", "holiday"),
    VariantSeed("Halloween", "2020-10-31 17:05:55", "holiday"),
    VariantSeed("shrove tuesday", "2020-02-25 17:05:55", "holiday"),
    VariantSeed("2moro @ noonish", "2020-12-26 12:00:00", "alias"),
    VariantSeed("T-minus 5 minutes", "2020-12-25 17:00:55", "alias"),
    VariantSeed("in a fortnight", "2021-01-08 17:05:55", "duration"),
    VariantSeed("an hour and a half ago", "2020-12-25 15:35:55", "duration"),
    VariantSeed("half five tomorrow night", "2020-12-26 05:30:00", "clock_phrase"),
    VariantSeed("when the clock strikes 6", "2020-12-25 06:00:00", "clock_phrase"),
    VariantSeed("quarter past 5", "2020-12-25 05:15:00", "clock_phrase"),
    VariantSeed("half past 5", "2020-12-25 05:30:00", "clock_phrase"),
    VariantSeed("quarter to 6", "2020-12-25 05:45:00", "clock_phrase"),
    VariantSeed("4 and twenty past 7", "2020-12-25 07:24:00", "clock_phrase"),
    VariantSeed("Friday afternoon", "2020-12-25 15:00:00", "parts_of_day"),
    VariantSeed("the second to last day of the month", "2020-12-30 17:05:55", "boundary"),
    VariantSeed("the other night", "2020-12-24 21:00:00", "parts_of_day"),
    VariantSeed("right now", "2020-12-25 17:05:55", "alias"),
    VariantSeed("a week 2moro", "2021-01-02 17:05:55", "anchor_offset"),
    VariantSeed("bank holiday", "2020-12-25 17:05:55", "holiday"),
    VariantSeed("Christmas Eve", "2020-12-24 17:05:55", "holiday"),
    VariantSeed("the last Sunday of the year", "2020-12-27 17:05:55", "ordinal_weekday"),
    VariantSeed("the hundredth day of the year", "2020-04-09 17:05:55", "day_of_year"),
    VariantSeed("the hundreth day of the year", "2020-04-09 17:05:55", "day_of_year"),
    VariantSeed("end of business tomorrow", "2020-12-26 17:00:00", "business"),
    VariantSeed("EOP", "2020-12-25 17:00:00", "business"),
    VariantSeed("close of year", "2020-12-31 17:05:55", "business"),
    VariantSeed("start of next quarter", "2021-01-01 17:05:55", "business"),
    VariantSeed("at dinner time", "2020-12-25 18:00:00", "mealtime"),
    VariantSeed("tea time", "2020-12-26 17:00:00", "mealtime"),
    VariantSeed("Sunday @ about lunch time", "2020-12-27 12:30:00", "mealtime"),
    VariantSeed("the other day", "2020-12-23 17:05:55", "relative_day"),
    VariantSeed("the day before yesterday", "2020-12-23 17:05:55", "relative_day"),
    VariantSeed("the day after tomorrow", "2020-12-27 17:05:55", "relative_day"),
    VariantSeed("in the morrow", "2020-12-26 17:05:55", "relative_day"),
    VariantSeed("Tuesday gone", "2020-12-22 17:05:55", "relative_weekday"),
    VariantSeed("Tuesday past", "2020-12-22 17:05:55", "relative_weekday"),
    VariantSeed("the 2nd week of january", "2021-01-08 17:05:55", "week_period"),
    VariantSeed("the day before the 2nd week of january", "2021-01-07 17:05:55", "week_period"),
    VariantSeed("3 weeks ago at 2am", "2020-12-04 02:00:00", "relative_time"),
    VariantSeed("tomorrow at 5pm UTC", "2020-12-26 17:00:00", "timezone"),
    VariantSeed("next Friday 9am PST", "2021-01-01 09:00:00", "timezone"),
    VariantSeed("tomorrow at 5pm UTC+2", "2020-12-26 17:00:00", "timezone"),
    VariantSeed("tomorrow at 5 p.m. UTC", "2020-12-26 17:00:00", "timezone"),
    VariantSeed("start of Q2", "2020-04-01 17:05:55", "quarter"),
    VariantSeed("mid Q1 2027", "2027-02-15 17:05:55", "quarter"),
    VariantSeed("the next leap year", "2024-01-01 17:05:55", "leap_year"),
    VariantSeed("a day before the next leap year", "2023-12-31 17:05:55", "leap_year"),
    VariantSeed("the 7th of the 6th eighty one", "1981-06-07 17:05:55", "ordinal_month_year"),
    VariantSeed("the first of the 3rd 22 @ 3pm", "2022-03-01 15:00:00", "ordinal_month_year"),
    VariantSeed("7th of the 6th 81", "1981-06-07 17:05:55", "ordinal_month_year"),
    VariantSeed("the fourteenth week after xmas", "2021-04-02 17:05:55", "anchor_offset"),
    VariantSeed("two Fridays from now", "2021-01-08 17:05:55", "counted_weekday"),
    VariantSeed("the twelfth month", "2021-12-01 17:05:55", "month_anchor"),
    VariantSeed("the day before the twelfth month", "2021-11-30 17:05:55", "month_anchor"),
    VariantSeed("the night before last", "2020-12-23 21:00:00", "parts_of_day"),
    VariantSeed("the night b4 yesterday", "2020-12-23 21:00:00", "parts_of_day"),
)


def _dedupe_keep_order(items):
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _common_variants(phrase):
    variants = [phrase]

    if "@" in phrase:
        variants.append(phrase.replace("@", "at"))
    if " at " in f" {phrase} ":
        variants.append(phrase.replace(" at ", " @ "))

    replacements = (
        ("tomorrow", "2moro"),
        ("tomorrow", "tmrw"),
        ("tomorrow", "2moz"),
        ("2moro", "tomorrow"),
        ("night", "nite"),
        ("christmas", "xmas"),
        ("end of business", "eob"),
        ("close of year", "eoy"),
        ("before", "b4"),
        ("b4", "before"),
        ("T-minus", "T minus"),
        ("T minus", "T-minus"),
    )
    for source, target in replacements:
        if re.search(rf"\b{re.escape(source)}\b", phrase, flags=re.IGNORECASE):
            variants.append(
                re.sub(rf"\b{re.escape(source)}\b", target, phrase, flags=re.IGNORECASE)
            )

    if phrase and phrase[0].isalpha():
        variants.append(phrase.lower())
        variants.append(phrase.title())
        variants.append(phrase.upper())

    return _dedupe_keep_order([variant.strip() for variant in variants if variant.strip()])


def _family_variants(seed):
    phrase = seed.phrase
    variants = list(_common_variants(phrase))

    if seed.family == "parts_of_day":
        variants.append(phrase.replace("tomorrow", "2moro"))
        variants.append(phrase.replace("tomorrow", "tmrw"))
        if phrase.lower().startswith("next "):
            variants.append(f"on {phrase}")
        if "afternoon" in phrase:
            variants.append(phrase.replace("afternoon", "arvo"))
        if phrase == "the other night":
            variants.extend(("other night", "the other nite"))
        if phrase == "the night before last":
            variants.extend(("night before last", "the night b4 last"))
        if phrase == "the night b4 yesterday":
            variants.extend(("night b4 yesterday", "the night before yesterday"))

    if seed.family == "boundary":
        if phrase == "end of month":
            variants.extend(("end of the month", "the end of month", "month end"))
        if phrase == "the start of june":
            variants.extend(
                ("start of june", "the beginning of june", "the start of the month of june")
            )
        if phrase == "the second to last day of the month":
            variants.extend(
                (
                    "second to last day of the month",
                    "the second-last day of the month",
                    "the penultimate day of the month",
                )
            )

    if seed.family == "ordinal_date":
        if "12th" in phrase:
            variants.extend(
                (
                    phrase.replace("the 12th", "12th"),
                    phrase.replace("12th", "twelfth"),
                    phrase.replace("the 12th of", "12th of"),
                )
            )
        if phrase == "next month on the first":
            variants.extend(
                (
                    "the first of next month",
                    "the 1st of next month",
                    "next month on 1st",
                    "1st of next month",
                )
            )

    if seed.family == "holiday":
        if "valentines" in phrase:
            variants.extend(
                (
                    phrase.replace("valentines", "valentine's day"),
                    phrase.replace("valentines", "valentines day"),
                    phrase.replace("valentines", "st valentine's day"),
                    phrase.replace("valentines", "saint valentine's day"),
                )
            )
        if phrase == "pancake day":
            variants.extend(("shrove tuesday", "shrove Tuesday"))
        if phrase == "shrove tuesday":
            variants.extend(("Shrove Tuesday", "pancake day"))
        if phrase == "Christmas Eve":
            variants.extend(("xmas eve", "christmas eve", "Xmas Eve", "the night before christmas"))
        if phrase == "New Year's Day":
            variants.extend(
                ("new years day", "new year's day", "New Years Day", "new year's")
            )
        if phrase == "Halloween":
            variants.extend(("hallowe'en", "halloween", "all hallows eve"))
        if phrase == "bank holiday":
            variants.extend(("the bank holiday", "bank holiday monday"))

    if seed.family == "duration":
        if "fortnight" in phrase:
            variants.extend(
                (
                    phrase.replace("fortnight", "2 weeks"),
                    phrase.replace("in a fortnight", "a fortnight from now"),
                )
            )
        if phrase == "an hour and a half ago":
            variants.extend(("1.5 hours ago", "one hour and a half ago"))

    if seed.family == "clock_phrase":
        if phrase == "when the clock strikes 6":
            variants.extend(
                (
                    "the clock strikes 6",
                    "when the clock strikes six",
                    "the clock strikes six",
                )
            )
        if phrase == "half five tomorrow night":
            variants.extend(("5:30 tomorrow night", "half 5 tomorrow night"))
        if phrase == "quarter past 5":
            variants.extend(("quarter past five", "a quarter past 5", "quarter past 05"))
        if phrase == "half past 5":
            variants.extend(("half past five", "half past 05"))
        if phrase == "quarter to 6":
            variants.extend(("quarter to six", "a quarter to 6", "quarter to 06"))
        if phrase == "4 and twenty past 7":
            variants.extend(
                (
                    "four and twenty past 7",
                    "4 and 20 past 7",
                    "four and 20 past 7",
                    "4 and twenty past seven",
                )
            )

    if seed.family == "named_time":
        if phrase == "today at noon":
            variants.extend(("today noon", "noon today", "midday today"))
        if phrase == "midnight on Friday":
            variants.extend(("Friday at midnight", "midnight Friday"))

    if seed.family == "anchor_offset":
        if phrase == "3 days from next Wednesday":
            variants.extend(
                (
                    "in 3 days from next Wednesday",
                    "3 days after next Wednesday",
                    "3 days from next wednesday",
                )
            )
        if phrase == "15 minutes before midnight":
            variants.extend(
                (
                    "15 mins before midnight",
                    "15 minutes b4 midnight",
                    "15 minutes before 12am",
                )
            )
        if phrase == "a week 2moro":
            variants.extend(("a week tomorrow", "one week tomorrow"))
        if phrase == "the fourteenth week after xmas":
            variants.extend(
                (
                    "fourteenth week after xmas",
                    "the 14th week after xmas",
                    "the fourteenth week after christmas",
                )
            )

    if seed.family == "relative_time":
        if phrase == "3 weeks ago at 2am":
            variants.extend(("3 weeks ago at 2 am", "3 weeks ago at 2 in the morning"))

    if seed.family == "ordinal_weekday":
        if phrase == "the first Monday in May":
            variants.extend(
                (
                    "first Monday in May",
                    "the first Monday of May",
                    "first Monday of May",
                )
            )
        if phrase == "the last Friday in June":
            variants.extend(
                (
                    "last Friday in June",
                    "the last Friday of June",
                    "last Friday of June",
                )
            )
        if phrase == "the last Sunday of the year":
            variants.extend(("last Sunday of the year", "the last Sunday in the year"))

    if seed.family == "alias":
        if phrase == "2moro @ noonish":
            variants.extend(
                (
                    "tomorrow @ noonish",
                    "2moz at noonish",
                    "tmrw at noonish",
                    "2moro at midday",
                )
            )
        if phrase == "T-minus 5 minutes":
            variants.extend(("t minus 5 minutes", "t-minus 5 minutes"))

    if phrase == "right now":
        variants.extend(("now", "here and now", "immediately", "at once"))

    if seed.family == "business":
        if phrase == "end of business tomorrow":
            variants.extend(
                (
                    "eob tomorrow",
                    "cob tomorrow",
                    "close of business tomorrow",
                    "end of business on the morrow",
                )
            )
        if phrase == "EOP":
            variants.extend(("end of play", "close of play", "eop today"))
        if phrase == "close of year":
            variants.extend(("end of year", "close of the year", "the close of year"))
        if phrase == "start of next quarter":
            variants.extend(
                (
                    "start of the next quarter",
                    "first day of next quarter",
                    "the start of next quarter",
                )
            )

    if seed.family == "relative_day":
        if phrase == "the other day":
            variants.extend(("other day",))
        if phrase == "the day before yesterday":
            variants.extend(("day before yesterday", "before yesterday", "the day b4 yesterday"))
        if phrase == "the day after tomorrow":
            variants.extend(("day after tomorrow", "after tomorrow", "the day after 2moro"))
        if phrase == "in the morrow":
            variants.extend(("on the morrow", "the morrow"))

    if seed.family == "week_period":
        if phrase == "the 2nd week of january":
            variants.extend(("2nd week of january", "the second week of january"))
        if phrase == "the day before the 2nd week of january":
            variants.extend(
                (
                    "day before the 2nd week of january",
                    "the day before the second week of january",
                )
            )

    if seed.family == "day_of_year":
        if phrase == "the hundredth day of the year":
            variants.extend(("hundredth day of the year", "the 100th day of the year"))
        if phrase == "the hundreth day of the year":
            variants.extend(("hundreth day of the year", "the hundredth day of the year"))

    if seed.family == "mealtime":
        if phrase == "at dinner time":
            variants.extend(("dinner time", "at dinnertime", "dinnertime"))
        if phrase == "tea time":
            variants.extend(("teatime", "at tea time", "at teatime"))
        if phrase == "Sunday @ about lunch time":
            variants.extend(
                (
                    "Sunday at lunch time",
                    "Sunday @ lunchtime",
                    "Sunday at lunchtime",
                    "Sunday @ around lunch time",
                )
            )

    if seed.family == "timezone":
        if phrase == "tomorrow at 5pm UTC":
            variants.extend(
                (
                    "tomorrow at 5 pm UTC",
                    "tomorrow 5pm UTC",
                    "tomorrow at 5pm utc",
                    "tomorrow at 17:00 UTC",
                )
            )
        if phrase == "next Friday 9am PST":
            variants.extend(
                (
                    "next Friday at 9am PST",
                    "next Friday 9 am PST",
                    "next Friday 9am pst",
                    "next Friday at 9 a.m. PST",
                )
            )
        if phrase == "tomorrow at 5pm UTC+2":
            variants.extend(
                (
                    "tomorrow at 5 pm UTC+2",
                    "tomorrow at 17:00 UTC+2",
                    "tomorrow at 5pm utc+2",
                )
            )
        if phrase == "tomorrow at 5 p.m. UTC":
            variants.extend(
                (
                    "tomorrow at 5pm UTC",
                    "tomorrow at 5 pm UTC",
                    "tomorrow at 5 post meridiem UTC",
                )
            )

    if seed.family == "quarter":
        if phrase == "start of Q2":
            variants.extend(("start of q2", "the start of Q2"))
        if phrase == "mid Q1 2027":
            variants.extend(("mid q1 2027", "middle of Q1 2027"))

    if seed.family == "leap_year":
        if phrase == "the next leap year":
            variants.extend(("next leap year",))
        if phrase == "a day before the next leap year":
            variants.extend(("1 day before the next leap year",))

    if seed.family == "ordinal_month_year":
        if phrase == "the 7th of the 6th eighty one":
            variants.extend(
                (
                    "7th of the 6th eighty one",
                    "the 7th of the 6th 81",
                    "7th of the 6th 81",
                    "the seventh of the 6th 81",
                    "the 7th of the sixth 81",
                )
            )
        if phrase == "the first of the 3rd 22 @ 3pm":
            variants.extend(
                (
                    "first of the 3rd 22 @ 3pm",
                    "the 1st of the 3rd 22 @ 3pm",
                    "the first of the 3rd 22 at 3pm",
                    "1st of the 3rd 22 at 3pm",
                    "the first of the third 22 at 3pm",
                    "the 1st of the third 22 @ 3pm",
                )
            )
        if phrase == "7th of the 6th 81":
            variants.extend(
                (
                    "7th of the sixth 81",
                    "the 7th of the 6th 81",
                    "the 7th of the sixth 81",
                )
            )

    if seed.family == "month_anchor":
        if phrase == "the twelfth month":
            variants.extend(("twelfth month", "the 12th month"))
        if phrase == "the day before the twelfth month":
            variants.extend(
                (
                    "day before the twelfth month",
                    "the day before the 12th month",
                )
            )

    if seed.family == "relative_weekday":
        if phrase == "Tuesday gone":
            variants.extend(("tuesday gone", "the Tuesday gone"))
        if phrase == "Tuesday past":
            variants.extend(("tuesday past", "the Tuesday past"))

    if seed.family == "counted_weekday":
        if phrase == "two Fridays from now":
            variants.extend(
                (
                    "2 Fridays from now",
                    "two fridays from now",
                    "two Fridays hence",
                )
            )

    return _dedupe_keep_order([variant for variant in variants if variant != seed.phrase or True])


def generate_variant_cases():
    cases = []
    for seed in SEED_CASES:
        for variant in _family_variants(seed):
            cases.append(
                VariantCase(
                    phrase=variant,
                    expected=seed.expected,
                    family=seed.family,
                    source_phrase=seed.phrase,
                )
            )
    unique = []
    seen = set()
    for case in cases:
        key = (case.phrase.lower(), case.expected, case.family, case.source_phrase)
        if key in seen:
            continue
        seen.add(key)
        unique.append(case)
    return unique


def generate_extraction_cases():
    wrappers = (
        "let's do it {phrase} please",
        "how about {phrase} for the plan",
        "i think {phrase} works best",
    )
    cases = []
    for variant in generate_variant_cases():
        # Keep extraction cases focused on phrases that should be captured as one span.
        if len(variant.phrase.split()) < 2:
            continue
        for wrapper in wrappers:
            text = wrapper.format(phrase=variant.phrase)
            cases.append(
                ExtractionCase(
                    text=text,
                    expected_text=variant.phrase,
                    expected=variant.expected,
                    family=variant.family,
                    source_phrase=variant.source_phrase,
                )
            )

    unique = []
    seen = set()
    for case in cases:
        key = (case.text.lower(), case.expected_text.lower(), case.expected, case.family)
        if key in seen:
            continue
        seen.add(key)
        unique.append(case)
    return unique


def run_variant_sweep(reference=DEFAULT_REFERENCE):
    failures = []
    successes = []

    for case in generate_variant_cases():
        try:
            actual = str(Date(case.phrase, relative_to=reference))
        except Exception as exc:  # pragma: no cover
            failures.append(
                {
                    **asdict(case),
                    "actual": None,
                    "error": str(exc),
                }
            )
            continue

        record = {
            **asdict(case),
            "actual": actual,
        }
        if actual == case.expected:
            successes.append(record)
        else:
            failures.append(record)

    return {
        "reference": reference,
        "seed_count": len(SEED_CASES),
        "variant_count": len(successes) + len(failures),
        "success_count": len(successes),
        "failure_count": len(failures),
        "failures": failures,
    }


def run_extraction_sweep(reference=DEFAULT_REFERENCE):
    from stringtime import extract_dates

    failures = []
    successes = []

    for case in generate_extraction_cases():
        try:
            matches = extract_dates(case.text, relative_to=reference)
        except Exception as exc:  # pragma: no cover
            failures.append(
                {
                    **asdict(case),
                    "actual_text": None,
                    "actual": None,
                    "error": str(exc),
                }
            )
            continue

        if len(matches) != 1:
            failures.append(
                {
                    **asdict(case),
                    "actual_text": [match.text for match in matches],
                    "actual": [str(match.date) for match in matches],
                }
            )
            continue

        actual_text = matches[0].text
        actual = str(matches[0].date)
        record = {
            **asdict(case),
            "actual_text": actual_text,
            "actual": actual,
        }
        if actual_text == case.expected_text and actual == case.expected:
            successes.append(record)
        else:
            failures.append(record)

    return {
        "reference": reference,
        "seed_count": len(SEED_CASES),
        "extraction_variant_count": len(successes) + len(failures),
        "success_count": len(successes),
        "failure_count": len(failures),
        "failures": failures,
    }


def write_variant_failures(output_path, reference=DEFAULT_REFERENCE):
    result = run_variant_sweep(reference=reference)
    Path(output_path).write_text(json.dumps(result, indent=2) + "\n")
    return result


def write_extraction_failures(output_path, reference=DEFAULT_REFERENCE):
    result = run_extraction_sweep(reference=reference)
    Path(output_path).write_text(json.dumps(result, indent=2) + "\n")
    return result
