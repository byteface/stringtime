__version__ = "0.0.7"
__all__ = [
    "after",
    "Date",
    "DateMatch",
    "ParseMetadata",
    "builtin_holiday_alias_count",
    "builtin_holiday_definition_count",
    "clear_custom_holidays",
    "extract_dates",
    "is_after",
    "is_before",
    "is_same_day",
    "is_same_time",
    "register_holiday",
    "register_holiday_date",
    "register_holiday_dates",
    "register_holidays",
    "until",
]

import calendar
import contextvars
import datetime
import math
import re
import warnings
from dataclasses import dataclass

import ply.lex as lex
import ply.yacc as yacc
from dateutil.easter import easter
from dateutil.relativedelta import relativedelta

from stringtime.date import Date as stDate
from stringtime.holidays import (HOLIDAY_FIRST_TOKENS,
                                 builtin_holiday_alias_count,
                                 builtin_holiday_definition_count,
                                 clear_custom_holidays,
                                 get_registered_holiday_resolver,
                                 register_holiday, register_holiday_date,
                                 register_holiday_dates, register_holidays)
from stringtime.parse_metadata import ParseMetadata
from stringtime.vocabulary import (BUSINESS_WEEKDAY_TUPLE,
                                   BUSINESS_MONTHLY_ORDINAL_PATTERN,
                                   BUSINESS_QUARTERLY_ORDINAL_PATTERN,
                                   CARDINAL_NUMBER_MAP,
                                   CARDINAL_NUMBER_PATTERN,
                                   CARDINAL_NUMBER_WORD_SET,
                                   FUTURE_RELATIVE_PHRASE_PATTERN,
                                   FUZZY_QUALIFIER_WORD_SET,
                                   INDEFINITE_RELATIVE_ARTICLES, MONTH_ALIASES,
                                   MONTH_ALL_SET, MONTH_INDEX, MONTH_NAME_SET,
                                   MONTH_NAMES,
                                   MONTH_OR_ORDINAL_MONTH_PATTERN,
                                   NEGATIVE_RELATIVE_SIGN_PHRASES,
                                   NORMALIZATION_ALIASES as VOCAB_NORMALIZATION_ALIASES,
                                   NORMALIZATION_WORD_ALIASES as VOCAB_NORMALIZATION_WORD_ALIASES,
                                   PAST_RELATIVE_PHRASE_PATTERN,
                                   MONTH_PATTERN, ORDINAL_DAY_MAP,
                                   DATE_ORDINAL_PATTERN,
                                   ORDINAL_DAY_PATTERN,
                                   ORDINAL_MONTH_MAP,
                                   ORDINAL_MONTH_PATTERN,
                                   ORDINAL_OCCURRENCE_MAP,
                                   ORDINAL_OCCURRENCE_PATTERN,
                                   POSITIVE_ORDINAL_OCCURRENCE_PATTERN,
                                   RELATIVE_DAY_WORD_SET,
                                   WEEKDAY_ALIASES, WEEKDAY_INDEX,
                                   WEEKDAY_ALL_SET, WEEKDAY_NAME_SET,
                                   WEEKDAY_NAMES, WEEKDAY_OR_PLURAL_PATTERN,
                                   WEEKDAY_PLURAL_PATTERN, WEEKDAY_PATTERN,
                                   WEEKDAY_PLURALS, WEEKDAY_PLURAL_SET,
                                   WEEKEND_ORDINAL_PATTERN,
                                   month_regex,
                                   normalize_month_name,
                                   normalize_weekday_name,
                                   parse_cardinal_number, weekday_regex)

DEBUG = False
try:
    ERR_ICN = "\U0000274c"
    WARN_ICN = "\U000026a0"
    OK_ICN = "\U00002714"
    # print(__version__, ERR_ICN, WARN_ICN, OK_ICN)
except UnicodeEncodeError:
    warnings.warn("Warning: Icons not supported.")
    ERR_ICN = ""
    WARN_ICN = ""
    OK_ICN = ""


def stlog(msg: str, *args, lvl: str = None, **kwargs):
    """logging for stringtime"""
    if not DEBUG:
        return
    if lvl is None:
        print(msg, args, kwargs)
    elif "e" in lvl:  # error
        print(f"{ERR_ICN} \033[1;41m{msg}\033[1;0m", *args, kwargs)
    elif "w" in lvl:  # warning
        print(f"{WARN_ICN} \033[1;31m{msg}\033[1;0m", *args, kwargs)
    elif "g" in lvl:  # green for good
        print(f"{OK_ICN} \033[1;32m{msg}\033[1;0m", *args, kwargs)
    # else:
    #     print(msg, *args, kwargs)


TIMEZONE_OFFSETS = {
    "z": 0,
    "utc": 0,
    "gmt": 0,
    "est": -5 * 60,
    "edt": -4 * 60,
    "cst": -6 * 60,
    "cdt": -5 * 60,
    "mst": -7 * 60,
    "mdt": -6 * 60,
    "pst": -8 * 60,
    "pdt": -7 * 60,
    "bst": 1 * 60,
    "cet": 1 * 60,
    "cest": 2 * 60,
    "eet": 2 * 60,
    "eest": 3 * 60,
    "ist": 5 * 60 + 30,
    "jst": 9 * 60,
    "aest": 10 * 60,
    "aedt": 11 * 60,
    "acst": 9 * 60 + 30,
    "acdt": 10 * 60 + 30,
    "awst": 8 * 60,
}

EXTRACTION_TOKEN_RE = re.compile(r"[A-Za-z0-9@:+'.-]+")
TIME_TOKEN_RE = re.compile(
    r"(?:\d{1,2}\s?(?:am|pm)|\d{1,2}(?::\d{2})(?::\d{2})?(?:\s?(?:am|pm))?)$",
    re.IGNORECASE,
)
CURRENT_REFERENCE = contextvars.ContextVar("stringtime_reference", default=None)
MOON_PHASE_EPOCH = datetime.datetime(2000, 1, 6, 18, 14, 0)
SYNODIC_MONTH_DAYS = 29.530588853
WEEKDAY_RE = weekday_regex()
WEEKDAY_OR_PLURAL_RE = weekday_regex(include_plural=True)
MONTH_RE = month_regex()
ORDINAL_DAY_RE = ORDINAL_DAY_PATTERN
ORDINAL_MONTH_RE = ORDINAL_MONTH_PATTERN
CARDINAL_NUMBER_RE = CARDINAL_NUMBER_PATTERN
DAY_REFERENCE_RE = (
    rf"(?:today|tomorrow|yesterday|this|(?:next|last)\s+(?:{WEEKDAY_RE})|(?:{WEEKDAY_RE}))"
)
DATE_PREFIX_LOOKAHEAD_RE = (
    rf"(?:today|tomorrow|yesterday|next|last|this|noon|midnight|midday|{WEEKDAY_RE}|{MONTH_RE})"
)

NORMALIZATION_ALIASES = dict(VOCAB_NORMALIZATION_ALIASES)

NORMALIZATION_WORD_ALIASES = {
    **VOCAB_NORMALIZATION_WORD_ALIASES,
    "midnite": "midnight",
    "arvo": "afternoon",
    "eob": "end of business",
    "cob": "end of business",
    "cop": "end of play",
    "mid summer": "midsummer",
    "eom": "end of month",
    "eoy": "close of year",
    "coy": "close of year",
    **WEEKDAY_ALIASES,
    **MONTH_ALIASES,
}


def build_tzinfo(token):
    token = token.lower()

    if token in TIMEZONE_OFFSETS:
        return datetime.timezone(
            datetime.timedelta(minutes=TIMEZONE_OFFSETS[token]), token.upper()
        )

    if token.startswith(("utc", "gmt")) and len(token) > 3:
        match = re.fullmatch(r"(utc|gmt)([+-])(\d{1,2})(?::?(\d{2}))?", token)
        if match is None:
            return None

        sign = 1 if match.group(2) == "+" else -1
        hours = int(match.group(3))
        minutes = int(match.group(4) or 0)
        offset_minutes = sign * (hours * 60 + minutes)
        return datetime.timezone(
            datetime.timedelta(minutes=offset_minutes), token.upper()
        )

    return None


def extract_timezone_suffix(phrase):
    from stringtime.normalization import extract_timezone_suffix as _impl

    return _impl(phrase)


def apply_timezone(date_obj, tzinfo, timezone_aware=False):
    from stringtime.normalization import apply_timezone as _impl

    return _impl(date_obj, tzinfo, timezone_aware=timezone_aware)


def normalize_timezone_phrase(phrase):
    from stringtime.normalization import normalize_timezone_phrase as _impl

    return _impl(phrase)


def normalize_phrase(phrase):
    from stringtime.normalization import normalize_phrase as _impl

    return _impl(phrase)


def apply_word_aliases(phrase):
    from stringtime.normalization import apply_word_aliases as _impl

    return _impl(phrase)


def apply_literal_aliases(phrase):
    from stringtime.normalization import apply_literal_aliases as _impl

    return _impl(phrase)


@dataclass
class DateMatch:
    text: str
    start: int
    end: int
    date: stDate


@dataclass(frozen=True)
class AnchorDefinition:
    name: str
    families: tuple[str, ...]
    resolver: callable


def clone_date(date_obj):
    cloned = stDate()
    cloned._date = date_obj.to_datetime().replace()
    cloned.is_infinite = getattr(date_obj, "is_infinite", False)
    cloned.infinite_direction = getattr(date_obj, "infinite_direction", 0)
    cloned.parse_metadata = getattr(date_obj, "parse_metadata", None)
    return cloned


def coerce_reference_date(value):
    if value is None:
        return None
    if isinstance(value, stDate):
        return clone_date(value)
    if isinstance(value, datetime.datetime):
        d = stDate()
        d._date = value.replace()
        return d
    if isinstance(value, datetime.date):
        d = stDate()
        d._date = datetime.datetime.combine(value, datetime.time())
        return d
    if isinstance(value, (str, int)):
        return stDate(value)
    raise TypeError("relative_to must be a string, int, date, datetime, or Date")


def coerce_value_date(value, *, argument_name="value", default_now=False):
    if value is None:
        if default_now:
            return get_reference_date()
        raise TypeError(
            f"{argument_name} must be a string, int, date, datetime, or Date"
        )

    coerced = coerce_reference_date(value)
    if coerced is None:
        raise TypeError(
            f"{argument_name} must be a string, int, date, datetime, or Date"
        )
    return coerced


def normalize_duration_datetime(value):
    from stringtime.normalization import normalize_duration_datetime as _impl

    return _impl(value)


def comparable_datetime(value):
    if getattr(value, "is_infinite", False):
        return value
    return normalize_duration_datetime(value.to_datetime())


def compare_date_values(first, second):
    if getattr(first, "is_infinite", False) or getattr(second, "is_infinite", False):
        if getattr(first, "is_infinite", False) and getattr(
            second, "is_infinite", False
        ):
            if first.infinite_direction == second.infinite_direction:
                return 0
            return 1 if first.infinite_direction > second.infinite_direction else -1
        if getattr(first, "is_infinite", False):
            return 1 if first.infinite_direction > 0 else -1
        return -1 if second.infinite_direction > 0 else 1

    first_dt = comparable_datetime(first)
    second_dt = comparable_datetime(second)
    if first_dt < second_dt:
        return -1
    if first_dt > second_dt:
        return 1
    return 0


def format_duration_string(from_value, to_value):
    start = normalize_duration_datetime(from_value)
    end = normalize_duration_datetime(to_value)

    if end < start:
        start, end = end, start

    delta = relativedelta(end, start)
    weeks, days = divmod(delta.days, 7)
    components = [
        ("year", delta.years),
        ("month", delta.months),
        ("week", weeks),
        ("day", days),
        ("hour", delta.hours),
        ("minute", delta.minutes),
        ("second", delta.seconds),
    ]

    parts = []
    for label, value in components:
        if value == 0:
            continue
        suffix = "" if value == 1 else "s"
        parts.append(f"{value} {label}{suffix}")

    if not parts:
        return "0 seconds"
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return f"{', '.join(parts[:-1])} and {parts[-1]}"


def maybe_roll_until_target_forward(target, reference):
    if normalize_duration_datetime(target.to_datetime()) >= normalize_duration_datetime(
        reference.to_datetime()
    ):
        return target

    metadata = getattr(target, "parse_metadata", None)
    if metadata is None or metadata.used_dateutil:
        return target

    normalized = (metadata.normalized_text or "").strip().lower()
    if normalized == "" or normalized.startswith(("next ", "last ", "this ")):
        return target

    if get_registered_holiday_resolver(normalized) is None:
        return target

    return get_date(f"next {normalized}", relative_to=reference)


def resolve_duration_arguments(*args, from_=None, to=None, kwargs=None):
    from stringtime.normalization import resolve_duration_arguments as _impl

    return _impl(*args, from_=from_, to=to, kwargs=kwargs)


def get_reference_date():
    reference = CURRENT_REFERENCE.get()
    if reference is None:
        return stDate()
    return clone_date(reference)


def attach_parse_metadata(date_obj, metadata):
    date_obj.parse_metadata = metadata
    return date_obj


def build_parse_metadata(
    input_text,
    matched_text,
    normalized_text,
    *,
    exact,
    fuzzy,
    used_dateutil,
    semantic_kind=None,
    representative_granularity=None,
    recurrence_frequency=None,
    recurrence_interval=None,
    recurrence_byweekday=None,
    recurrence_bymonth=None,
    recurrence_bymonthday=None,
    recurrence_ordinal=None,
    recurrence_byhour=None,
    recurrence_byminute=None,
    recurrence_until=None,
    recurrence_start=None,
    recurrence_exclusions=None,
    recurrence_window_start=None,
    recurrence_window_end=None,
):
    from stringtime.composition import build_parse_metadata as _impl

    return _impl(
        input_text,
        matched_text,
        normalized_text,
        exact=exact,
        fuzzy=fuzzy,
        used_dateutil=used_dateutil,
        semantic_kind=semantic_kind,
        representative_granularity=representative_granularity,
        recurrence_frequency=recurrence_frequency,
        recurrence_interval=recurrence_interval,
        recurrence_byweekday=recurrence_byweekday,
        recurrence_bymonth=recurrence_bymonth,
        recurrence_bymonthday=recurrence_bymonthday,
        recurrence_ordinal=recurrence_ordinal,
        recurrence_byhour=recurrence_byhour,
        recurrence_byminute=recurrence_byminute,
        recurrence_until=recurrence_until,
        recurrence_start=recurrence_start,
        recurrence_exclusions=recurrence_exclusions,
        recurrence_window_start=recurrence_window_start,
        recurrence_window_end=recurrence_window_end,
    )


def finalize_parsed_candidate(
    candidate,
    *,
    tzinfo,
    timezone_aware,
    raw_text,
    matched_text,
    normalized_phrase,
    fuzzy,
    metadata_overrides=None,
):
    from stringtime.composition import finalize_parsed_candidate as _impl

    return _impl(
        candidate,
        tzinfo=tzinfo,
        timezone_aware=timezone_aware,
        raw_text=raw_text,
        matched_text=matched_text,
        normalized_phrase=normalized_phrase,
        fuzzy=fuzzy,
        metadata_overrides=metadata_overrides,
    )


def finalize_first_matching_candidate(
    candidates,
    *,
    tzinfo,
    timezone_aware,
    raw_text,
    matched_text,
    normalized_phrase,
    fuzzy,
):
    from stringtime.composition import finalize_first_matching_candidate as _impl

    return _impl(
        candidates,
        tzinfo=tzinfo,
        timezone_aware=timezone_aware,
        raw_text=raw_text,
        matched_text=matched_text,
        normalized_phrase=normalized_phrase,
        fuzzy=fuzzy,
    )


def finalize_infinity_candidate(
    phrase,
    *,
    raw_text,
    matched_text,
    fuzzy,
):
    from stringtime.composition import finalize_infinity_candidate as _impl

    return _impl(
        phrase,
        raw_text=raw_text,
        matched_text=matched_text,
        fuzzy=fuzzy,
    )


def normalize_parse_input(raw_text):
    from stringtime.normalization import normalize_parse_input as _impl

    return _impl(raw_text)


def collect_direct_parse_candidates(phrase, *args, timezone_aware=False, **kwargs):
    return {
        "simple_clock_instant_date": get_simple_clock_instant_date(phrase),
        "simple_numeric_instant_date": get_simple_numeric_instant_date(phrase),
        "leap_year_offset_date": get_leap_year_offset_date(phrase),
        "ordinal_time_coordinate_date": get_ordinal_time_coordinate_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "compact_offset_date": get_compact_offset_phrase_date(phrase),
        "relative_month_day_date": get_relative_month_day_phrase_date(phrase),
        "counted_weekday_date": get_counted_weekday_phrase_date(phrase),
        "counted_month_date": get_counted_month_phrase_date(phrase),
        "counted_holiday_date": get_counted_holiday_phrase_date(phrase),
        "weekday_and_date_date": get_weekday_and_date_phrase_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "weekday_in_month_date": get_weekday_in_month_date(phrase),
        "counted_weekday_anchor_date": get_counted_weekday_anchor_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "recurring_weekday_date": get_recurring_weekday_date(
            phrase, *args, timezone_aware=timezone_aware, **kwargs
        ),
        "recurring_schedule_date": get_recurring_schedule_date(
            phrase, *args, timezone_aware=timezone_aware, **kwargs
        ),
        "weekday_anchor_date": get_weekday_anchor_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "ordinal_weekday_anchor_date": get_ordinal_weekday_anchor_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "add_subtract_date": get_add_subtract_phrase_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "ordinal_month_year_date": get_ordinal_month_year_date(phrase),
        "relative_period_date": get_relative_period_phrase_date(phrase),
        "weekday_occurrence_period_date": get_weekday_occurrence_period_phrase_date(
            phrase
        ),
        "quarter_phrase_date": get_quarter_phrase_date(phrase),
        "month_anchor_date": get_month_anchor_date(phrase),
        "week_of_month_anchor_date": get_week_of_month_anchor_date(phrase),
        "leap_year_anchor_date": get_leap_year_anchor_date(phrase),
        "business_date": get_business_phrase_date(phrase),
        "sleep_date": get_sleep_phrase_date(phrase),
        "clock_date": get_clock_phrase_date(phrase),
        "compound_clock_date": get_compound_clock_phrase_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "anchor_offset_date": get_anchor_offset_phrase_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "year_wrapped_date": get_year_wrapped_phrase_date(
            phrase, *args, timezone_aware=timezone_aware, **kwargs
        ),
        "composed_date_time": get_composed_date_time_phrase_date(
            phrase, *args, timezone_aware=timezone_aware, **kwargs
        ),
    }


def finalize_part_of_day_stage(
    part_of_day_date,
    *,
    normalized_phrase,
    tzinfo,
    timezone_aware,
    raw_text,
    matched_text,
    fuzzy,
):
    from stringtime.composition import finalize_part_of_day_stage as _impl

    return _impl(
        part_of_day_date,
        normalized_phrase=normalized_phrase,
        tzinfo=tzinfo,
        timezone_aware=timezone_aware,
        raw_text=raw_text,
        matched_text=matched_text,
        fuzzy=fuzzy,
    )


def finalize_composed_stage(
    composed_date_time,
    registered_anchor_definition,
    *,
    normalized_phrase,
    tzinfo,
    timezone_aware,
    raw_text,
    matched_text,
    fuzzy,
):
    from stringtime.composition import finalize_composed_stage as _impl

    return _impl(
        composed_date_time,
        registered_anchor_definition,
        normalized_phrase=normalized_phrase,
        tzinfo=tzinfo,
        timezone_aware=timezone_aware,
        raw_text=raw_text,
        matched_text=matched_text,
        fuzzy=fuzzy,
    )


def split_recurring_phrase_parts(phrase):
    from stringtime.recurrence import split_recurring_phrase_parts as _impl

    return _impl(phrase)


def parse_recurring_weekday_series(text):
    from stringtime.recurrence import parse_recurring_weekday_series as _impl

    return _impl(text)


def format_recurrence_time_value(time_text, *, part_of_day=None):
    from stringtime.recurrence import format_recurrence_time_value as _impl

    return _impl(time_text, part_of_day=part_of_day)


def parse_recurring_exclusions(text):
    from stringtime.recurrence import parse_recurring_exclusions as _impl

    return _impl(text)


def infer_recurring_details(phrase):
    from stringtime.recurrence import infer_recurring_details as _impl

    return _impl(phrase)


def infer_phrase_semantics(phrase):
    phrase = (phrase or "").strip().lower()

    if phrase in {"forever", "for ever", "infinity", "∞"}:
        return "infinity", "unbounded"

    if phrase == "" or is_now(phrase):
        return "instant", "second"

    if (
        phrase.startswith(
            ("end of", "start of", "close of", "first day of", "last day of")
        )
        or phrase.startswith(("end of business", "end of play", "eop"))
        or "midnight" in phrase
    ):
        if "quarter" in phrase:
            return "boundary", "quarter"
        if "month" in phrase:
            return "boundary", "month"
        if "year" in phrase:
            return "boundary", "year"
        if "midnight" in phrase:
            return "boundary", "minute"
        return "boundary", "hour"

    if re.fullmatch(
        r"(?:the\s+)?(?:first|1st|third|3rd|last)\s+(?:business|working)\s+day\s+of\s+(?:each|every)\s+month",
        phrase,
    ):
        return "recurring", "month"

    if re.fullmatch(
        r"(?:the\s+)?(?:first|1st|last)\s+(?:business|working)\s+day\s+of\s+(?:each|every)\s+quarter",
        phrase,
    ):
        return "recurring", "quarter"

    if any(
        token in phrase
        for token in (
            "from now",
            "ago",
            "hence",
            "before now",
            "after now",
            "in the future",
            "in the past",
            "business days",
            "working day",
            "fortnight",
            "sleeps",
        )
    ):
        return "relative_offset", "second"

    if re.fullmatch(
        rf"(?:(?:on\s+)?(?:(?:every)\s+)?(?:{WEEKDAY_PLURAL_PATTERN})|every\s+(?:{WEEKDAY_RE}))",
        phrase,
    ):
        return "recurring", "week"

    if re.fullmatch(
        r"(?:on\s+)?(?:every\s+)?(?:weekday|weekdays|weekend|weekends)",
        phrase,
    ):
        return "recurring", "week"

    if re.fullmatch(
        r"(?:the\s+)?(?:first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th|last|penultimate)\s+"
        rf"(?:{WEEKDAY_RE})\s+of\s+(?:each|every)\s+month",
        phrase,
    ):
        return "recurring", "month"

    if re.fullmatch(
        rf"(?:every\s+month\s+on\s+|on\s+)?(?:the\s+)?(?:{DATE_ORDINAL_PATTERN})\s+of\s+(?:each|every)\s+month|every\s+month\s+on\s+(?:the\s+)?(?:{DATE_ORDINAL_PATTERN})",
        phrase,
    ):
        return "recurring", "month"

    if re.fullmatch(
        rf"every\s+(?:christmas|boxing day|christmas eve|new year's day|new years day|halloween|easter|(?:{MONTH_RE})\s+\d{{1,2}}(?:st|nd|rd|th)|(?:the\s+)?\d{{1,2}}(?:st|nd|rd|th)\s+of\s+(?:{MONTH_RE}))",
        phrase,
    ):
        return "recurring", "year"

    if re.fullmatch(r"every\s+(?:business|working)\s+day", phrase):
        return "recurring", "week"

    if any(
        token in phrase
        for token in (
            "morning",
            "afternoon",
            "evening",
            "night",
            "lunchtime",
            "first thing",
        )
    ):
        return "period", "part_of_day"

    if any(
        token in phrase
        for token in (
            "christmas",
            "xmas",
            "easter",
            "thanksgiving",
            "halloween",
            "labor day",
            "bank holiday",
            "new year's day",
            "new years day",
        )
    ):
        return "period", "day"

    if re.search(r"\b(at|@)\b", phrase) or re.search(
        r"\b\d{1,2}(:\d{2})?(\s?(am|pm))?\b", phrase
    ):
        return "instant", "minute"

    if phrase in {
        "noon",
        "midday",
        "chinese dentist",
        "cowboy time",
    } or phrase.startswith(("quarter past", "quarter to", "half past", "half ")):
        return "instant", "minute"

    if re.search(
        rf"\b({WEEKDAY_RE}|today|tomorrow|yesterday)\b",
        phrase,
    ):
        return "period", "day"

    if re.search(r"\b\d+(st|nd|rd|th)\b", phrase) or re.search(
        r"\b(first|second|third|fourth|fifth|penultimate|last)\b", phrase
    ):
        return "period", "day"

    return "instant", "second"


def get_composed_metadata_overrides(phrase):
    phrase = (phrase or "").strip().lower()

    recurring_monthly_with_time_patterns = (
        rf"(?:the\s+)?(?:first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th|last|penultimate)\s+(?:{WEEKDAY_RE})\s+of\s+(?:each|every)\s+month\s+(?:at|@)\s+.+",
        r"(?:the\s+)?(?:first|1st|last)\s+(?:business|working)\s+day\s+of\s+(?:each|every)\s+month\s+(?:at|@)\s+.+",
        rf"(?:every\s+month\s+on\s+|on\s+)?(?:the\s+)?(?:{DATE_ORDINAL_PATTERN})\s+of\s+(?:each|every)\s+month\s+(?:at|@)\s+.+",
    )
    for pattern in recurring_monthly_with_time_patterns:
        if re.fullmatch(pattern, phrase):
            return {
                "semantic_kind": "recurring",
                "representative_granularity": "month",
            }

    recurring_yearly_with_time_patterns = (
        rf"every\s+(?:christmas|boxing day|christmas eve|new year's day|new years day|halloween|easter|(?:{MONTH_RE})\s+\d{{1,2}}(?:st|nd|rd|th)|(?:the\s+)?\d{{1,2}}(?:st|nd|rd|th)\s+of\s+(?:{MONTH_RE}))\s+(?:at|@)\s+.+",
    )
    for pattern in recurring_yearly_with_time_patterns:
        if re.fullmatch(pattern, phrase):
            return {
                "semantic_kind": "recurring",
                "representative_granularity": "year",
            }

    recurring_quarterly_with_time_patterns = (
        r"(?:the\s+)?(?:first|1st|last)\s+(?:business|working)\s+day\s+of\s+(?:each|every)\s+quarter\s+(?:at|@)\s+.+",
    )
    for pattern in recurring_quarterly_with_time_patterns:
        if re.fullmatch(pattern, phrase):
            return {
                "semantic_kind": "recurring",
                "representative_granularity": "quarter",
            }

    recurring_workweek_with_time_patterns = (
        r"every\s+(?:business|working)\s+day\s+(?:at|@)\s+.+",
    )
    for pattern in recurring_workweek_with_time_patterns:
        if re.fullmatch(pattern, phrase):
            return {
                "semantic_kind": "recurring",
                "representative_granularity": "week",
            }

    recurring_with_time_patterns = (
        rf"(?:on\s+)?(?:{WEEKDAY_PLURAL_PATTERN})\s+(?:at|@)\s+.+",
        rf"every\s+(?:{WEEKDAY_RE})\s+(?:at|@)\s+.+",
        r"(?:on\s+)?(?:every\s+)?(?:weekday|weekdays|weekend|weekends)\s+(?:at|@)\s+.+",
    )
    for pattern in recurring_with_time_patterns:
        if re.fullmatch(pattern, phrase):
            return {
                "semantic_kind": "recurring",
                "representative_granularity": "week",
            }

    return {}


def get_recurring_schedule_granularity(phrase):
    from stringtime.recurrence import get_recurring_schedule_granularity as _impl

    return _impl(phrase)


# -----------------------------------------------------------------------------

from stringtime.parser_lex import (
    tokens,
    t_COLON,
    t_AND,
    t_HALF,
    t_DATE_END,
    t_PLUS,
    t_MINUS,
    t_DECIMAL,
    t_NUMBER,
    t_WORD_NUMBER,
    t_DAY,
    t_REC_GROUP,
    t_BUSINESS,
    t_MONTH,
    t_TIME,
    t_PHRASE,
    t_PAST_PHRASE,
    t_YESTERDAY,
    t_TOMORROW,
    t_TODAY,
    t_THIS,
    t_NEXT,
    t_EVERY,
    t_UNTIL,
    t_THROUGH,
    t_EXCEPT,
    t_FROM,
    t_AFTER_TOMORROW,
    t_BEFORE_YESTERDAY,
    t_AT,
    t_ON,
    t_OF,
    t_AM,
    t_PM,
    t_THE,
    t_ignore,
)

# def t_DATE_STRING(t):
# TODO - the same in reverse. so turns a date string, relative to now, into human readable text
# i.e. 2 minutes ago
# TODO - might make sense to do a seperate parser for this one.


def t_error(t):
    raise TypeError("Unknown text '%s'" % (t.value,))


lex.lex()


class DateFactory:
    def __init__(self, phrase, *args, **kwargs):
        self.phrase = phrase

    @staticmethod
    def create_date(
        year=None, month=None, week=None, day=None, hour=None, minute=None, second=None
    ):
        """creates a date with fixed props

        unlike datatime it uses 0 indexing for months

        Args:
            year (_type_, optional): The year. Defaults to None.
            month (_type_, optional): the month (0-11). Defaults to None.
            week (_type_, optional): _description_. Defaults to None.
            day (_type_, optional): _description_. Defaults to None.
            hour (_type_, optional): _description_. Defaults to None.
            minute (_type_, optional): _description_. Defaults to None.
            second (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        d = get_reference_date()
        if year is not None:
            d.set_year(year)
        if month is not None:
            d.set_month(month)
        if week is not None:
            d.set_week(week)
        if day is not None:
            d.set_date(day)
        if hour is not None:
            d.set_hours(hour)
        if minute is not None:
            d.set_minutes(minute)
        if second is not None:
            d.set_seconds(second)
        return d

    # todo - consider renaming all the props to offset_
    @staticmethod
    def create_date_with_offsets(
        year=None, month=None, week=None, day=None, hour=None, minute=None, second=None
    ):
        """PARAMS NEED TO BE PASSED AS OFFSETS!

        this creates a now date with an offset for each property of the time
        remember all props are offsets so don't set directly.
        They shift the current time for every given prop.

        - use positive integers to increment a prop
        - use negative integers to deduct from a prop

        Args:
            year (_type_, optional): Number of years to add/take from the current year.
            month (int, optional): Number of months to add/take from the current month.
            week (int, optional): Number of weeks to add/take from the current week.
            day (int, optional): Number of days to add/take from the current day.
            hour (int, optional): Number of hours to add/take from the current hour.
            minute (int, optional): Number of minutes to add/take from the current minute.
            second (int, optional): Number of seconds to add/take from the current second.

        Returns:
            Date : Returns a Date object with the offsets applied.
        """
        # print("Creating date!!", year, month, week, day, hour, minute, second)
        # TODO - should maybe optionally pass and remember the phrase on a new 'description' prop on Date...?
        d = get_reference_date()
        if year is not None:
            stlog(
                f"Increasing years by {year}",
                str(d),
                lvl="g",
            )
            current_year = d.get_year()
            d.set_fullyear(current_year + year)
        if month is not None:
            stlog(
                f"Increasing months by {month}",
                str(d),
            )
            currrent_month = d.get_month()
            d.set_month(
                currrent_month + (month)  # - 1)
            )  # note the minus one is because Date expects 0-11 but humans say 1-12. wrong cos its the offset?
        if week is not None:
            stlog(
                f"Increasing weeks by {week}",
                str(d),
                lvl="g",
            )
            currrent_day = d.get_date()
            d.set_date(currrent_day + week * 7)
        if day is not None:
            stlog(
                f"Increasing days by {day}",
                str(d),
                lvl="g",
            )
            currrent_day = d.get_date()
            d.set_date(currrent_day + day)
        if hour is not None:
            stlog(
                f"Increasing hours by {hour}",
                str(d),
                lvl="g",
            )
            currrent_hour = d.get_hours()
            d.set_hours(currrent_hour + hour)
        if minute is not None:
            stlog(
                f"Increasing minutes by {minute}",
                str(d),
                lvl="g",
            )
            currrent_minute = d.get_minutes()
            d.set_minutes(currrent_minute + minute)
        if second is not None:
            stlog(
                f"Increasing seconds by {second}",
                str(d),
                lvl="g",
            )
            currrent_second = d.get_seconds()
            d.set_seconds(currrent_second + second)

        return d

    @staticmethod
    def create_date_with_half_offset(unit, whole=1, sign=1):
        """Create mixed offsets for phrases like 'an hour and a half'."""
        params = {}
        whole = whole * sign

        if unit == "minute":
            params["minute"] = whole
            params["second"] = 30 * sign
        elif unit == "hour":
            params["hour"] = whole
            params["minute"] = 30 * sign
        elif unit == "day":
            params["day"] = whole
            params["hour"] = 12 * sign
        elif unit == "week":
            params["week"] = whole
            params["day"] = 3 * sign
            params["hour"] = 12 * sign
        elif unit == "month":
            params["month"] = whole
            params["day"] = 15 * sign
        elif unit == "year":
            params["year"] = whole
            params["month"] = 6 * sign
        else:
            params[unit] = whole

        return DateFactory.create_date_with_offsets(**params)

    @staticmethod
    def create_date_with_fractional_offset(unit, value, sign=1):
        """Create offsets for decimal durations like '1.5 days'."""
        whole = int(value)
        fraction = value - whole

        if abs(fraction - 0.5) < 1e-9:
            return DateFactory.create_date_with_half_offset(
                unit, whole=whole, sign=sign
            )

        params = {unit: value * sign}

        # Fall back to the nearest supported sub-unit when possible.
        if unit == "minute":
            params = {"minute": whole * sign, "second": round(60 * fraction) * sign}
        elif unit == "hour":
            params = {"hour": whole * sign, "minute": round(60 * fraction) * sign}
        elif unit == "day":
            params = {"day": whole * sign, "hour": round(24 * fraction) * sign}
        elif unit == "week":
            total_days = 7 * value
            whole_days = int(total_days)
            params = {
                "day": whole_days * sign,
                "hour": round((total_days - whole_days) * 24) * sign,
            }

        return DateFactory.create_date_with_offsets(**params)


def normalize_relative_whole(value):
    return 1 if value in INDEFINITE_RELATIVE_ARTICLES else value


def relative_phrase_sign(direction):
    return -1 if direction in NEGATIVE_RELATIVE_SIGN_PHRASES else 1


def build_relative_offset_date(unit, amount, sign=1):
    if isinstance(amount, float):
        return DateFactory.create_date_with_fractional_offset(unit, amount, sign=sign)
    return DateFactory.create_date_with_offsets(**{unit: sign * amount})


def build_compound_relative_offset_date(
    first_unit, first_amount, second_unit, second_amount, sign=1
):
    params = {
        first_unit: sign * first_amount,
        second_unit: sign * second_amount,
    }
    return DateFactory.create_date_with_offsets(**params)


def build_half_relative_offset_date(unit, whole, sign=1):
    return DateFactory.create_date_with_half_offset(
        unit,
        whole=normalize_relative_whole(whole),
        sign=sign,
    )


def normalize_meridiem_hour(hour, meridiem):
    if meridiem == "pm" and hour < 12:
        return hour + 12
    if meridiem == "am" and hour == 12:
        return 0
    return hour


def build_hour_date(hour, meridiem=None):
    normalized_hour = normalize_meridiem_hour(hour, meridiem)
    return DateFactory.create_date(hour=normalized_hour, minute=0, second=0)


def build_timestamp_date(hour, minute, second=0):
    return DateFactory.create_date(hour=hour, minute=minute, second=second)


def apply_meridiem_to_date(date_obj, meridiem):
    adjusted = clone_date(date_obj)
    adjusted.set_hours(normalize_meridiem_hour(adjusted.get_hours(), meridiem))
    return adjusted



def build_relative_day_token_date(day_offset, tokens):
    if len(tokens) == 1:
        return DateFactory.create_date_with_offsets(day=day_offset)

    if len(tokens) == 2 and isinstance(tokens[1], stDate):
        merged = DateFactory.create_date_with_offsets(day=day_offset)
        return merge_date_parts(merged, tokens[1])

    if len(tokens) == 3:
        if tokens[1] == "at" and isinstance(tokens[2], stDate):
            merged = DateFactory.create_date_with_offsets(day=day_offset)
            return merge_date_parts(merged, tokens[2])
        if isinstance(tokens[1], (int, float)) and tokens[2] in {"am", "pm"}:
            hour_date = build_hour_date(tokens[1], tokens[2])
            return DateFactory.create_date(
                day=get_reference_date().get_date() + day_offset,
                hour=hour_date.get_hours(),
                minute=0,
                second=0,
            )
        return DateFactory.create_date(
            day=get_reference_date().get_date() + day_offset,
            hour=tokens[2],
            minute=0,
            second=0,
        )

    if len(tokens) == 4:
        hour_date = build_hour_date(tokens[2], tokens[3])
        return DateFactory.create_date(
            day=get_reference_date().get_date() + day_offset,
            hour=hour_date.get_hours(),
            minute=0,
            second=0,
        )

    return None


def build_relative_day_rule_date(day_offset, tokens):
    normalized_tokens = tokens[1:] if len(tokens) > 1 and tokens[0] == "the" else tokens
    return build_relative_day_token_date(day_offset, normalized_tokens)


def build_period_rule_date(relation, unit, tail=None):
    base = get_relative_period_phrase_date(f"{relation} {unit}")
    if base is None or tail is None:
        return base
    return merge_date_parts(base, tail)


def build_period_prefix(relation, unit):
    if unit not in {"week", "month", "year"}:
        return None
    return relation, unit


def render_period_prefix(period_prefix):
    if period_prefix is None:
        return None
    return f"{period_prefix[0]} {period_prefix[1]}"


def render_recurring_time_tail(value):
    if not isinstance(value, stDate):
        return None
    hour = value.get_hours()
    minute = value.get_minutes()
    second = value.get_seconds()
    if second:
        return f"at {hour:02d}:{minute:02d}:{second:02d}"
    if minute:
        return f"at {hour:02d}:{minute:02d}"
    return f"at {hour:02d}:00"


def build_recurring_grammar_date(*parts):
    phrase = " ".join(part for part in parts if part).strip()
    if phrase == "":
        return None
    return get_recurring_schedule_date(phrase)


def build_anchor_offset_date(anchor_date, unit, amount, direction):
    if direction in {"before", "last"}:
        return apply_relative_offset(anchor_date, unit, amount, sign=-1)
    if direction in {"after", "next"}:
        return apply_relative_offset(anchor_date, unit, amount, sign=1)
    return None


def build_compound_anchor_offset_date(
    anchor_date, first_unit, first_amount, second_unit, second_amount, direction
):
    date_obj = build_anchor_offset_date(anchor_date, first_unit, first_amount, direction)
    if date_obj is None:
        return None
    return apply_relative_offset(
        date_obj,
        second_unit,
        second_amount,
        sign=relative_phrase_sign(direction),
    )


def build_half_anchor_offset_date(anchor_date, unit, whole, direction):
    sign = relative_phrase_sign(direction)
    whole = normalize_relative_whole(whole)
    return anchor_date.add(unit, whole * sign).add(unit, 0.5 * sign)


from stringtime import parser_grammar


yacc.yacc(module=parser_grammar)


###############################################################################


def is_now(phrase):
    """
    Check if the phrase is "now".
    These shouldn't need to go thru the parser.
    """
    return phrase.lower() in [
        "now",
        "right now",
        "right away",
        "right this second",
        "right this minute",
        "immediately",
        "straight away",
        "at once",
        "as soon as possible",
        "this current moment",
        "asap",
        "here and now",
        "today",  # this one also requires a token. i.e. today at 5pm
    ]


def replace_short_words(phrase):
    """
    replace shortened words with normal equivalents
    """

    protected_second_unit = "__stringtime_second_unit__"

    def replace_fractional_words(match):
        raw_number = match.group("number")
        unit = match.group("unit")
        word_numbers = {
            "a": 1,
            "an": 1,
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
            "eleven": 11,
            "twelve": 12,
            "thirteen": 13,
            "fourteen": 14,
            "fifteen": 15,
            "sixteen": 16,
            "seventeen": 17,
            "eighteen": 18,
            "nineteen": 19,
            "twenty": 20,
            "thirty": 30,
            "forty": 40,
            "fifty": 50,
            "sixty": 60,
            "seventy": 70,
            "eighty": 80,
            "ninety": 90,
        }
        if raw_number.isdigit():
            value = int(raw_number)
        else:
            value = word_numbers[raw_number]
        return f"{value + 0.5} {unit}"

    def replace_quarter_words(match):
        raw_number = match.group("number")
        unit = match.group("unit")
        quarter_values = {
            "a": 0.25,
            "an": 0.25,
            "one": 0.25,
            "three": 0.75,
        }
        return f"{quarter_values[raw_number]} {unit}"

    def ordinal_suffix(value):
        if 10 <= value % 100 <= 20:
            return "th"
        return {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")

    def replace_compound_ordinal_words(match):
        tens_word = match.group("tens")
        ones_word = match.group("ones")
        tens_values = {"twenty": 20, "thirty": 30}
        ones_ordinals = {
            "first": 1,
            "second": 2,
            "third": 3,
            "fourth": 4,
            "fifth": 5,
            "sixth": 6,
            "seventh": 7,
            "eighth": 8,
            "ninth": 9,
        }
        value = tens_values[tens_word] + ones_ordinals[ones_word]
        return f"{value}{ordinal_suffix(value)}"

    def replace_simple_ordinal_words(match):
        word = match.group("ordinal")
        ordinal_values = {
            "first": 1,
            "second": 2,
            "third": 3,
            "fourth": 4,
            "fifth": 5,
            "sixth": 6,
            "seventh": 7,
            "eighth": 8,
            "ninth": 9,
            "tenth": 10,
            "eleventh": 11,
            "twelfth": 12,
            "thirteenth": 13,
            "fourteenth": 14,
            "fifteenth": 15,
            "sixteenth": 16,
            "seventeenth": 17,
            "eighteenth": 18,
            "nineteenth": 19,
            "twentieth": 20,
            "thirtieth": 30,
        }
        value = ordinal_values[word]
        return f"{value}{ordinal_suffix(value)}"

    def rewrite_month_relative_on(match):
        direction = match.group("direction")
        day = match.group("day")
        suffix = match.group("suffix")
        return f"{day}{suffix} of {direction} month"

    def rewrite_day_time_phrase(match):
        day_phrase = match.group("day_phrase")
        time_phrase = match.group("time_phrase")
        return f"{time_phrase} {day_phrase}"

    def normalize_ish_time(match):
        return match.group("hour")

    def replace_scaled_year_units(match):
        count = int(match.group("count"))
        scale = match.group("scale")
        multiplier = {
            "decade": 10,
            "decades": 10,
            "century": 100,
            "centuries": 100,
            "millennium": 1000,
            "millenium": 1000,
            "millennia": 1000,
        }[scale]
        return f"{count * multiplier} years"

    # TODO - regexes might be better here. allow space or number in front
    # phrase = re.sub(r'[\s*\d*](hrs)', 'hour', phrase)
    phrase = re.sub(
        r"\b(?P<number>\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|few|several)\s+second\b",
        lambda match: f"{match.group('number')} {protected_second_unit}",
        phrase,
    )
    phrase = re.sub(
        r"\bhalf\s+(?:a\s+|an\s+)?second\b",
        f"half {protected_second_unit}",
        phrase,
    )
    phrase = re.sub(
        rf"\b(?P<number>\d+|{CARDINAL_NUMBER_RE})\s+and\s+a\s+half\s+(?P<unit>years?|months?|weeks?|days?|hours?|minutes?|seconds?)\b",
        replace_fractional_words,
        phrase,
    )
    phrase = re.sub(
        r"\b(?P<tens>twenty|thirty)\s+(?P<ones>first|second|third|fourth|fifth|sixth|seventh|eighth|ninth)\b",
        replace_compound_ordinal_words,
        phrase,
    )
    phrase = re.sub(
        r"\b(?P<ordinal>first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|thirtieth)\b",
        replace_simple_ordinal_words,
        phrase,
    )
    phrase = re.sub(
        r"\b(?P<direction>last|next)\s+month\s+on\s+the\s+(?P<day>\d+)(?P<suffix>st|nd|rd|th)\b",
        rewrite_month_relative_on,
        phrase,
    )
    phrase = re.sub(
        rf"\b(?P<day_phrase>(?:(?:last|next)\s+)?(?:{WEEKDAY_RE})|today|tomorrow|yesterday)\s+(?:at|@)\s+(?P<time_phrase>\d{{1,2}}:\d{{2}}(?:\s?(?:am|pm))?)\b",
        rewrite_day_time_phrase,
        phrase,
    )
    phrase = re.sub(
        r"\b(?P<number>a|an|one|three)\s+quarters?\s+of\s+(?:an?\s+)?(?P<unit>years?|months?|weeks?|days?|hours?|minutes?|seconds?)\b",
        replace_quarter_words,
        phrase,
    )

    # phrase = phrase.replace("ms", "millisecond")
    # phrase = phrase.replace("mil", "millisecond")
    phrase = re.sub(r"\bms\b", "millisecond", phrase)
    phrase = re.sub(r"\bmil\b", "millisecond", phrase)
    phrase = re.sub(r"\bmils\b", "millisecond", phrase)
    # phrase = phrase.replace("mils", "millisecond")

    phrase = re.sub(r"\bcouple of\b", "2", phrase)
    phrase = re.sub(r"\ba few\b", "3", phrase)
    phrase = re.sub(r"\bfew\b", "3", phrase)
    phrase = re.sub(r"\bseveral\b", "7", phrase)
    phrase = re.sub(r"\bhalf\s+second\b", "half a second", phrase)
    phrase = re.sub(r"\bhalf\s+millisecond\b", "half a millisecond", phrase)
    phrase = re.sub(
        r"\b(?P<count>\d+)\s+(?P<scale>decade|decades|century|centuries|millennium|millenium|millennia)\b",
        replace_scaled_year_units,
        phrase,
    )

    phrase = phrase.replace("century", "100 years")
    phrase = phrase.replace("centuries", "100 years")
    phrase = phrase.replace("decade", "10 years")
    phrase = phrase.replace("decades", "10 years")
    # phrase = phrase.replace("millenium", "1000 years")
    # phrase = phrase.replace("millenia", "1000 years")
    phrase = re.sub(r"\bmillenium\b", "1000 years", phrase)
    phrase = re.sub(r"\bmillennium\b", "1000 years", phrase)
    phrase = re.sub(r"\bmillenia\b", "1000 years", phrase)

    # special cases
    phrase = re.sub(r"\ba fortnight\b", "2 weeks", phrase)
    phrase = re.sub(r"\bfortnights\b", "2 weeks", phrase)
    phrase = re.sub(r"\bfortnight\b", "2 weeks", phrase)
    # phrase = re.sub(r"a few\b", "3", phrase)
    # phrase = re.sub(r"\bseveral\b", "7", phrase)

    phrase = apply_word_aliases(phrase)

    for source, target in NORMALIZATION_ALIASES.items():
        phrase = phrase.replace(source, target)

    phrase = re.sub(r"\b(?P<hour>\d{1,2})ish\b", normalize_ish_time, phrase)
    phrase = phrase.replace(protected_second_unit, "second")

    return phrase


def nth_weekday_of_month(year, month, weekday, occurrence):
    d = datetime.date(year, month, 1)
    while d.weekday() != weekday:
        d += datetime.timedelta(days=1)
    d += datetime.timedelta(weeks=occurrence - 1)
    return d


def last_weekday_of_month(year, month, weekday):
    if month == 12:
        d = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        d = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    while d.weekday() != weekday:
        d -= datetime.timedelta(days=1)
    return d


def penultimate_weekday_of_month(year, month, weekday):
    return last_weekday_of_month(year, month, weekday) - datetime.timedelta(days=7)


def nth_weekday_of_year(year, weekday, occurrence):
    d = datetime.date(year, 1, 1)
    while d.weekday() != weekday:
        d += datetime.timedelta(days=1)
    d += datetime.timedelta(weeks=occurrence - 1)
    return d


def last_weekday_of_year(year, weekday):
    d = datetime.date(year, 12, 31)
    while d.weekday() != weekday:
        d -= datetime.timedelta(days=1)
    return d


def penultimate_weekday_of_year(year, weekday):
    return last_weekday_of_year(year, weekday) - datetime.timedelta(days=7)


def quarter_start_month(quarter):
    return (quarter - 1) * 3 + 1


def get_holiday_date(phrase):
    current_year = get_reference_date().get_year()
    year_offset = 0
    relative_direction = None
    original_phrase = phrase.strip()

    if original_phrase in {"bank holiday", "next bank holiday"}:
        reference_date = get_reference_date().to_datetime().date()
        if original_phrase == "next bank holiday":
            reference_date += datetime.timedelta(days=1)

        for search_year in range(reference_date.year, reference_date.year + 3):
            for holiday in get_uk_bank_holidays(search_year):
                if holiday >= reference_date:
                    d = get_reference_date()
                    d.set_fullyear(holiday.year)
                    d.set_month(holiday.month - 1)
                    d.set_date(holiday.day)
                    return d
        return None

    if phrase.endswith(" next year"):
        year_offset = 1
        phrase = phrase[: -len(" next year")]
    elif phrase.endswith(" last year"):
        year_offset = -1
        phrase = phrase[: -len(" last year")]
    elif phrase.endswith(" this year"):
        phrase = phrase[: -len(" this year")]
    else:
        explicit_year_match = re.fullmatch(r"(?P<name>.+?)\s+(?P<year>\d{4})", phrase)
        if explicit_year_match is not None:
            year = int(explicit_year_match.group("year"))
            phrase = explicit_year_match.group("name")
            year_offset = year - current_year

    if phrase.startswith("next "):
        relative_direction = "next"
        phrase = phrase[len("next ") :]
    elif phrase.startswith("last "):
        relative_direction = "last"
        phrase = phrase[len("last ") :]

    holiday_key = phrase.strip()
    year = current_year + year_offset

    resolver = get_registered_holiday_resolver(holiday_key)
    if resolver is None:
        return None

    if relative_direction is not None and year_offset == 0:
        reference_date = get_reference_date().to_datetime().date()
        if relative_direction == "next":
            holiday = None
            for search_year in range(current_year, current_year + 12):
                candidate = resolver(search_year)
                if candidate is None:
                    continue
                if candidate > reference_date:
                    holiday = candidate
                    break
        else:
            holiday = None
            for search_year in range(current_year, current_year - 12, -1):
                candidate = resolver(search_year)
                if candidate is None:
                    continue
                if candidate < reference_date:
                    holiday = candidate
                    break
    else:
        holiday = resolver(year)

    if holiday is None:
        return None

    d = get_reference_date()
    d.set_fullyear(holiday.year)
    d.set_month(holiday.month - 1)
    d.set_date(holiday.day)
    return d


def observe_weekday_holiday(date_value, occupied=None):
    occupied = occupied or set()
    observed = date_value

    if observed.weekday() == 5:
        observed += datetime.timedelta(days=2)
    elif observed.weekday() == 6:
        observed += datetime.timedelta(days=1)

    while observed in occupied:
        observed += datetime.timedelta(days=1)

    return observed


def get_uk_bank_holidays(year):
    holidays = []

    new_year = observe_weekday_holiday(datetime.date(year, 1, 1))
    holidays.append(new_year)

    easter_sunday = easter(year)
    holidays.append(easter_sunday - datetime.timedelta(days=2))  # Good Friday
    holidays.append(easter_sunday + datetime.timedelta(days=1))  # Easter Monday
    holidays.append(nth_weekday_of_month(year, 5, 0, 1))  # Early May bank holiday
    holidays.append(last_weekday_of_month(year, 5, 0))  # Spring bank holiday
    holidays.append(last_weekday_of_month(year, 8, 0))  # Summer bank holiday

    christmas = observe_weekday_holiday(datetime.date(year, 12, 25))
    boxing = observe_weekday_holiday(datetime.date(year, 12, 26), occupied={christmas})
    holidays.append(christmas)
    holidays.append(boxing)

    return sorted(holidays)


def resolve_period_year_month(period):
    from stringtime.parse_anchors import resolve_period_year_month as _impl

    return _impl(period)


def resolve_year_phrase(period):
    from stringtime.parse_anchors import resolve_year_phrase as _impl

    return _impl(period)


def resolve_quarter_year(quarter_phrase):
    from stringtime.parse_anchors import resolve_quarter_year as _impl

    return _impl(quarter_phrase)


def get_ordinal_weekday_date(phrase):
    from stringtime.parse_anchors import get_ordinal_weekday_date as _impl

    return _impl(phrase)


def get_weekday_occurrence_period_date(phrase):
    from stringtime.parse_anchors import get_weekday_occurrence_period_date as _impl

    return _impl(phrase)


def get_ordinal_weekday_anchor_date(phrase, *args, timezone_aware=False, **kwargs):
    pattern = (
        rf"(?:the\s+)?(?P<occurrence>{ORDINAL_OCCURRENCE_PATTERN})\s+"
        rf"(?P<weekday>{WEEKDAY_RE})\s+"
        r"(?P<direction>before|after)\s+(?P<anchor>.+)"
    )
    match = re.fullmatch(pattern, phrase)
    if match is None:
        return None

    occurrence = match.group("occurrence")
    weekday_name = match.group("weekday")
    direction = match.group("direction")
    anchor_text = match.group("anchor").strip()

    anchor_date = parse_anchor_like_text(
        anchor_text,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if anchor_date is None:
        return None

    occurrence_count = 1 if occurrence == "last" else 2 if occurrence == "penultimate" else ORDINAL_OCCURRENCE_MAP[occurrence]
    weekday = WEEKDAY_INDEX[weekday_name]

    anchor_dt = anchor_date.to_datetime()
    current = anchor_dt.date()
    found = None
    count = 0
    step = -1 if direction == "before" else 1

    while count < occurrence_count:
        current += datetime.timedelta(days=step)
        if current.weekday() == weekday:
            count += 1
            found = current

    if found is None:
        return None

    d = clone_date(anchor_date)
    d.set_fullyear(found.year)
    d.set_month(found.month - 1)
    d.set_date(found.day)
    return d


def get_weekday_in_month_date(phrase):
    match = re.fullmatch(
        rf"(?:the\s+)?(?P<weekday>{WEEKDAY_PATTERN})\s+in\s+(?P<period>.+)",
        phrase,
    )
    if match is None:
        return None

    normalized_period = replace_short_words(match.group("period"))
    resolved = resolve_period_year_month(normalized_period)
    if resolved is None:
        return None

    year, month = resolved
    target_weekday = WEEKDAY_INDEX[match.group("weekday")]

    def first_matching_weekday(target_year):
        d = build_calendar_anchor_date(target_year, month, 1)
        while d.to_datetime().weekday() != target_weekday:
            d.set_date(d.get_date() + 1)
        return d

    d = first_matching_weekday(year)
    if normalized_period in MONTH_INDEX and d.to_datetime().replace(
        tzinfo=None
    ) < get_reference_date().to_datetime().replace(
        tzinfo=None
    ):
        d = first_matching_weekday(year + 1)
    return d


def get_weekday_anchor_date(phrase, *args, timezone_aware=False, **kwargs):
    match = re.fullmatch(
        rf"(?:the\s+)?(?P<weekday>{WEEKDAY_PATTERN})\s+"
        r"(?P<direction>before|after)\s+(?P<anchor>.+)",
        phrase,
    )
    if match is None:
        return None

    weekday = WEEKDAY_INDEX[match.group("weekday")]

    anchor_date = parse_anchor_like_text(
        match.group("anchor").strip(),
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if anchor_date is None:
        return None

    current = anchor_date.to_datetime().date()
    step = -1 if match.group("direction") == "before" else 1

    while True:
        current += datetime.timedelta(days=step)
        if current.weekday() == weekday:
            break

    d = clone_date(anchor_date)
    d.set_fullyear(current.year)
    d.set_month(current.month - 1)
    d.set_date(current.day)
    return d


def get_recurring_weekday_date(phrase, *args, timezone_aware=False, **kwargs):
    from stringtime.recurrence import get_recurring_weekday_date as _impl

    return _impl(phrase, *args, timezone_aware=timezone_aware, **kwargs)


def get_recurring_schedule_date(phrase, *args, timezone_aware=False, **kwargs):
    from stringtime.recurrence import get_recurring_schedule_date as _impl

    return _impl(phrase, *args, timezone_aware=timezone_aware, **kwargs)


def get_ordinal_month_year_date(phrase):
    from stringtime.parse_anchors import get_ordinal_month_year_date as _impl

    return _impl(phrase)


def get_quarter_phrase_date(phrase):
    from stringtime.parse_anchors import get_quarter_phrase_date as _impl

    return _impl(phrase)


def get_weekday_occurrence_period_phrase_date(phrase):
    from stringtime.parse_anchors import get_weekday_occurrence_period_phrase_date as _impl

    return _impl(phrase)


def get_fiscal_anchor_date(phrase):
    if phrase.startswith("the "):
        phrase = phrase[4:]

    reference = get_reference_date()
    reference_dt = reference.to_datetime().replace(tzinfo=None)

    match = re.fullmatch(
        r"(?:(?P<relation>next|last|this)\s+)?fiscal\s+q(?P<quarter>[1-4])(?:\s+(?P<year>\d{4}))?",
        phrase,
    )
    if match is not None:
        quarter = int(match.group("quarter"))
        explicit_year = match.group("year")
        if explicit_year is not None:
            year = int(explicit_year)
        else:
            year = reference.get_year()
            quarter_start = datetime.datetime(year, quarter_start_month(quarter), 1)
            if match.group("relation") == "next":
                if quarter_start <= reference_dt:
                    year += 1
            elif match.group("relation") == "last":
                if quarter_start >= reference_dt:
                    year -= 1
            elif match.group("relation") is None and quarter_start < reference_dt:
                year += 1

        d = clone_date(reference)
        d.set_fullyear(year)
        d.set_month(quarter_start_month(quarter) - 1)
        d.set_date(1)
        return d

    match = re.fullmatch(
        r"(?:(?P<relation>next|last|this)\s+)?fiscal\s+year\s+(?P<edge>start|end)|(?P<alt_edge>start|end)\s+of\s+(?:(?P<alt_relation>next|last|this)\s+)?fiscal\s+year",
        phrase,
    )
    if match is not None:
        relation = match.group("relation") or match.group("alt_relation") or "this"
        edge = match.group("edge") or match.group("alt_edge")
        year = reference.get_year()
        if relation == "next":
            year += 1
        elif relation == "last":
            year -= 1

        d = clone_date(reference)
        d.set_fullyear(year)
        if edge == "start":
            d.set_month(0)
            d.set_date(1)
        else:
            d.set_month(11)
            d.set_date(31)
        return d

    if phrase == "quarter close":
        month = reference.get_month() + 1
        quarter = ((month - 1) // 3) + 1
        year = reference.get_year()
        end_month = quarter_start_month(quarter) + 2
        d = clone_date(reference)
        d.set_fullyear(year)
        d.set_month(end_month - 1)
        d.set_date(stDate.get_month_length(end_month, year))
        return d

    if phrase == "month close":
        year = reference.get_year()
        month = reference.get_month() + 1
        d = clone_date(reference)
        d.set_fullyear(year)
        d.set_month(month - 1)
        d.set_date(stDate.get_month_length(month, year))
        return d

    return None


def get_season_anchor_date(phrase):
    if phrase.startswith("the "):
        phrase = phrase[4:]

    reference = get_reference_date()
    reference_dt = reference.to_datetime().replace(tzinfo=None)
    season_months = {
        "spring": (3, 5),
        "summer": (6, 8),
        "autumn": (9, 11),
        "fall": (9, 11),
        "winter": (12, 2),
    }

    match = re.fullmatch(
        r"(?:(?P<edge>start|mid|middle|end)\s+of\s+|(?P<bare_mid>mid)\s+)?(?:(?P<relation>next|last|this)\s+)?(?P<season>spring|summer|autumn|fall|winter)(?:\s+(?P<year>\d{4}))?",
        phrase,
    )
    if match is None:
        return None

    season = match.group("season")
    edge = match.group("edge") or match.group("bare_mid") or "start"
    relation = match.group("relation")
    explicit_year = match.group("year")
    start_month, end_month = season_months[season]

    def season_start_for(year):
        return datetime.datetime(year, start_month, 1)

    if explicit_year is not None:
        start_year = int(explicit_year)
    else:
        start_year = reference.get_year()
        current_start = season_start_for(start_year)
        if season == "winter" and reference.get_month() + 1 < 3:
            current_start = season_start_for(start_year - 1)

        if relation == "next":
            if current_start <= reference_dt:
                start_year = current_start.year + 1
            else:
                start_year = current_start.year
        elif relation == "last":
            if current_start >= reference_dt:
                start_year = current_start.year - 1
            else:
                start_year = current_start.year
        elif relation == "this":
            start_year = current_start.year
        else:
            if current_start < reference_dt:
                start_year = current_start.year + 1
            else:
                start_year = current_start.year

    d = clone_date(reference)
    d.set_fullyear(start_year)
    d.set_month(start_month - 1)
    d.set_date(1)

    if edge in {"mid", "middle"}:
        mid_month = start_month + 1 if season != "winter" else 1
        mid_year = (
            start_year if season != "winter" or mid_month != 1 else start_year + 1
        )
        d.set_fullyear(mid_year)
        d.set_month(mid_month - 1)
        d.set_date(15)
    elif edge == "end":
        if season == "winter":
            end_year = start_year + 1
            d.set_fullyear(end_year)
            d.set_month(1)
            d.set_date(stDate.get_month_length(2, end_year))
        else:
            d.set_month(end_month - 1)
            d.set_date(stDate.get_month_length(end_month, start_year))

    return d


def get_solstice_equinox_date(phrase):
    if phrase.startswith("the "):
        phrase = phrase[4:]

    reference = get_reference_date()
    reference_dt = reference.to_datetime().replace(tzinfo=None)
    event_lookup = {
        "spring equinox": (3, 20),
        "vernal equinox": (3, 20),
        "summer solstice": (6, 21),
        "autumn equinox": (9, 22),
        "fall equinox": (9, 22),
        "autumnal equinox": (9, 22),
        "winter solstice": (12, 21),
    }

    match = re.fullmatch(
        r"(?:(?P<relation>next|last|this)\s+)?(?P<event>spring equinox|vernal equinox|summer solstice|autumn equinox|fall equinox|autumnal equinox|winter solstice)(?:\s+(?P<year>\d{4}))?",
        phrase,
    )
    if match is None:
        return None

    month, day = event_lookup[match.group("event")]
    if match.group("year") is not None:
        year = int(match.group("year"))
    else:
        year = reference.get_year()
        candidate = datetime.datetime(year, month, day, 12, 0, 0)
        relation = match.group("relation")
        if relation == "next":
            if candidate <= reference_dt:
                year += 1
        elif relation == "last":
            if candidate >= reference_dt:
                year -= 1
        elif relation is None and candidate < reference_dt:
            year += 1

    d = clone_date(reference)
    d.set_fullyear(year)
    d.set_month(month - 1)
    d.set_date(day)
    d.set_hours(12)
    d.set_minutes(0)
    d.set_seconds(0)
    return d


def get_recurring_week_anchor_date(phrase):
    reference = get_reference_date()
    weekday = reference.to_datetime().weekday()

    if phrase in {"start of week", "start of the week", "this week start"}:
        d = clone_date(reference)
        d.set_date(d.get_date() - weekday)
        return d

    if phrase in {"end of week", "end of the week"}:
        d = clone_date(reference)
        d.set_date(d.get_date() + (6 - weekday))
        return d

    if phrase == "midweek":
        d = clone_date(reference)
        offset = 2 - weekday
        if offset < 0:
            offset += 7
        d.set_date(d.get_date() + offset)
        return d

    if phrase in {"this weekend", "next weekend"}:
        d = clone_date(reference)
        target_offset = (5 - weekday) % 7
        if phrase == "next weekend":
            target_offset += 7 if target_offset == 0 else 7
        d.set_date(d.get_date() + target_offset)
        return d

    return None


def get_named_lunar_event_date(phrase):
    if phrase.startswith("the "):
        phrase = phrase[4:]

    reference = get_reference_date()
    reference_dt = reference.to_datetime().replace(tzinfo=None)
    monthly_named_moons = {
        "wolf moon": 1,
        "strawberry moon": 6,
        "hunter's moon": 10,
        "hunters moon": 10,
    }

    match = re.fullmatch(
        r"(?:(?P<relation>next|last)\s+)?(?P<event>wolf moon|strawberry moon|hunter's moon|hunters moon|supermoon|blood moon|micromoon)",
        phrase,
    )
    if match is None:
        return None

    event = match.group("event")
    relation = match.group("relation") or "next"

    if event in {"supermoon", "blood moon", "micromoon"}:
        moment = get_named_moon_datetime(reference_dt, "full moon", relation=relation)
        return date_from_datetime(moment) if moment is not None else None

    target_month = monthly_named_moons[event]
    year = reference.get_year()
    candidates = []
    for search_year in range(year - 2, year + 4):
        moons = get_moon_phase_datetimes_for_month(
            search_year, target_month, "full moon"
        )
        candidates.extend(moons[:1])

    if relation == "last":
        previous = [candidate for candidate in candidates if candidate < reference_dt]
        return date_from_datetime(max(previous)) if previous else None

    upcoming = [candidate for candidate in candidates if candidate > reference_dt]
    return date_from_datetime(min(upcoming)) if upcoming else None


def get_relative_weekday_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    match = re.fullmatch(
        rf"(?:the\s+)?(?P<weekday>{WEEKDAY_RE})\s+(?P<relation>after next|before last|gone|past)",
        phrase,
    )
    if match is None:
        return None

    weekday = match.group("weekday")
    relation = match.group("relation")
    anchor = "next" if relation == "after next" else "last"

    d = parse_natural_date_strict(
        f"{anchor} {weekday}",
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if d is None:
        return None

    if relation == "after next":
        d.set_date(d.get_date() + 7)
    elif relation == "before last":
        d.set_date(d.get_date() - 7)
    return d


def get_weekday_and_date_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    match = re.fullmatch(
        rf"(?:the\s+)?(?P<weekday>{WEEKDAY_RE})\s+and\s+(?P<date>.+)",
        phrase,
    )
    if match is None:
        return None

    date_part = parse_natural_date_strict(
        match.group("date"),
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if date_part is None:
        return None

    if date_part.to_datetime().weekday() != WEEKDAY_INDEX[match.group("weekday")]:
        return None
    return date_part


def get_counted_weekday_phrase_date(phrase):
    match = re.fullmatch(
        r"(?:(?:in)\s+)?(?P<count>\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
        rf"(?P<weekday>{WEEKDAY_OR_PLURAL_RE})\s+"
        r"(?:(?:from\s+now)|hence|ago|time)",
        phrase,
    )
    if match is None:
        return None

    count = parse_offset_number(match.group("count"))
    if count is None or count < 1:
        return None

    weekday_name = match.group("weekday")
    weekday_name = normalize_weekday_name(weekday_name)
    if weekday_name is None:
        return None

    weekday = WEEKDAY_INDEX[weekday_name]

    reference = get_reference_date()
    if "ago" in phrase:
        day_delta = (reference.to_datetime().weekday() - weekday) % 7
        if day_delta == 0:
            day_delta = 7
        day_delta += 7 * (count - 1)
        day_delta *= -1
    else:
        day_delta = (weekday - reference.to_datetime().weekday()) % 7
        if day_delta == 0:
            day_delta = 7
        day_delta += 7 * (count - 1)

    d = clone_date(reference)
    d._date = d.to_datetime() + datetime.timedelta(days=day_delta)
    return d


def get_counted_holiday_phrase_date(phrase):
    match = re.fullmatch(
        r"(?:(?:in)\s+)?(?P<count>\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
        r"(?P<holiday>[a-z' -]+?)\s+"
        r"(?:(?:from\s+now)|hence|ago|time)",
        phrase,
    )
    if match is None:
        return None

    count = parse_offset_number(match.group("count"))
    if count is None or count < 1:
        return None

    raw_holiday = match.group("holiday").strip()
    holiday_candidates = [raw_holiday]
    if raw_holiday.endswith("ies"):
        holiday_candidates.append(raw_holiday[:-3] + "y")
    if raw_holiday.endswith("es"):
        holiday_candidates.append(raw_holiday[:-2])
    if raw_holiday.endswith("s"):
        holiday_candidates.append(raw_holiday[:-1])

    resolver = None
    for candidate in holiday_candidates:
        resolver = get_registered_holiday_resolver(candidate)
        if resolver is not None:
            break
    if resolver is None:
        return None

    reference_date = get_reference_date().to_datetime().date()
    matches = []
    if "ago" in phrase:
        year_range = range(reference_date.year, reference_date.year - 40, -1)
        comparator = lambda candidate: candidate <= reference_date
    else:
        year_range = range(reference_date.year, reference_date.year + 40)
        comparator = lambda candidate: candidate >= reference_date

    for year in year_range:
        candidate = resolver(year)
        if candidate is None or not comparator(candidate):
            continue
        matches.append(candidate)
        if len(matches) >= count:
            break

    if len(matches) < count:
        return None

    target = matches[count - 1]
    d = get_reference_date()
    d.set_fullyear(target.year)
    d.set_month(target.month - 1)
    d.set_date(target.day)
    return d


def get_counted_month_phrase_date(phrase):
    match = re.fullmatch(
        r"(?:(?:in)\s+)?(?P<count>\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
        rf"(?P<month>{'|'.join(sorted(MONTH_ALL_SET, key=len, reverse=True))})\s+"
        r"(?:(?:from\s+now)|hence|ago|time)",
        phrase,
    )
    if match is None:
        return None

    count = parse_offset_number(match.group("count"))
    if count is None or count < 1:
        return None

    month_name = normalize_month_name(match.group("month"))
    if month_name is None:
        return None

    target_month = MONTH_INDEX[month_name]
    reference = get_reference_date()
    reference_dt = reference.to_datetime().replace(tzinfo=None)

    if "ago" in phrase:
        year_range = range(reference_dt.year, reference_dt.year - 40, -1)
        comparator = lambda year: (year, target_month) < (
            reference_dt.year,
            reference_dt.month,
        )
    else:
        year_range = range(reference_dt.year, reference_dt.year + 40)
        comparator = lambda year: (year, target_month) > (
            reference_dt.year,
            reference_dt.month,
        )

    matches = []
    for year in year_range:
        if not comparator(year):
            continue
        matches.append(year)
        if len(matches) >= count:
            break

    if len(matches) < count:
        return None

    target_year = matches[count - 1]
    d = clone_date(reference)
    d.set_date(1)
    d.set_fullyear(target_year)
    d.set_month(target_month - 1)
    return d


def get_relative_period_phrase_date(phrase):
    from stringtime.parse_anchors import get_relative_period_phrase_date as _impl

    return _impl(phrase)


def get_counted_weekday_anchor_date(phrase, *args, timezone_aware=False, **kwargs):
    match = re.fullmatch(
        r"(?P<count>\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
        r"(?P<weekday>mondays?|tuesdays?|wednesdays?|thursdays?|fridays?|saturdays?|sundays?)\s+"
        r"(?P<direction>after|before)\s+(?P<anchor>.+)",
        phrase,
    )
    if match is None:
        return None

    count = parse_offset_number(match.group("count"))
    if count is None or count < 1:
        return None

    weekday_name = normalize_weekday_name(match.group("weekday"))
    if weekday_name is None:
        return None

    weekday = WEEKDAY_INDEX[weekday_name]

    anchor_date = parse_anchor_like_text(
        match.group("anchor"),
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if anchor_date is None:
        return None

    current = anchor_date.to_datetime().date()
    step = 1 if match.group("direction") == "after" else -1
    found = None

    while count > 0:
        current += datetime.timedelta(days=step)
        if current.weekday() == weekday:
            count -= 1
            found = current

    if found is None:
        return None

    d = clone_date(anchor_date)
    d.set_fullyear(found.year)
    d.set_month(found.month - 1)
    d.set_date(found.day)
    return d


def get_relative_month_day_phrase_date(phrase):
    from stringtime.parse_anchors import get_relative_month_day_phrase_date as _impl

    return _impl(phrase)


def get_boundary_phrase_date(phrase):
    from stringtime.parse_anchors import get_boundary_phrase_date as _impl

    return _impl(phrase)


def get_month_anchor_date(phrase):
    from stringtime.parse_anchors import get_month_anchor_date as _impl

    return _impl(phrase)


def get_week_of_month_anchor_date(phrase):
    from stringtime.parse_anchors import get_week_of_month_anchor_date as _impl

    return _impl(phrase)


def get_leap_year_anchor_date(phrase):
    from stringtime.parse_anchors import get_leap_year_anchor_date as _impl

    return _impl(phrase)


def get_leap_year_offset_date(phrase):
    match = re.fullmatch(
        r"(?P<count>\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|several)\s+leap\s+years?\s+(?P<direction>ago|from now|hence)",
        phrase,
    )
    if match is None:
        return None

    count = parse_offset_number(match.group("count"))
    if count is None:
        return None

    reference = get_reference_date()
    year = reference.get_year()

    if match.group("direction") == "ago":
        candidate = year - 1
        step = -1
    else:
        candidate = year + 1
        step = 1

    leap_years = []
    while len(leap_years) < count:
        if calendar.isleap(candidate):
            leap_years.append(candidate)
        candidate += step

    target_year = leap_years[-1]
    d = clone_date(reference)
    d.set_date(1)
    d.set_fullyear(target_year)
    d.set_month(0)
    return d


def get_day_of_year_phrase_date(phrase):
    match = re.fullmatch(
        r"(?:the\s+)?(?P<day>\d+(?:st|nd|rd|th)|hundredth)\s+day\s+of\s+(?:the\s+)?(?P<period>year|the year|this year|next year|last year|\d{4})",
        phrase,
    )
    if match is None:
        return None

    raw_day = match.group("day")
    if raw_day == "hundredth":
        day_number = 100
    else:
        ordinal_match = re.fullmatch(r"(\d+)(?:st|nd|rd|th)", raw_day)
        day_number = (
            int(ordinal_match.group(1)) if ordinal_match is not None else int(raw_day)
        )

    year = resolve_year_phrase(match.group("period"))
    if year is None:
        return None

    max_day = 366 if calendar.isleap(year) else 365
    if day_number < 1 or day_number > max_day:
        return None

    target = datetime.date(year, 1, 1) + datetime.timedelta(days=day_number - 1)
    d = get_reference_date()
    d.set_fullyear(target.year)
    d.set_month(target.month - 1)
    d.set_date(target.day)
    return d


def get_ordinal_time_coordinate_date(phrase, *args, timezone_aware=False, **kwargs):
    ordinal_lookup = ORDINAL_DAY_MAP
    ordinal_pattern = DATE_ORDINAL_PATTERN

    def parse_ordinal(raw_value):
        match = re.fullmatch(r"(\d+)(?:st|nd|rd|th)", raw_value)
        if match is not None:
            return int(match.group(1))
        return ordinal_lookup.get(raw_value)

    match = re.fullmatch(
        rf"(?:the\s+)?(?P<second>{ordinal_pattern})\s+second\s+of\s+(?:the\s+)?(?P<minute>{ordinal_pattern})\s+minute\s+on\s+(?P<anchor>.+)",
        phrase,
    )
    if match is not None:
        second = parse_ordinal(match.group("second"))
        minute = parse_ordinal(match.group("minute"))
        if second is None or minute is None:
            return None
        if not (1 <= second <= 59 and 1 <= minute <= 59):
            return None

        anchor_date = resolve_nested_anchor_date_text(
            match.group("anchor"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if anchor_date is None:
            return None

        d = clone_date(anchor_date)
        d.set_minutes(minute)
        d.set_seconds(second)
        return d

    match = re.fullmatch(
        rf"(?:the\s+)?(?P<minute>{ordinal_pattern})\s+minute\s+on\s+(?P<anchor>.+)",
        phrase,
    )
    if match is not None:
        minute = parse_ordinal(match.group("minute"))
        if minute is None or not (1 <= minute <= 59):
            return None

        anchor_date = resolve_nested_anchor_date_text(
            match.group("anchor"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if anchor_date is None:
            return None

        d = clone_date(anchor_date)
        d.set_minutes(minute)
        d.set_seconds(0)
        return d

    match = re.fullmatch(
        rf"(?:the\s+)?(?P<second>{ordinal_pattern})\s+second\s+of\s+(?:the\s+)?(?P<minute>{ordinal_pattern})\s+minute",
        phrase,
    )
    if match is not None:
        second = parse_ordinal(match.group("second"))
        minute = parse_ordinal(match.group("minute"))
        if second is None or minute is None:
            return None
        if not (1 <= second <= 59 and 1 <= minute <= 59):
            return None

        d = get_reference_date()
        d.set_minutes(minute)
        d.set_seconds(second)
        return d

    match = re.fullmatch(rf"(?:the\s+)?(?P<hour>{ordinal_pattern})\s+hour", phrase)
    if match is None:
        return None

    hour = parse_ordinal(match.group("hour"))
    if hour is None or not (1 <= hour <= 23):
        return None

    d = get_reference_date()
    d.set_hours(hour)
    d.set_minutes(0)
    d.set_seconds(0)
    return d


def get_part_of_day_time(part):
    return {
        "breakfast": (8, 0),
        "breakfasttime": (8, 0),
        "brunch": (11, 0),
        "lunch": (12, 30),
        "morning": (9, 0),
        "late morning": (11, 0),
        "early in the morning": (6, 0),
        "early morning": (6, 0),
        "mid-morning": (10, 0),
        "mid morning": (10, 0),
        "afternoon": (15, 0),
        "late afternoon": (16, 30),
        "tea": (17, 0),
        "dinner": (18, 0),
        "evening": (19, 0),
        "night": (21, 0),
        "lunchtime": (12, 30),
        "dinnertime": (18, 0),
        "teatime": (17, 0),
    }.get(part)


def get_solar_event_time_for_date(date_obj, event):
    # Approximate solar events by month in local civil time.
    monthly_times = {
        1: {
            "dawn": (7, 30),
            "sunrise": (8, 5),
            "sunset": (16, 25),
            "dusk": (17, 0),
            "twilight": (17, 0),
        },
        2: {
            "dawn": (6, 45),
            "sunrise": (7, 20),
            "sunset": (17, 15),
            "dusk": (17, 50),
            "twilight": (17, 50),
        },
        3: {
            "dawn": (5, 45),
            "sunrise": (6, 20),
            "sunset": (18, 5),
            "dusk": (18, 40),
            "twilight": (18, 40),
        },
        4: {
            "dawn": (4, 45),
            "sunrise": (5, 25),
            "sunset": (19, 0),
            "dusk": (19, 35),
            "twilight": (19, 35),
        },
        5: {
            "dawn": (4, 0),
            "sunrise": (4, 45),
            "sunset": (19, 45),
            "dusk": (20, 20),
            "twilight": (20, 20),
        },
        6: {
            "dawn": (3, 30),
            "sunrise": (4, 15),
            "sunset": (20, 15),
            "dusk": (20, 50),
            "twilight": (20, 50),
        },
        7: {
            "dawn": (3, 45),
            "sunrise": (4, 30),
            "sunset": (20, 10),
            "dusk": (20, 45),
            "twilight": (20, 45),
        },
        8: {
            "dawn": (4, 30),
            "sunrise": (5, 15),
            "sunset": (19, 20),
            "dusk": (19, 55),
            "twilight": (19, 55),
        },
        9: {
            "dawn": (5, 20),
            "sunrise": (6, 0),
            "sunset": (18, 20),
            "dusk": (18, 55),
            "twilight": (18, 55),
        },
        10: {
            "dawn": (6, 10),
            "sunrise": (6, 45),
            "sunset": (17, 10),
            "dusk": (17, 45),
            "twilight": (17, 45),
        },
        11: {
            "dawn": (6, 55),
            "sunrise": (7, 30),
            "sunset": (16, 15),
            "dusk": (16, 50),
            "twilight": (16, 50),
        },
        12: {
            "dawn": (7, 25),
            "sunrise": (8, 0),
            "sunset": (15, 55),
            "dusk": (16, 30),
            "twilight": (16, 30),
        },
    }
    return monthly_times.get(date_obj.get_month() + 1, {}).get(event)


def set_date_time(date_obj, hour, minute=0, second=0):
    d = clone_date(date_obj)
    d.set_hours(hour)
    d.set_minutes(minute)
    d.set_seconds(second)
    return d


def build_calendar_anchor_date(
    year,
    month,
    day,
    *,
    base_date=None,
    hour=None,
    minute=None,
    second=None,
):
    d = clone_date(base_date or get_reference_date())
    d.set_date(1)
    d.set_fullyear(year)
    d.set_month(month - 1)
    d.set_date(day)
    if hour is not None:
        d.set_hours(hour)
    if minute is not None:
        d.set_minutes(minute)
    if second is not None:
        d.set_seconds(second)
    return d


def normalize_meridiem_hour(hour, meridiem):
    hour = int(hour) % 24
    if meridiem is None:
        return hour
    meridiem = meridiem.strip().lower()
    if meridiem == "pm" and hour < 12:
        hour += 12
    if meridiem == "am" and hour == 12:
        hour = 0
    return hour


def build_structured_time_date(hour, minute=0, second=0, meridiem=None):
    d = get_reference_date()
    d.set_hours(normalize_meridiem_hour(hour, meridiem))
    d.set_minutes(minute)
    d.set_seconds(second)
    return d


def date_from_datetime(dt):
    d = stDate()
    d._date = dt.replace(microsecond=0)
    return d


def get_moon_phase_datetime(reference_dt, phase_name, relation="next"):
    phase_fractions = {
        "new moon": 0.0,
        "first quarter moon": 0.25,
        "full moon": 0.5,
        "last quarter moon": 0.75,
    }
    phase_fraction = phase_fractions[phase_name]
    period_seconds = SYNODIC_MONTH_DAYS * 24 * 60 * 60
    cycles = (reference_dt - MOON_PHASE_EPOCH).total_seconds() / period_seconds
    phase_cycles = cycles - phase_fraction

    if relation == "last":
        index = math.ceil(phase_cycles) - 1
        moment = MOON_PHASE_EPOCH + datetime.timedelta(
            seconds=(index + phase_fraction) * period_seconds
        )
        while moment >= reference_dt:
            index -= 1
            moment = MOON_PHASE_EPOCH + datetime.timedelta(
                seconds=(index + phase_fraction) * period_seconds
            )
        return moment

    index = math.floor(phase_cycles) + 1
    moment = MOON_PHASE_EPOCH + datetime.timedelta(
        seconds=(index + phase_fraction) * period_seconds
    )
    while moment <= reference_dt:
        index += 1
        moment = MOON_PHASE_EPOCH + datetime.timedelta(
            seconds=(index + phase_fraction) * period_seconds
        )
    return moment


def get_full_moons_for_month(year, month):
    start = datetime.datetime(year, month, 1)
    if month == 12:
        end = datetime.datetime(year + 1, 1, 1)
    else:
        end = datetime.datetime(year, month + 1, 1)

    candidates = []
    probe = start - datetime.timedelta(days=40)
    current = get_moon_phase_datetime(probe, "full moon", relation="next")
    while current < end + datetime.timedelta(days=40):
        if start <= current < end:
            candidates.append(current)
        current = current + datetime.timedelta(days=SYNODIC_MONTH_DAYS)

    return sorted(candidates)


def get_moon_phase_datetimes_for_month(year, month, phase_name):
    start = datetime.datetime(year, month, 1)
    if month == 12:
        end = datetime.datetime(year + 1, 1, 1)
    else:
        end = datetime.datetime(year, month + 1, 1)

    if phase_name == "blue moon":
        return [
            candidate
            for candidate in get_blue_moon_datetimes_for_year(year)
            if candidate.month == month
        ]

    if phase_name == "harvest moon":
        harvest = get_harvest_moon_datetime(year)
        if harvest.year == year and harvest.month == month:
            return [harvest]
        return []

    probe = start - datetime.timedelta(days=40)
    current = get_moon_phase_datetime(probe, phase_name, relation="next")
    candidates = []
    while current < end + datetime.timedelta(days=40):
        if start <= current < end:
            candidates.append(current)
        current = current + datetime.timedelta(days=SYNODIC_MONTH_DAYS)

    return sorted(candidates)


def get_harvest_moon_datetime(year):
    target = datetime.datetime(year, 9, 22, 12, 0, 0)
    candidates = []
    current = get_moon_phase_datetime(target - datetime.timedelta(days=45), "full moon")
    while current <= target + datetime.timedelta(days=45):
        candidates.append(current)
        current = current + datetime.timedelta(days=SYNODIC_MONTH_DAYS)
    return min(candidates, key=lambda value: abs(value - target))


def get_blue_moon_datetimes_for_year(year):
    blue_moons = []
    for month in range(1, 13):
        full_moons = get_full_moons_for_month(year, month)
        if len(full_moons) >= 2:
            blue_moons.append(full_moons[1])
    return blue_moons


def get_named_moon_datetime(reference_dt, phase_name, relation="next"):
    comparison_reference = reference_dt.replace(tzinfo=None)

    if phase_name in {
        "new moon",
        "first quarter moon",
        "full moon",
        "last quarter moon",
    }:
        return get_moon_phase_datetime(reference_dt, phase_name, relation=relation)

    if phase_name == "harvest moon":
        years = range(reference_dt.year - 12, reference_dt.year + 12)
        candidates = [get_harvest_moon_datetime(year) for year in years]
    elif phase_name == "blue moon":
        candidates = []
        for year in range(reference_dt.year - 12, reference_dt.year + 12):
            candidates.extend(get_blue_moon_datetimes_for_year(year))
    else:
        return None

    if relation == "last":
        previous = [
            candidate
            for candidate in candidates
            if candidate.replace(tzinfo=None) < comparison_reference
        ]
        return max(previous) if previous else None

    upcoming = [
        candidate
        for candidate in candidates
        if candidate.replace(tzinfo=None) > comparison_reference
    ]
    return min(upcoming) if upcoming else None


def get_month_name_number(raw_month):
    return MONTH_INDEX.get(raw_month)


def get_moon_phase_phrase_date(phrase):
    reference = get_reference_date()
    phrase = re.sub(r"^on\s+", "", phrase)
    if phrase in {"the full moon before last", "full moon before last"}:
        first = get_named_moon_datetime(
            reference.to_datetime(), "full moon", relation="last"
        )
        if first is None:
            return None
        second = get_named_moon_datetime(first, "full moon", relation="last")
        return date_from_datetime(second) if second is not None else None
    constrained_match = re.fullmatch(
        rf"(?:the\s+)?(?:(?P<which>first|last)\s+)?(?P<phase>new moon|first quarter moon|full moon|last quarter moon|harvest moon|blue moon)\s+in\s+(?P<month>{MONTH_RE})\s+(?P<year>\d{{4}})",
        phrase,
    )
    if constrained_match is not None:
        phase_name = constrained_match.group("phase")
        month = get_month_name_number(constrained_match.group("month"))
        year = int(constrained_match.group("year"))
        candidates = get_moon_phase_datetimes_for_month(year, month, phase_name)
        if not candidates:
            return None
        which = constrained_match.group("which") or "first"
        moment = candidates[-1] if which == "last" else candidates[0]
        return date_from_datetime(moment)

    constrained_reference_match = re.fullmatch(
        rf"(?:the\s+)?(?:(?P<which>first|last)\s+)?(?P<phase>new moon|first quarter moon|full moon|last quarter moon|harvest moon|blue moon)\s+in\s+(?P<month>{MONTH_RE})",
        phrase,
    )
    if constrained_reference_match is not None:
        phase_name = constrained_reference_match.group("phase")
        month = get_month_name_number(constrained_reference_match.group("month"))
        which = constrained_reference_match.group("which") or "first"

        for year in range(reference.get_year(), reference.get_year() + 12):
            candidates = get_moon_phase_datetimes_for_month(year, month, phase_name)
            if not candidates:
                continue
            moment = candidates[-1] if which == "last" else candidates[0]
            if moment.replace(tzinfo=None) >= reference.to_datetime().replace(
                tzinfo=None
            ):
                return date_from_datetime(moment)

    match = re.fullmatch(
        r"(?:the\s+)?(?:(?P<relation>next|last)\s+)?(?P<phase>new moon|first quarter moon|full moon|last quarter moon|harvest moon|blue moon)",
        phrase,
    )
    if match is None:
        return None

    relation = match.group("relation") or "next"
    moment = get_named_moon_datetime(
        reference.to_datetime(), match.group("phase"), relation=relation
    )
    if moment is None:
        return None

    return date_from_datetime(moment)


def get_registered_anchor_definitions(*args, timezone_aware=False, **kwargs):
    from stringtime.parse_anchors import get_registered_anchor_definitions as _impl

    return _impl(*args, timezone_aware=timezone_aware, **kwargs)


def resolve_registered_anchor(
    phrase, *args, families=None, timezone_aware=False, **kwargs
):
    from stringtime.parse_anchors import resolve_registered_anchor as _impl

    return _impl(
        phrase,
        *args,
        families=families,
        timezone_aware=timezone_aware,
        **kwargs,
    )


def get_anchor_metadata_overrides(definition):
    from stringtime.parse_anchors import get_anchor_metadata_overrides as _impl

    return _impl(definition)


def get_named_event_date(phrase, *args, timezone_aware=False, **kwargs):
    resolved, _definition = resolve_registered_anchor(
        phrase,
        *args,
        families={"event"},
        timezone_aware=timezone_aware,
        **kwargs,
    )
    return resolved


def resolve_with_optional_leading_article(
    text,
    resolver,
    *args,
    timezone_aware=False,
    **kwargs,
):
    from stringtime.parse_anchors import resolve_with_optional_leading_article as _impl

    return _impl(
        text,
        resolver,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )


def parse_anchor_date(anchor_text, *args, timezone_aware=False, **kwargs):
    anchor_date, _definition = resolve_registered_anchor(
        anchor_text,
        *args,
        families={"event", "structural"},
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if anchor_date is None:
        anchor_date = parse_natural_date_strict(
            anchor_text,
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
    return anchor_date


def resolve_anchor_target_text(text, *args, timezone_aware=False, **kwargs):
    from stringtime.parse_anchors import resolve_anchor_target_text as _impl

    return _impl(text, *args, timezone_aware=timezone_aware, **kwargs)


def resolve_date_target_text(text, *args, timezone_aware=False, **kwargs):
    from stringtime.parse_anchors import resolve_date_target_text as _impl

    return _impl(text, *args, timezone_aware=timezone_aware, **kwargs)


def resolve_nested_anchor_date_text(text, *args, timezone_aware=False, **kwargs):
    from stringtime.parse_anchors import resolve_nested_anchor_date_text as _impl

    return _impl(text, *args, timezone_aware=timezone_aware, **kwargs)


def get_solar_event_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    reference = get_reference_date()
    phrase = re.sub(r"^(?:on|at)\s+", "", phrase)
    event_pattern = r"dawn|sunrise|sunset|dusk|twilight"

    match = re.fullmatch(rf"(?P<event>{event_pattern})", phrase)
    if match is not None:
        time_value = get_solar_event_time_for_date(reference, match.group("event"))
        if time_value is None:
            return None

        d = set_date_time(reference, time_value[0], time_value[1])
        if (
            reference.get_hours(),
            reference.get_minutes(),
            reference.get_seconds(),
        ) >= (time_value[0], time_value[1], 0):
            d.set_date(d.get_date() + 1)
            shifted_time = get_solar_event_time_for_date(d, match.group("event"))
            if shifted_time is not None:
                d.set_hours(shifted_time[0])
                d.set_minutes(shifted_time[1])
                d.set_seconds(0)
        return d

    for pattern in [
        rf"(?P<event>{event_pattern})\s+on\s+(?P<date>.+)",
        rf"(?P<date>.+?)\s+(?:at|@)\s+(?P<event>{event_pattern})",
        rf"(?P<event>{event_pattern})\s+(?P<date>(?:on\s+)?.+)",
    ]:
        match = re.fullmatch(pattern, phrase)
        if match is None:
            continue

        date_part = resolve_anchor_target_text(
            match.group("date"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if date_part is None:
            continue

        time_value = get_solar_event_time_for_date(date_part, match.group("event"))
        if time_value is None:
            continue

        return set_date_time(date_part, time_value[0], time_value[1])

    return None


def get_part_of_day_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    reference = get_reference_date()
    phrase = re.sub(r"^(?:on|at)\s+", "", phrase)
    if phrase == "last night":
        d = set_date_time(reference, 21, 0)
        d.set_date(d.get_date() - 1)
        return d

    if phrase in {"night before yesterday", "the night before yesterday"}:
        d = set_date_time(reference, 21, 0)
        d.set_date(d.get_date() - 2)
        return d

    if phrase in {"night before last", "the night before last"}:
        d = set_date_time(reference, 21, 0)
        d.set_date(d.get_date() - 2)
        return d

    if phrase in {"other night", "the other night"}:
        d = set_date_time(reference, 21, 0)
        d.set_date(d.get_date() - 1)
        return d

    in_the_match = re.fullmatch(
        r"in the (?P<part>morning|late morning|afternoon|late afternoon|evening|night)",
        phrase,
    )
    if in_the_match is not None:
        part = in_the_match.group("part")
        time_value = get_part_of_day_time(part)
        if time_value is not None:
            d = set_date_time(reference, time_value[0], time_value[1])
            if (
                reference.get_hours(),
                reference.get_minutes(),
                reference.get_seconds(),
            ) >= (time_value[0], time_value[1], 0):
                d.set_date(d.get_date() + 1)
            return d

    standalone_time = get_part_of_day_time(phrase)
    if standalone_time is not None:
        d = set_date_time(reference, standalone_time[0], standalone_time[1])
        if (
            reference.get_hours(),
            reference.get_minutes(),
            reference.get_seconds(),
        ) >= (standalone_time[0], standalone_time[1], 0):
            d.set_date(d.get_date() + 1)
        return d

    patterns = [
        rf"(?P<date>{DAY_REFERENCE_RE})\s+(?P<part>morning|late morning|afternoon|late afternoon|evening|night|lunchtime|dinnertime|teatime|early in the morning|early morning|mid-morning|mid morning)",
        rf"(?P<part>morning|late morning|afternoon|late afternoon|evening|night|lunchtime|dinnertime|teatime|early in the morning|early morning|mid-morning|mid morning)\s+(?P<date>(?:today|tomorrow|yesterday|(?:next|last)\s+(?:{WEEKDAY_RE})|(?:{WEEKDAY_RE})))",
        r"(?P<part>morning|late morning|afternoon|late afternoon|evening|night|lunchtime|dinnertime|teatime)\s+on\s+(?P<date>.+)",
        r"(?:the\s+)?(?P<part>morning|late morning|afternoon|late afternoon|evening|night|lunchtime|dinnertime|teatime)\s+of\s+(?P<date>.+)",
        r"in\s+the\s+(?P<part>morning|late morning|afternoon|late afternoon|evening|night)\s+on\s+(?P<date>.+)",
    ]

    for pattern in patterns:
        match = re.fullmatch(pattern, phrase)
        if match is None:
            continue

        date_text = match.group("date")
        if date_text == "this":
            date_text = "today"

        date_part = parse_natural_date_strict(
            date_text,
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if date_part is None:
            continue

        time_value = get_part_of_day_time(match.group("part"))
        if time_value is None:
            continue

        return set_date_time(date_part, time_value[0], time_value[1])

    return None


def is_business_day(date_obj):
    return date_obj.to_datetime().weekday() < 5


def shift_business_days(date_obj, days):
    d = clone_date(date_obj)
    if days == 0:
        return d

    direction = 1 if days > 0 else -1
    remaining = abs(days)

    while remaining > 0:
        d.set_date(d.get_date() + direction)
        if is_business_day(d):
            remaining -= 1

    return d


def build_day_boundary_date(hour, *, day_offset=0, next_if_past=False):
    d = get_reference_date()

    if day_offset != 0:
        d.set_date(d.get_date() + day_offset)
    elif next_if_past and d.get_hours() >= hour:
        d.set_date(d.get_date() + 1)

    d.set_hours(hour)
    d.set_minutes(0)
    d.set_seconds(0)
    return d


def get_business_phrase_date(phrase):
    if phrase == "next working day":
        return shift_business_days(get_reference_date(), 1)

    if phrase in {"end of business", "end of play", "eop"}:
        return build_day_boundary_date(17)

    if phrase in {"end of business tomorrow", "end of play tomorrow", "eop tomorrow"}:
        return build_day_boundary_date(17, day_offset=1)

    if phrase in {"first thing", "first thing in the morning"}:
        return build_day_boundary_date(9, next_if_past=True)

    match = re.fullmatch(
        r"(?P<label>end of business|end of play|eop)\s+(?P<anchor>.+)",
        phrase,
    )
    if match is not None:
        anchor_date = parse_anchor_like_text(match.group("anchor"))
        if anchor_date is None:
            return None
        return set_date_time(anchor_date, 17, 0)

    match = re.fullmatch(
        r"(?:the\s+)?(?P<count>first|second|third|1st|2nd|3rd|\d+)\s+(?:business|working)\s+days?\s+(?P<direction>after|before)\s+(?P<anchor>.+)",
        phrase,
    )
    if match is not None:
        count_lookup = {
            "first": 1,
            "second": 2,
            "third": 3,
            "1st": 1,
            "2nd": 2,
            "3rd": 3,
        }
        raw_count = match.group("count")
        count = count_lookup.get(
            raw_count, int(raw_count) if raw_count.isdigit() else None
        )
        if count is None:
            return None

        anchor_date = parse_anchor_like_text(match.group("anchor"))
        if anchor_date is None:
            return None

        if match.group("direction") == "before":
            count *= -1

        return shift_business_days(anchor_date, count)

    match = re.fullmatch(
        r"(?:the\s+)?last\s+(?:business|working)\s+day\s+before\s+(?P<anchor>.+)",
        phrase,
    )
    if match is not None:
        anchor_date = parse_anchor_like_text(match.group("anchor"))
        if anchor_date is None:
            return None
        return shift_business_days(anchor_date, -1)

    match = re.fullmatch(
        r"(?:the\s+)?last\s+(?:business|working)\s+day\s+of\s+(?P<period>next month|last month|this month)",
        phrase,
    )
    if match is not None:
        d = clone_date(get_reference_date())
        if match.group("period") == "next month":
            d.set_month(d.get_month() + 1)
        elif match.group("period") == "last month":
            d.set_month(d.get_month() - 1)
        d.set_date(stDate.get_month_length(d.get_month() + 1, d.get_year()))
        while not is_business_day(d):
            d.set_date(d.get_date() - 1)
        return d

    match = re.fullmatch(
        r"(?P<count>\d+)\s+(?:business|working)\s+days?\s+(?P<direction>from now|ago)",
        phrase,
    )
    if match is None:
        return None

    count = int(match.group("count"))
    if match.group("direction") == "ago":
        count *= -1

    return shift_business_days(get_reference_date(), count)


def get_sleep_phrase_date(phrase):
    match = re.fullmatch(r"(?P<count>\d+)\s+more\s+sleeps?", phrase)
    if match is not None:
        d = get_reference_date()
        d.set_date(d.get_date() + int(match.group("count")))
        return d

    match = re.fullmatch(
        r"(?P<count>\d+)\s+sleeps?\s+(?:til|till|until)\s+(?P<target>xmas|christmas)",
        phrase,
    )
    if match is None:
        return None

    count = int(match.group("count"))
    target = "christmas" if match.group("target") == "xmas" else match.group("target")
    target_date = get_holiday_date(target)
    reference = get_reference_date()

    if target_date is None:
        return None

    if target_date.to_datetime().date() <= reference.to_datetime().date():
        target_date.set_fullyear(target_date.get_year() + 1)

    d = clone_date(target_date)
    d.set_date(d.get_date() - count)
    return d


def get_special_phrase_date(phrase):
    if phrase == "y2k":
        d = get_reference_date()
        d.set_fullyear(2000)
        d.set_month(0)
        d.set_date(1)
        return d

    if phrase == "weekend":
        d = clone_date(get_reference_date())
        while d.to_datetime().weekday() != 5:
            d.set_date(d.get_date() + 1)
        return d

    return None


def get_simple_numeric_instant_date(phrase):
    if re.fullmatch(r"\d+\.\d+", phrase):
        try:
            return build_hour_date(float(phrase))
        except (TypeError, ValueError):
            return None

    parsed_cardinal = parse_cardinal_number(phrase)
    if parsed_cardinal is not None and " " not in phrase and "-" not in phrase:
        return build_hour_date(parsed_cardinal)

    return None


def get_simple_clock_instant_date(phrase):
    match = re.fullmatch(
        r"(?:at\s+)?(?:(?:about|around)\s+)?(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?(?:ish)?(?:\s?(?P<meridiem>am|pm))?(?:\s+oclock)?",
        phrase,
    )
    if match is None:
        return None

    hour = int(match.group("hour"))
    minute = int(match.group("minute") or 0)
    meridiem = match.group("meridiem")
    normalized_hour = normalize_meridiem_hour(hour, meridiem)
    return build_timestamp_date(normalized_hour, minute, 0)


def get_compact_offset_phrase_date(phrase):
    match = re.fullmatch(
        r"(?P<count>\d+)(?P<unit>m|h|d|w|y)(?:\s+(?P<direction>ago|from now|hence))?",
        phrase,
    )
    if match is None:
        return None

    unit_map = {
        "m": "minute",
        "h": "hour",
        "d": "day",
        "w": "week",
        "y": "year",
    }
    direction = match.group("direction")
    sign = -1 if direction == "ago" else 1
    return apply_relative_offset(
        get_reference_date(),
        unit_map[match.group("unit")],
        int(match.group("count")),
        sign=sign,
    )


def get_named_clock_time(phrase):
    exact_aliases = {
        "chinese dentist": (2, 30),
        "cowboy time": (9, 50),
        "midnight": (0, 0),
        "noon": (12, 0),
        "midday": (12, 0),
        "high noon": (12, 0),
    }

    return exact_aliases.get(phrase)


def get_clock_phrase_date(phrase):
    compound_amount_pattern = r"(?:twenty|thirty|forty|fifty)(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?"
    word_hours = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
        "twenty one": 21,
        "twenty two": 22,
        "twenty three": 23,
    }

    def parse_clock_hour(value):
        meridiem_match = re.fullmatch(r"(?P<hour>\d{1,2})(?P<meridiem>am|pm)", value)
        if meridiem_match is not None:
            return normalize_meridiem_hour(
                meridiem_match.group("hour"),
                meridiem_match.group("meridiem"),
            )
        if value.isdigit():
            return int(value) % 24
        return word_hours.get(value)

    def parse_clock_with_part_of_day(value, part):
        clock_date = get_clock_phrase_date(value)
        if clock_date is None:
            clock_date = parse_natural_date_strict(value)
        if clock_date is None:
            return None

        hour = clock_date.get_hours()
        if part in {"afternoon", "evening", "night"} and hour < 12:
            hour += 12
        if part == "morning" and hour == 12:
            hour = 0

        d = clone_date(clock_date)
        d.set_hours(hour)
        return d

    precise_time_match = re.fullmatch(
        r"(?P<hour>\d{1,2}):(?P<minute>\d{2})(?::(?P<second>\d{2}))?(?P<meridiem>\s?(?:am|pm))?",
        phrase,
        re.IGNORECASE,
    )
    if precise_time_match is not None:
        return build_structured_time_date(
            precise_time_match.group("hour"),
            int(precise_time_match.group("minute")),
            int(precise_time_match.group("second") or 0),
            precise_time_match.group("meridiem"),
        )

    precise_with_extra_seconds_match = re.fullmatch(
        r"(?P<hour>\d{1,2}):(?P<minute>\d{2})(?:\s+and\s+)(?P<second>\d{1,2})\s+seconds?(?P<meridiem>\s?(?:am|pm))?",
        phrase,
        re.IGNORECASE,
    )
    if precise_with_extra_seconds_match is None:
        precise_with_extra_seconds_match = re.fullmatch(
            r"(?P<hour>\d{1,2}):(?P<minute>\d{2})(?P<meridiem>\s?(?:am|pm))(?:\s+and\s+)(?P<second>\d{1,2})\s+seconds?",
            phrase,
            re.IGNORECASE,
        )
    if precise_with_extra_seconds_match is not None:
        return build_structured_time_date(
            precise_with_extra_seconds_match.group("hour"),
            int(precise_with_extra_seconds_match.group("minute")),
            int(precise_with_extra_seconds_match.group("second")),
            precise_with_extra_seconds_match.group("meridiem"),
        )

    bare_meridiem_match = re.fullmatch(
        r"(?P<hour>\d{1,2})\s?(?P<meridiem>am|pm)",
        phrase,
        re.IGNORECASE,
    )
    if bare_meridiem_match is not None:
        return build_structured_time_date(
            bare_meridiem_match.group("hour"),
            0,
            0,
            bare_meridiem_match.group("meridiem"),
        )

    part_of_day_match = re.fullmatch(
        r"(?P<clock>.+?)\s+in\s+the\s+(?P<part>morning|afternoon|evening|night)",
        phrase,
    )
    if part_of_day_match is not None:
        return parse_clock_with_part_of_day(
            part_of_day_match.group("clock"),
            part_of_day_match.group("part"),
        )

    named_time = get_named_clock_time(phrase)
    if named_time is not None:
        hour, minute = named_time
        d = get_reference_date()
        d.set_hours(hour)
        d.set_minutes(minute)
        d.set_seconds(0)
        return d

    match = re.fullmatch(
        r"(?:when\s+)?the\s+clock\s+strikes\s+(?P<hour>\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)",
        phrase,
    )
    if match is None:
        match = re.fullmatch(
            r"when the clock strikes (?P<hour>\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)",
            phrase,
        )
    if match is not None:
        hour = parse_clock_hour(match.group("hour"))
        if hour is None:
            return None
        d = get_reference_date()
        d.set_hours(hour)
        d.set_minutes(0)
        d.set_seconds(0)
        return d

    match = re.fullmatch(
        r"(?P<ones>\d{1,2}|one|two|three|four|five|six|seven|eight|nine)\s+and\s+(?:20|twenty)\s+past\s+(?P<hour>\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)(?:\s+hundred\s+hours)?",
        phrase,
    )
    if match is not None:
        ones = parse_clock_hour(match.group("ones"))
        hour = parse_clock_hour(match.group("hour"))
        if ones is None or hour is None:
            return None
        d = get_reference_date()
        d.set_hours(hour)
        d.set_minutes(20 + ones)
        d.set_seconds(0)
        return d

    match = re.fullmatch(
        r"(?:a\s+)?quarter\s+(?P<direction>past|to)\s+"
        r"(?P<hour>\d{1,2}(?:am|pm)?|midnight|noon|midday|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)",
        phrase,
    )
    if match is not None:
        minutes = 15
        seconds = 0
        direction = match.group("direction")
        target_hour = match.group("hour")
        if target_hour in {"midnight", "noon", "midday"}:
            named_hour, _named_minute = get_named_clock_time(target_hour)
            hour = named_hour
        else:
            hour = parse_clock_hour(target_hour)
    else:
        match = re.fullmatch(
            r"half\s+past\s+"
            r"(?P<hour>\d{1,2}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)",
            phrase,
        )
        if match is not None:
            minutes = 30
            seconds = 0
            direction = "past"
            hour = parse_clock_hour(match.group("hour"))
        else:
            match = re.fullmatch(
                r"(?P<amount>a|an|\d+)\s+minutes?\s+(?P<direction>past|to)\s+(?P<hour>\d{1,2}(?:\s*(?:am|pm))?)",
                phrase,
            )
            if match is not None:
                minutes = (
                    1
                    if match.group("amount") in {"a", "an"}
                    else int(match.group("amount"))
                )
                seconds = 0
                direction = match.group("direction")
                hour = parse_clock_hour(match.group("hour").replace(" ", ""))
            else:
                match = re.fullmatch(
                    rf"(?P<amount>a|an|\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|{compound_amount_pattern})"
                    r"\s+seconds?\s+(?P<direction>past|to)\s+(?P<hour>\d{1,2}(?:\s*(?:am|pm))?|midnight|noon|midday)",
                    phrase,
                )
                if match is not None:
                    if match.group("amount") in {"a", "an"}:
                        seconds = 1
                    elif match.group("amount").isdigit():
                        seconds = int(match.group("amount"))
                    else:
                        seconds = parse_offset_number(match.group("amount"))
                    minutes = 0
                    direction = match.group("direction")
                    target_hour = match.group("hour").replace(" ", "")
                    if target_hour in {"midnight", "noon", "midday"}:
                        named_hour, named_minute = get_named_clock_time(target_hour)
                        hour = named_hour
                    else:
                        hour = parse_clock_hour(target_hour)
                else:
                    match = re.fullmatch(
                        rf"(?P<amount>a|an|\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|{compound_amount_pattern})"
                        r"\s+(?P<direction>past|to)\s+"
                        r"(?P<hour>\d{1,2}(?:am|pm)?|midnight|noon|midday|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)",
                        phrase,
                    )
                    if match is not None:
                        minutes = parse_offset_number(match.group("amount"))
                        seconds = 0
                        direction = match.group("direction")
                        target_hour = match.group("hour")
                        if target_hour in {"midnight", "noon", "midday"}:
                            named_hour, _named_minute = get_named_clock_time(
                                target_hour
                            )
                            hour = named_hour
                        else:
                            hour = parse_clock_hour(target_hour)
                    else:
                        match = re.fullmatch(
                            r"half\s+(?P<hour>\d{1,2}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)",
                            phrase,
                        )
                        if match is not None:
                            minutes = 30
                            seconds = 0
                            direction = "past"
                            hour = parse_clock_hour(match.group("hour"))
                        else:
                            match = re.fullmatch(
                                r"(?P<amount>a|an|\d+)\s+minutes?\s+past\s+the\s+hour",
                                phrase,
                            )
                            if match is not None:
                                minutes = (
                                    1
                                    if match.group("amount") in {"a", "an"}
                                    else int(match.group("amount"))
                                )
                                seconds = 0
                                direction = "past_hour"
                                hour = None
    if match is None:
        return None

    d = get_reference_date()
    if direction == "past":
        d.set_hours(hour)
        d.set_minutes(minutes)
        d.set_seconds(seconds)
    elif direction == "past_hour":
        d.set_minutes(minutes)
        d.set_seconds(0)
    else:
        d.set_hours((hour - 1) % 24)
        if seconds:
            d.set_minutes(59 - minutes)
            d.set_seconds(60 - seconds)
        else:
            d.set_minutes(60 - minutes)
            d.set_seconds(0)
    return d


def get_compound_clock_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    patterns = [
        r"(?P<date>today|tomorrow|yesterday)\s+(?:at\s+)?(?P<time>noon|midnight|midday)",
        r"(?P<time>noon|midnight|midday)\s+(?P<date>today|tomorrow|yesterday)",
        r"(?P<time>noon|midnight|midday)\s+on\s+(?P<date>.+)",
    ]

    for pattern in patterns:
        match = re.fullmatch(pattern, phrase)
        if match is None:
            continue

        time_value = get_named_clock_time(match.group("time"))
        if time_value is None:
            continue

        date_part = parse_natural_date_strict(
            match.group("date"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if date_part is None:
            continue

        d = clone_date(date_part)
        d.set_hours(time_value[0])
        d.set_minutes(time_value[1])
        d.set_seconds(0)
        return d

    return None


def merge_date_parts(base_date, overlay_date):
    now = get_reference_date()
    d = base_date
    d2 = overlay_date

    if d2.get_year() != now.get_year():
        d.set_year(d2.get_year())
    if d2.get_month() != now.get_month():
        d.set_month(d2.get_month())
    if d2.get_date() != now.get_date():
        d.set_date(d2.get_date())
    if d2.get_hours() != now.get_hours():
        d.set_hours(d2.get_hours())
    if d2.get_minutes() != now.get_minutes():
        d.set_minutes(d2.get_minutes())
    if d2.get_seconds() != now.get_seconds():
        d.set_seconds(d2.get_seconds())

    return d


def merge_date_with_explicit_time(base_date, time_date):
    d = clone_date(base_date)
    d2 = time_date
    d.set_hours(d2.get_hours())
    d.set_minutes(d2.get_minutes())
    d.set_seconds(d2.get_seconds())
    return d


def merge_date_with_relative_time_phrase(base_date, time_phrase):
    match = re.fullmatch(
        r"(?P<amount>a|an|\d+)\s+minutes?\s+past\s+the\s+hour", time_phrase
    )
    if match is None:
        return None

    minutes = 1 if match.group("amount") in {"a", "an"} else int(match.group("amount"))
    d = clone_date(base_date)
    d.set_minutes(minutes)
    d.set_seconds(0)
    return d


def parse_structured_date_text(candidate, *args, timezone_aware=False, **kwargs):
    if not candidate:
        return None

    parsed = parse_natural_date_strict(
        candidate,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if parsed is not None:
        return parsed

    normalized_candidate = normalize_phrase(candidate)
    if normalized_candidate != candidate:
        return parse_natural_date_strict(
            normalized_candidate,
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )

    return None


def parse_anchor_like_text(candidate, *args, timezone_aware=False, **kwargs):
    from stringtime.parse_anchors import parse_anchor_like_text as _impl

    return _impl(candidate, *args, timezone_aware=timezone_aware, **kwargs)


def parse_structured_time_text(
    candidate, *args, reference_override=None, timezone_aware=False, **kwargs
):
    if not candidate:
        return None

    def parse_clock_with_part_of_day(value, part):
        clock_date = get_clock_phrase_date(value)
        if clock_date is None:
            return None

        hour = clock_date.get_hours()
        if part in {"afternoon", "evening", "night"} and hour < 12:
            hour += 12
        if part == "morning" and hour == 12:
            hour = 0

        d = clone_date(clock_date)
        d.set_hours(hour)
        return d

    token = None
    if reference_override is not None:
        token = CURRENT_REFERENCE.set(clone_date(reference_override))

    try:
        time_date = get_clock_phrase_date(candidate)
        if time_date is not None:
            return time_date

        if TIME_TOKEN_RE.fullmatch(candidate) or candidate in {
            "noon",
            "midnight",
            "midday",
        }:
            time_date = parse_natural_date_strict(
                candidate,
                *args,
                timezone_aware=timezone_aware,
                **kwargs,
            )
            if time_date is not None:
                return time_date

        precise_time_match = re.fullmatch(
            r"\d{1,2}:\d{2}:\d{2}(?:\s?(?:am|pm))?",
            candidate,
            re.IGNORECASE,
        )
        if precise_time_match is not None:
            time_date = parse_natural_date_strict(
                candidate,
                *args,
                timezone_aware=timezone_aware,
                **kwargs,
            )
            if time_date is not None:
                return time_date

        fuzzy_time_match = re.fullmatch(
            r"(?:about|around)\s+\d{1,2}(?::\d{2})?(?:ish)?|\d{1,2}(?::\d{2})?ish",
            candidate,
            re.IGNORECASE,
        )
        if fuzzy_time_match is not None:
            time_date = get_simple_clock_instant_date(candidate)
            if time_date is not None:
                return time_date

        part_of_day_match = re.fullmatch(
            r"(?P<clock>.+?)\s+in\s+the\s+(?P<part>morning|afternoon|evening|night)",
            candidate,
        )
        if part_of_day_match is not None:
            time_date = parse_clock_with_part_of_day(
                part_of_day_match.group("clock"),
                part_of_day_match.group("part"),
            )
            if time_date is not None:
                return time_date

        time_date = get_part_of_day_phrase_date(
            candidate, *args, timezone_aware=timezone_aware, **kwargs
        )
        if time_date is not None:
            return time_date

        time_date = get_business_phrase_date(candidate)
        if time_date is not None:
            return time_date

        if re.fullmatch(r"\d{1,2}", candidate):
            return build_structured_time_date(int(candidate), 0, 0)

        return None
    finally:
        if token is not None:
            CURRENT_REFERENCE.reset(token)


def try_merge_date_time_pattern(
    phrase,
    pattern,
    *,
    date_group,
    time_group,
    args=(),
    timezone_aware=False,
    **kwargs,
):
    match = re.fullmatch(pattern, phrase)
    if match is None:
        return None

    date_part = parse_structured_date_text(
        match.group(date_group),
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if date_part is None:
        return None

    time_part = parse_structured_time_text(
        match.group(time_group),
        *args,
        reference_override=date_part,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if time_part is None:
        return None

    return merge_date_with_explicit_time(date_part, time_part)


def try_merge_time_date_pattern(
    phrase,
    pattern,
    *,
    time_group,
    date_group,
    args=(),
    timezone_aware=False,
    **kwargs,
):
    match = re.fullmatch(pattern, phrase)
    if match is None:
        return None

    date_part = parse_structured_date_text(
        match.group(date_group),
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if date_part is None:
        return None

    relative_time_merge = merge_date_with_relative_time_phrase(
        date_part,
        match.group(time_group),
    )
    if relative_time_merge is not None:
        return relative_time_merge

    time_part = parse_structured_time_text(
        match.group(time_group),
        *args,
        reference_override=date_part,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if time_part is None:
        return None

    return merge_date_with_explicit_time(date_part, time_part)


def apply_relative_offset(base_date, unit, amount, sign=1):
    d = clone_date(base_date)
    amount = amount * sign

    if unit == "year":
        d.set_fullyear(d.get_year() + amount)
    elif unit == "month":
        d.set_month(d.get_month() + amount)
    elif unit == "week":
        d._date = d.to_datetime() + datetime.timedelta(weeks=amount)
    elif unit == "day":
        d._date = d.to_datetime() + datetime.timedelta(days=amount)
    elif unit == "hour":
        d._date = d.to_datetime() + datetime.timedelta(hours=amount)
    elif unit == "minute":
        d._date = d.to_datetime() + datetime.timedelta(minutes=amount)
    elif unit == "second":
        d._date = d.to_datetime() + datetime.timedelta(seconds=amount)
    elif unit == "millisecond":
        d._date = d.to_datetime() + datetime.timedelta(milliseconds=amount)
    elif unit == "microsecond":
        d._date = d.to_datetime() + datetime.timedelta(microseconds=amount)

    return d


def parse_offset_number(raw_number):
    ordinal_match = re.fullmatch(r"(\d+)(?:st|nd|rd|th)", raw_number)
    if ordinal_match is not None:
        return int(ordinal_match.group(1))

    compound_match = re.fullmatch(
        r"(?P<tens>twenty|thirty|forty|fifty)(?:[- ](?P<ones>one|two|three|four|five|six|seven|eight|nine))?",
        raw_number,
    )
    if compound_match is not None:
        tens_values = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}
        ones_values = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
        }
        value = tens_values[compound_match.group("tens")]
        if compound_match.group("ones") is not None:
            value += ones_values[compound_match.group("ones")]
        return value

    if raw_number == "several":
        return 7
    return parse_cardinal_number(raw_number)


def parse_compound_offset(offset_text):
    offset_text = re.sub(
        r"\bhalf\s+(?:a\s+|an\s+)?millisecond\b",
        "500 microseconds",
        offset_text,
    )
    offset_text = re.sub(
        r"\bhalf\s+(?:a\s+|an\s+)?second\b",
        "500 milliseconds",
        offset_text,
    )
    offset_text = re.sub(
        r"\bhalf\s+(?:a\s+|an\s+)?minute\b",
        "30 seconds",
        offset_text,
    )
    offset_text = re.sub(
        r"\bhalf\s+(?:a\s+|an\s+)?hour\b",
        "30 minutes",
        offset_text,
    )
    offset_text = re.sub(
        r"\bhalf\s+(?:a\s+|an\s+)?day\b",
        "12 hours",
        offset_text,
    )
    number_pattern = (
        r"(\d+(?:st|nd|rd|th)?|a|an|one|two|three|four|five|six|seven|eight|nine|ten|"
        r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
        r"twenty|twenty[- ]one|twenty[- ]two|twenty[- ]three|twenty[- ]four|twenty[- ]five|"
        r"twenty[- ]six|twenty[- ]seven|twenty[- ]eight|twenty[- ]nine|thirty|thirty[- ]one|"
        r"thirty[- ]two|thirty[- ]three|thirty[- ]four|thirty[- ]five|thirty[- ]six|"
        r"thirty[- ]seven|thirty[- ]eight|thirty[- ]nine|forty|forty[- ]one|forty[- ]two|"
        r"forty[- ]three|forty[- ]four|forty[- ]five|forty[- ]six|forty[- ]seven|"
        r"forty[- ]eight|forty[- ]nine|fifty|fifty[- ]one|fifty[- ]two|fifty[- ]three|"
        r"fifty[- ]four|fifty[- ]five|fifty[- ]six|fifty[- ]seven|fifty[- ]eight|fifty[- ]nine)"
    )
    unit_pattern = r"(years?|months?|weeks?|days?|nights?|hours?|minutes?|seconds?|milliseconds?|microseconds?)"
    components = []

    half_match = re.fullmatch(
        rf"(?P<whole>{number_pattern})\s+(?P<unit>{unit_pattern})\s+and\s+(?:a|an|one)?\s*half",
        offset_text,
    )
    if half_match is not None:
        amount = parse_offset_number(half_match.group("whole"))
        if amount is None:
            return None
        unit = half_match.group("unit")
        unit = unit[:-1] if unit.endswith("s") else unit
        if unit == "night":
            unit = "day"
        return [(unit, amount + 0.5)]

    for raw_number, raw_unit in re.findall(
        rf"{number_pattern}\s+{unit_pattern}", offset_text
    ):
        amount = parse_offset_number(raw_number)
        if amount is None:
            return None
        unit = raw_unit[:-1] if raw_unit.endswith("s") else raw_unit
        if unit == "night":
            unit = "day"
        components.append((unit, amount))

    if not components:
        return None

    normalized = re.sub(
        rf"{number_pattern}\s+{unit_pattern}",
        "",
        offset_text,
    )
    normalized = re.sub(r"\b(?:and|,)\b", "", normalized)
    if normalized.strip():
        return None

    return components


def apply_relative_offsets(base_date, components, sign=1):
    d = clone_date(base_date)
    for unit, amount in components:
        d = apply_relative_offset(d, unit, amount, sign=sign)
    return d


def get_add_subtract_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    reference = get_reference_date()
    patterns = (
        (r"(?P<anchor>today|now)\s+(?:plus|add)\s+(?P<offset>.+)", 1),
        (r"(?P<anchor>today|now)\s+(?:minus|take away|off)\s+(?P<offset>.+)", -1),
        (r"(?:plus|add)\s+(?P<offset>.+)", 1),
        (r"(?:minus|take away|off)\s+(?P<offset>.+)", -1),
        (r"(?:in\s+)?(?P<offset>.+?)\s+time", 1),
        (r"(?P<offset>.+?)\s+or so", 1),
        (r"(?:give or take|roughly|approximately|about|around)\s+(?P<offset>.+)", 1),
    )

    for pattern, sign in patterns:
        match = re.fullmatch(pattern, phrase)
        if match is None:
            continue

        offset_text = replace_short_words(match.group("offset").strip())
        components = parse_compound_offset(offset_text)
        if components is None:
            continue

        anchor_text = match.groupdict().get("anchor")
        if anchor_text is None:
            anchor_date = clone_date(reference)
        else:
            anchor_date = resolve_date_target_text(
                anchor_text,
                *args,
                timezone_aware=timezone_aware,
                **kwargs,
            )
            if anchor_date is None:
                continue

        return apply_relative_offsets(anchor_date, components, sign=sign)

    return None


def get_anchor_offset_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    phrase = re.sub(r"^(?:the\s+)?day\s+before\s+", "1 day before ", phrase)
    phrase = re.sub(r"^(?:the\s+)?day\s+after\s+", "1 day after ", phrase)

    shortcut_match = re.fullmatch(
        r"(?P<offset>.+?)\s+(?:(?P<direction>before|prior|earlier)\s+)?(?P<anchor>today|tomorrow|yesterday)",
        phrase,
    )
    if shortcut_match is not None:
        components = parse_compound_offset(
            replace_short_words(shortcut_match.group("offset").strip())
        )
        if components is not None:
            anchor_date = resolve_date_target_text(
                shortcut_match.group("anchor"),
                *args,
                timezone_aware=timezone_aware,
                **kwargs,
            )
            if anchor_date is not None:
                sign = (
                    -1
                    if shortcut_match.group("direction") in {"before", "prior", "earlier"}
                    else 1
                )
                return apply_relative_offsets(anchor_date, components, sign)

    shortcut_to_match = re.fullmatch(
        r"(?P<offset>.+?)\s+(?P<direction>prior|earlier)\s+to\s+(?P<anchor>today|tomorrow|yesterday)",
        phrase,
    )
    if shortcut_to_match is not None:
        components = parse_compound_offset(
            replace_short_words(shortcut_to_match.group("offset").strip())
        )
        if components is not None:
            anchor_date = resolve_date_target_text(
                shortcut_to_match.group("anchor"),
                *args,
                timezone_aware=timezone_aware,
                **kwargs,
            )
            if anchor_date is not None:
                return apply_relative_offsets(anchor_date, components, -1)

    on_anchor_match = re.fullmatch(
        r"(?P<offset>.+?)\s+on\s+(?P<anchor>.+)",
        phrase,
    )
    if on_anchor_match is not None:
        raw_offset_text = replace_short_words(on_anchor_match.group("offset").strip())
        sign = 1
        directed_offset_match = re.fullmatch(
            r"(?P<offset>.+?)\s+(?P<direction>ago|from now|hence|time)",
            raw_offset_text,
        )
        if directed_offset_match is not None:
            raw_offset_text = directed_offset_match.group("offset").strip()
            if directed_offset_match.group("direction") == "ago":
                sign = -1

        components = parse_compound_offset(raw_offset_text)
        if components is not None:
            anchor_date = parse_anchor_like_text(
                on_anchor_match.group("anchor"),
                *args,
                timezone_aware=timezone_aware,
                **kwargs,
            )
            if anchor_date is not None:
                return apply_relative_offsets(anchor_date, components, sign)

    match = re.fullmatch(
        r"(?:(?:in)\s+)?(?P<offset>.+?)\s+(?P<direction>from|after|before|prior|earlier)\s+(?P<anchor>.+)",
        phrase,
    )
    if match is None:
        return None

    offset_text = replace_short_words(
        re.sub(r"^(?:the)\s+", "", match.group("offset").strip())
    )
    components = parse_compound_offset(offset_text)
    if components is None:
        bare_unit_match = re.fullmatch(
            r"(?:a|an)?\s*(year|month|week|day|hour|minute|second|millisecond|microsecond)s?",
            offset_text,
        )
        if bare_unit_match is not None:
            components = [(bare_unit_match.group(1), 1)]
    if components is None:
        if offset_text == "weekend":
            components = [("weekend", 1)]
        else:
            return None

    direction = match.group("direction")
    sign = -1 if direction in {"before", "prior", "earlier"} else 1

    anchor_text = match.group("anchor").strip()
    anchor_date = parse_anchor_like_text(
        anchor_text,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if anchor_date is None:
        return None

    if components == [("weekend", 1)]:
        d = clone_date(anchor_date)
        weekday = d.to_datetime().weekday()
        if sign > 0:
            days_until_saturday = (5 - weekday) % 7
            if days_until_saturday == 0:
                days_until_saturday = 7
            d.set_date(d.get_date() + days_until_saturday)
        else:
            days_since_saturday = (weekday - 5) % 7
            if days_since_saturday == 0:
                days_since_saturday = 7
            d.set_date(d.get_date() - days_since_saturday)
        return d

    return apply_relative_offsets(anchor_date, components, sign)


def parse_with_shifted_reference(target_year, text, *args, timezone_aware=False, **kwargs):
    shifted_reference = clone_date(get_reference_date())
    shifted_reference.set_fullyear(target_year)
    parse_kwargs = dict(kwargs)
    parse_kwargs["relative_to"] = shifted_reference
    return parse_natural_date_strict(
        text,
        *args,
        timezone_aware=timezone_aware,
        **parse_kwargs,
    )


def get_year_wrapped_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    match = re.fullmatch(r"(?P<year>\d{4})\s+(?P<rest>.+)", phrase)
    if match is None:
        return None

    inner_date = parse_with_shifted_reference(
        int(match.group("year")),
        match.group("rest"),
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if inner_date is None:
        return None

    return inner_date


def get_year_suffix_wrapped_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    match = re.fullmatch(r"(?P<rest>.+?)\s+(?P<year>\d{4})", phrase)
    if match is None:
        return None

    target_year = int(match.group("year"))
    inner_date = parse_with_shifted_reference(
        target_year,
        match.group("rest"),
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if inner_date is None:
        return None

    if inner_date.get_year() != target_year:
        inner_date = clone_date(inner_date)
        inner_date.set_fullyear(target_year)

    return inner_date


def try_merge_date_and_time_texts(
    date_text,
    time_text,
    *args,
    timezone_aware=False,
    time_transform=None,
    **kwargs,
):
    date_part = parse_structured_date_text(
        date_text,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if date_part is None:
        return None

    if time_transform is not None:
        time_text = time_transform(time_text)

    time_part = parse_structured_time_text(
        time_text,
        *args,
        reference_override=date_part,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if time_part is None:
        return None

    return merge_date_with_explicit_time(date_part, time_part)


def try_merge_time_and_date_texts(
    time_text,
    date_text,
    *args,
    timezone_aware=False,
    time_transform=None,
    **kwargs,
):
    date_part = parse_structured_date_text(
        date_text,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if date_part is None:
        return None

    if time_transform is not None:
        time_text = time_transform(time_text)

    time_part = parse_structured_time_text(
        time_text,
        *args,
        reference_override=date_part,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if time_part is None:
        return None

    return merge_date_with_explicit_time(date_part, time_part)


def try_merge_token_split_date_time(
    phrase,
    *args,
    timezone_aware=False,
    max_tokens=8,
    **kwargs,
):
    if "@" in phrase or " at " in f" {phrase} ":
        return None

    tokens = phrase.split()
    max_span = min(len(tokens) - 1, max_tokens)

    for tail_size in range(max_span, 1, -1):
        merged = try_merge_date_and_time_texts(
            " ".join(tokens[:-tail_size]).strip(),
            " ".join(tokens[-tail_size:]).strip(),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if merged is not None:
            return merged

    for head_size in range(max_span, 1, -1):
        merged = try_merge_time_and_date_texts(
            " ".join(tokens[:head_size]).strip(),
            " ".join(tokens[head_size:]).strip(),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if merged is not None:
            return merged

    return None


def get_composed_date_time_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    if re.fullmatch(
        rf"(?:the\s+)?(?:{POSITIVE_ORDINAL_OCCURRENCE_PATTERN})\s+week\s+(?:of|in)\s+.+",
        phrase,
    ) and not re.search(r"\s+(?:at|@)\s+", phrase):
        return None

    if re.fullmatch(
        rf"(?:the\s+)?(?:{DATE_ORDINAL_PATTERN})\s+minute\s+on\s+.+",
        phrase,
    ):
        return None

    if re.fullmatch(
        rf"(?:the\s+)?(?:{DATE_ORDINAL_PATTERN})\s+second\s+of\s+(?:the\s+)?(?:{DATE_ORDINAL_PATTERN})\s+minute\s+on\s+.+",
        phrase,
    ):
        return None

    year_wrapped = get_year_wrapped_phrase_date(
        phrase, *args, timezone_aware=timezone_aware, **kwargs
    )
    if year_wrapped is not None:
        return year_wrapped

    trailing_year_wrapped = get_year_suffix_wrapped_phrase_date(
        phrase, *args, timezone_aware=timezone_aware, **kwargs
    )
    if trailing_year_wrapped is not None:
        return trailing_year_wrapped

    compound_amount_pattern = r"(?:twenty|thirty|forty|fifty)(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?"
    clock_phrase_pattern = (
        rf"(?:a\s+)?quarter\s+(?:past|to)\s+(?:midnight|noon|midday|\d{{1,2}}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
        rf"|half\s+past\s+(?:\d{{1,2}}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
        rf"|half\s+(?:\d{{1,2}}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
        rf"|(?:a|an|\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|{compound_amount_pattern})\s+(?:minutes?\s+|seconds?\s+)?(?:past|to)\s+(?:the\s+hour|midnight|noon|midday|\d{{1,2}}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    )

    date_with_part_then_time_match = re.fullmatch(
        r"(?P<date>.+?)\s+in\s+the\s+(?P<part>morning|late morning|afternoon|late afternoon|evening|night)\s+(?:at|@)\s+(?P<time>.+)",
        phrase,
    )
    if date_with_part_then_time_match is not None:
        merged = try_merge_date_and_time_texts(
            date_with_part_then_time_match.group("date"),
            *args,
            timezone_aware=timezone_aware,
            time_text=date_with_part_then_time_match.group("time"),
            time_transform=lambda text: f"{text} in the {date_with_part_then_time_match.group('part')}",
            **kwargs,
        )
        if merged is not None:
            return merged

    date_then_time_with_part_match = re.fullmatch(
        r"(?P<date>.+?)\s+(?:at|@)\s+(?P<time>.+?\s+in\s+the\s+(?:morning|afternoon|evening|night))",
        phrase,
    )
    if date_then_time_with_part_match is not None:
        merged = try_merge_date_and_time_texts(
            date_then_time_with_part_match.group("date"),
            date_then_time_with_part_match.group("time"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if merged is not None:
            return merged

    generic_time_by_date_match = re.fullmatch(
        r"(?P<time>.+?)\s+by\s+(?P<date>.+)",
        phrase,
    )
    if generic_time_by_date_match is not None:
        merged = try_merge_time_and_date_texts(
            generic_time_by_date_match.group("time"),
            generic_time_by_date_match.group("date"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if merged is not None:
            return merged

    leading_at_match = re.fullmatch(r"at\s+(?P<rest>.+)", phrase)
    if leading_at_match is not None:
        leading_at_composed = get_composed_date_time_phrase_date(
            leading_at_match.group("rest"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if leading_at_composed is not None:
            return leading_at_composed

    explicit_time_relative_day_match = re.fullmatch(
        r"(?P<time>.+?)\s+(?P<date>(?:today|tomorrow|yesterday)\s+(?:morning|afternoon|evening|night))",
        phrase,
    )
    if explicit_time_relative_day_match is not None:
        merged = try_merge_time_and_date_texts(
            explicit_time_relative_day_match.group("time"),
            explicit_time_relative_day_match.group("date"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if merged is not None:
            return merged

    generic_date_when_time_match = re.fullmatch(
        r"(?P<head>.+?)\s+when\s+(?P<tail>the\s+clock\s+strikes\s+.+)",
        phrase,
    )
    if generic_date_when_time_match is not None:
        head_date = parse_structured_date_text(
            generic_date_when_time_match.group("head"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if head_date is not None:
            tail_clock = get_clock_phrase_date(
                generic_date_when_time_match.group("tail")
            )
            if tail_clock is not None:
                return merge_date_with_explicit_time(head_date, tail_clock)

    bare_date_then_clock_match = re.fullmatch(
        rf"(?P<head>.+?)\s+(?P<tail>{clock_phrase_pattern})",
        phrase,
    )
    if bare_date_then_clock_match is not None:
        merged = try_merge_date_and_time_texts(
            bare_date_then_clock_match.group("head"),
            bare_date_then_clock_match.group("tail"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if merged is not None:
            return merged

    bare_clock_then_date_match = re.fullmatch(
        rf"(?P<head>{clock_phrase_pattern})\s+(?P<tail>.+)",
        phrase,
    )
    if bare_clock_then_date_match is not None:
        merged = try_merge_time_and_date_texts(
            bare_clock_then_date_match.group("head"),
            bare_clock_then_date_match.group("tail"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if merged is not None:
            return merged

    token_split_merged = try_merge_token_split_date_time(
        phrase,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if token_split_merged is not None:
        return token_split_merged

    date_then_time_patterns = [
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>\d{1,2}(?::\d{2})?(?::\d{2})?(?:\s?(?:am|pm))?|noon|midnight|midday)",
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>\d{1,2}:\d{2}\s+and\s+\d{1,2}\s+seconds?(?:\s?(?:am|pm))?)",
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>\d{1,2}:\d{2}\s?(?:am|pm)\s+and\s+\d{1,2}\s+seconds?)",
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>end of business|close of business|end of play|close of play|eob|cob|eop)",
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>lunchtime|dinnertime|teatime|morning|afternoon|evening|night|early in the morning|early morning|mid-morning|mid morning)",
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>\d{1,2}(?::\d{2})?ish)",
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>(?:about|around)\s+\d{1,2}(?::\d{2})?ish)",
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>(?:about|around)\s+\d{1,2}(?::\d{2})?(?:am|pm))",
        rf"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>{clock_phrase_pattern})",
        rf"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>(?:a|an|\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|{compound_amount_pattern})\s+(?:minutes?\s+)?(?:past|to)\s+(?:the\s+hour|\d{1,2}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve))",
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>(?:a\s+)?quarter\s+(?:past|to)\s+(?:\d{1,2}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)|half\s+past\s+(?:\d{1,2}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)|half\s+(?:\d{1,2}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve))",
    ]
    time_then_date_patterns = [
        r"(?P<time>\d{1,2}(?::\d{2})?(?::\d{2})?\s?(?:am|pm)|noon|midnight|midday)\s+(?P<date>.+)",
        r"(?P<time>.+?)\s+(?P<date>(?:on\s+)?(?:today|tomorrow|yesterday|this)\b.*)",
        rf"(?P<time>.+?)\s+(?P<date>(?:the\s+)?(?:first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th|last|penultimate)\s+(?:{WEEKDAY_RE})\b.*)",
        r"(?P<time>.+?)\s+on\s+(?P<date>.+)",
        r"(?P<time>.+?)\s+in\s+(?P<date>.+)",
        rf"(?P<time>.+?)\s+(?P<date>(?:on\s+)?(?:(?:next|last)\s+)?(?:{WEEKDAY_RE})\b.*)",
    ]

    for pattern in date_then_time_patterns:
        merged = try_merge_date_time_pattern(
            phrase,
            pattern,
            date_group="head",
            time_group="tail",
            args=args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if merged is not None:
            return merged

    for pattern in time_then_date_patterns:
        merged = try_merge_time_date_pattern(
            phrase,
            pattern,
            time_group="time",
            date_group="date",
            args=args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if merged is not None:
            return merged

    return None


def _parse_natural_date_strict_impl(date, *args, **kwargs):
    timezone_aware = kwargs.pop("timezone_aware", False)
    fuzzy = kwargs.pop("fuzzy", False)
    matched_text = kwargs.pop("matched_text", None)

    if not isinstance(date, str):
        return None

    raw_text = date.strip()
    phrase = date.lower().strip()
    phrase = phrase.strip(" \t\r\n,.;:!?()[]{}\"'")
    if phrase == "":
        return attach_parse_metadata(
            get_reference_date(),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
            ),
        )

    infinity_candidate = finalize_infinity_candidate(
        phrase,
        raw_text=raw_text,
        matched_text=matched_text,
        fuzzy=fuzzy,
    )
    if infinity_candidate is not None:
        return infinity_candidate

    phrase, tzinfo = normalize_parse_input(raw_text)

    infinity_candidate = finalize_infinity_candidate(
        phrase,
        raw_text=raw_text,
        matched_text=matched_text,
        fuzzy=fuzzy,
    )
    if infinity_candidate is not None:
        return infinity_candidate

    direct_candidates = collect_direct_parse_candidates(
        phrase, *args, timezone_aware=timezone_aware, **kwargs
    )
    event_phrase = phrase
    normalized_phrase = replace_short_words(phrase)
    phrase = normalized_phrase
    part_of_day_date = get_part_of_day_phrase_date(
        phrase, *args, timezone_aware=timezone_aware
    )

    registered_anchor_date, registered_anchor_definition = resolve_registered_anchor(
        event_phrase,
        *args,
        families={"event", "structural"},
        timezone_aware=timezone_aware,
        **kwargs,
    )
    part_of_day_stage = finalize_part_of_day_stage(
        part_of_day_date,
        normalized_phrase=normalized_phrase,
        tzinfo=tzinfo,
        timezone_aware=timezone_aware,
        raw_text=raw_text,
        matched_text=matched_text,
        fuzzy=fuzzy,
    )
    if part_of_day_stage is not None:
        return part_of_day_stage

    direct_instant_candidates = (
        (
            direct_candidates["simple_clock_instant_date"],
            {"semantic_kind": "instant", "representative_granularity": "minute"},
        ),
        (
            direct_candidates["simple_numeric_instant_date"],
            {"semantic_kind": "instant", "representative_granularity": "minute"},
        ),
        (direct_candidates["clock_date"], {}),
        (direct_candidates["compound_clock_date"], {}),
    )
    finalized_direct_instant = finalize_first_matching_candidate(
        direct_instant_candidates,
        tzinfo=tzinfo,
        timezone_aware=timezone_aware,
        raw_text=raw_text,
        matched_text=matched_text,
        normalized_phrase=normalized_phrase,
        fuzzy=fuzzy,
    )
    if finalized_direct_instant is not None:
        return finalized_direct_instant

    composed_stage = finalize_composed_stage(
        direct_candidates["composed_date_time"],
        registered_anchor_definition,
        normalized_phrase=normalized_phrase,
        tzinfo=tzinfo,
        timezone_aware=timezone_aware,
        raw_text=raw_text,
        matched_text=matched_text,
        fuzzy=fuzzy,
    )
    if composed_stage is not None:
        return composed_stage

    anchor_candidates = (
        (
            registered_anchor_date,
            get_anchor_metadata_overrides(registered_anchor_definition),
        ),
    )
    finalized_anchor = finalize_first_matching_candidate(
        anchor_candidates,
        tzinfo=tzinfo,
        timezone_aware=timezone_aware,
        raw_text=raw_text,
        matched_text=matched_text,
        normalized_phrase=normalized_phrase,
        fuzzy=fuzzy,
    )
    if finalized_anchor is not None:
        return finalized_anchor

    simple_candidates = (
        (
            direct_candidates["leap_year_offset_date"],
            {
                "semantic_kind": "relative_offset",
                "representative_granularity": "year",
            },
        ),
        (
            direct_candidates["ordinal_time_coordinate_date"],
            {
                "semantic_kind": "instant",
                "representative_granularity": "second",
            },
        ),
        (
            direct_candidates["compact_offset_date"],
            {
                "semantic_kind": "relative_offset",
                "representative_granularity": "minute",
            },
        ),
        (
            direct_candidates["counted_holiday_date"],
            {
                "semantic_kind": "relative_offset",
                "representative_granularity": "day",
            },
        ),
        (
            direct_candidates["relative_month_day_date"],
            {"semantic_kind": "date", "representative_granularity": "day"},
        ),
        (
            direct_candidates["counted_weekday_date"],
            {
                "semantic_kind": "relative_offset",
                "representative_granularity": "week",
            },
        ),
        (
            direct_candidates["counted_month_date"],
            {
                "semantic_kind": "relative_offset",
                "representative_granularity": "year",
            },
        ),
        (
            direct_candidates["weekday_and_date_date"],
            {"semantic_kind": "date", "representative_granularity": "day"},
        ),
        (
            direct_candidates["weekday_in_month_date"],
            {"semantic_kind": "date", "representative_granularity": "day"},
        ),
        (
            direct_candidates["counted_weekday_anchor_date"],
            {"semantic_kind": "date", "representative_granularity": "day"},
        ),
        (
            direct_candidates["recurring_weekday_date"],
            {"semantic_kind": "recurring", "representative_granularity": "week"},
        ),
        (
            direct_candidates["recurring_schedule_date"],
            {
                "semantic_kind": "recurring",
                "representative_granularity": get_recurring_schedule_granularity(
                    normalized_phrase
                ),
            },
        ),
        (
            direct_candidates["weekday_anchor_date"],
            {"semantic_kind": "date", "representative_granularity": "day"},
        ),
        (
            direct_candidates["ordinal_weekday_anchor_date"],
            {"semantic_kind": "date", "representative_granularity": "day"},
        ),
        (
            direct_candidates["add_subtract_date"],
            {
                "semantic_kind": "relative_offset",
                "representative_granularity": "day",
            },
        ),
        (direct_candidates["ordinal_month_year_date"], {}),
        (
            direct_candidates["relative_period_date"],
            {"semantic_kind": "period", "representative_granularity": "day"},
        ),
        (
            direct_candidates["weekday_occurrence_period_date"],
            {"semantic_kind": "date", "representative_granularity": "day"},
        ),
        (
            direct_candidates["quarter_phrase_date"],
            {"semantic_kind": "period", "representative_granularity": "month"},
        ),
        (
            direct_candidates["month_anchor_date"],
            {"semantic_kind": "period", "representative_granularity": "day"},
        ),
        (
            direct_candidates["week_of_month_anchor_date"],
            {"semantic_kind": "date", "representative_granularity": "day"},
        ),
        (
            direct_candidates["leap_year_anchor_date"],
            {"semantic_kind": "date", "representative_granularity": "day"},
        ),
        (direct_candidates["business_date"], {}),
        (direct_candidates["sleep_date"], {}),
        (direct_candidates["anchor_offset_date"], {}),
        (direct_candidates["year_wrapped_date"], {}),
    )
    finalized_family_candidate = finalize_first_matching_candidate(
        simple_candidates,
        tzinfo=tzinfo,
        timezone_aware=timezone_aware,
        raw_text=raw_text,
        matched_text=matched_text,
        normalized_phrase=normalized_phrase,
        fuzzy=fuzzy,
    )
    if finalized_family_candidate is not None:
        return finalized_family_candidate

    if direct_candidates["composed_date_time"] is not None and not re.match(
        r"^(?:in|on)\s+the\s+(?:morning|afternoon|evening|night)\b",
        normalized_phrase,
    ):
        return finalize_parsed_candidate(
            direct_candidates["composed_date_time"],
            tzinfo=tzinfo,
            timezone_aware=timezone_aware,
            raw_text=raw_text,
            matched_text=matched_text,
            normalized_phrase=normalized_phrase,
            fuzzy=fuzzy,
            metadata_overrides=get_composed_metadata_overrides(normalized_phrase),
        )

    finalized_tail_candidate = finalize_first_matching_candidate(
        ((part_of_day_date, {}),),
        tzinfo=tzinfo,
        timezone_aware=timezone_aware,
        raw_text=raw_text,
        matched_text=matched_text,
        normalized_phrase=normalized_phrase,
        fuzzy=fuzzy,
    )
    if finalized_tail_candidate is not None:
        return finalized_tail_candidate

    for splitter in (" at ", " @ ", " on "):
        if splitter not in phrase:
            continue

        head, tail = phrase.split(splitter, 1)
        holiday_date = get_holiday_date(head.strip())
        if holiday_date is None:
            continue

        time_phrase = f"at {tail.strip()}" if splitter.strip() != "on" else tail.strip()
        tail_date = parse_natural_date_strict(
            time_phrase,
            *args,
            timezone_aware=timezone_aware,
        )
        if tail_date is None:
            continue

        merged = apply_timezone(
            merge_date_parts(holiday_date, tail_date),
            tzinfo,
            timezone_aware=timezone_aware,
        )
        return attach_parse_metadata(
            merged,
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
            ),
        )

    if is_now(phrase):
        return finalize_parsed_candidate(
            get_reference_date(),
            tzinfo=tzinfo,
            timezone_aware=timezone_aware,
            raw_text=raw_text,
            matched_text=matched_text,
            normalized_phrase=normalized_phrase,
            fuzzy=fuzzy,
        )

    try:
        parsed = yacc.parse(phrase)
    except Exception:
        return None

    if not parsed:
        return None

    return finalize_parsed_candidate(
        parsed[0],
        tzinfo=tzinfo,
        timezone_aware=timezone_aware,
        raw_text=raw_text,
        matched_text=matched_text,
        normalized_phrase=normalized_phrase,
        fuzzy=fuzzy,
    )


def parse_natural_date_strict(date, *args, **kwargs):
    if not isinstance(date, str):
        return None

    reference = coerce_reference_date(kwargs.get("relative_to"))
    if reference is None:
        reference = get_reference_date()

    token = CURRENT_REFERENCE.set(reference)
    try:
        return _parse_natural_date_strict_impl(date, *args, **kwargs)
    finally:
        CURRENT_REFERENCE.reset(token)


def is_extraction_anchor(token, next_token=None):
    token = token.lower()
    next_token = next_token.lower() if next_token is not None else None

    if token == "for" and next_token == "ever":
        return True

    if "@" in token:
        left, _, right = token.partition("@")
        if left and right:
            return is_extraction_anchor(left, right) or is_extraction_anchor(
                right, None
            )

    if "-" in token:
        left, _, right = token.partition("-")
        if left and right:
            return is_extraction_anchor(left, right) or is_extraction_anchor(
                token.replace("-", " "), None
            )

    direct_tokens = {
        "in",
        "on",
        "at",
        "@",
        "start",
        "end",
        "close",
        "beginning",
        "noon",
        "midday",
        "midnight",
        "clock",
        "quarter",
        "mid",
        "middle",
        "late",
        "when",
        "night",
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
        "sixth",
        "seventh",
        "eighth",
        "ninth",
        "tenth",
        "eleventh",
        "twelfth",
        "thirteenth",
        "fourteenth",
        "fifteenth",
        "sixteenth",
        "seventeenth",
        "eighteenth",
        "nineteenth",
        "twentieth",
        "thirtieth",
        "hundredth",
        "hundreth",
        "penultimate",
        "now",
        "right",
        "immediately",
        "straight",
        "once",
        "asap",
        "here",
        "2day",
        "tdy",
        "2moz",
        "2moro",
        "2morro",
        "2mrw",
        "tmrw",
        "tmr",
        "tomo",
        "tomoro",
        "tmoro",
        "tmorow",
        "tomoz",
        "tonight",
        "2nite",
        "tonite",
        "tnite",
        "yday",
        "yest",
        "ystd",
        "ystrday",
        "ystrdy",
        "yestday",
        "after",
        "before",
        "b4",
        "by",
        "from",
        "on",
        "as",
        "next",
        "last",
        "this",
        "nite",
        "eob",
        "eop",
        "cob",
        "cop",
        "eom",
        "eoy",
        "coy",
        "christmas",
        "xmas",
        "easter",
        "thanksgiving",
        "halloween",
        "spring",
        "summer",
        "autumn",
        "fall",
        "winter",
        "equinox",
        "solstice",
        "vernal",
        "autumnal",
        "fiscal",
        "midweek",
        "wolf",
        "strawberry",
        "hunter's",
        "hunters",
        "supermoon",
        "blood",
        "micromoon",
        "pancake",
        "shrove",
        "labor",
        "memorial",
        "black",
        "boxing",
        "bank",
        "holiday",
        "morrow",
        "weekend",
        "weekends",
        "weekday",
        "weekdays",
        "week",
        "month",
        "y2k",
        "forever",
        "infinity",
        "eternity",
        "lunch",
        "dinner",
        "tea",
        "breakfast",
        "brunch",
        "first",
        "dawn",
        "sunrise",
        "sunset",
        "dusk",
        "twilight",
        "full",
        "blue",
        "harvest",
        "other",
        "half",
        "second-last",
        "plus",
        "minus",
        "add",
        "off",
        "valentine's",
        "valentines",
        "new",
        "st",
        "leap",
        "each",
        "every",
    }
    direct_tokens.update(RELATIVE_DAY_WORD_SET)
    direct_tokens.update(FUZZY_QUALIFIER_WORD_SET)
    days = set(WEEKDAY_NAMES).union(WEEKDAY_ALIASES.keys())
    months = set(MONTH_NAMES).union(MONTH_ALIASES.keys())
    units = {
        "year",
        "years",
        "month",
        "months",
        "week",
        "weeks",
        "fortnight",
        "fortnights",
        "day",
        "days",
        "night",
        "nights",
        "hour",
        "hours",
        "minute",
        "minutes",
        "second",
        "seconds",
        "millisecond",
        "milliseconds",
    }

    if (
        token in direct_tokens
        or token in days
        or token in months
        or token in HOLIDAY_FIRST_TOKENS
    ):
        return True

    if token == "month" and next_token in {"end", "close"}:
        return True

    if token == "t" and next_token == "minus":
        return True

    if token == "t-minus":
        return True

    if token == "as" and next_token == "of":
        return True

    if token in {"by", "from", "on"} and next_token in direct_tokens.union(days).union(
        months
    ):
        return True

    if token in {"+", "-"} and re.fullmatch(r"\d+(?:\.\d+)?", next_token or ""):
        return True

    if token in {"plus", "minus", "add", "off"} and (
        re.fullmatch(r"\d+(?:\.\d+)?", next_token or "")
        or next_token in units
        or next_token
        in {"a", "an", "one", "two", "three", "four", "five", "six", "seven"}
    ):
        return True

    if token == "take" and next_token == "away":
        return True

    if token == "give" and next_token == "or":
        return True

    if token in FUZZY_QUALIFIER_WORD_SET and (
        re.fullmatch(r"\d+(?:\.\d+)?", next_token or "")
        or next_token in units
        or next_token
        in {"a", "an", "one", "two", "three", "four", "five", "six", "seven"}
    ):
        return True

    if token in TIMEZONE_OFFSETS or build_tzinfo(token) is not None:
        return True

    if TIME_TOKEN_RE.fullmatch(token):
        return True

    if re.fullmatch(r"\d+[mhdwy]", token):
        return True

    if re.fullmatch(r"\d+(?:st|nd|rd|th)", token):
        return True

    if re.fullmatch(r"\d+(?::\d{2})?", token) and next_token in {
        "am",
        "pm",
        "oclock",
    }:
        return True

    if re.fullmatch(r"\d+(?:\.\d+)?", token) and next_token in {
        "past",
        "to",
        "before",
        "after",
    }:
        return True

    if token in {
        "a",
        "an",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
        "twenty",
        "thirty",
        "forty",
        "fifty",
    } and next_token in {"past", "to", "before", "after"}:
        return True

    if re.fullmatch(r"\d+(?:\.\d+)?", token) and next_token in units.union({"in"}):
        return True

    if re.fullmatch(r"\d+(?:\.\d+)?", token) and next_token in WEEKDAY_ALL_SET:
        return True

    if re.fullmatch(r"\d+(?:\.\d+)?", token) and next_token:
        holiday_candidate = next_token
        candidates = [holiday_candidate]
        if holiday_candidate.endswith("ies"):
            candidates.append(holiday_candidate[:-3] + "y")
        if holiday_candidate.endswith("es"):
            candidates.append(holiday_candidate[:-2])
        if holiday_candidate.endswith("s"):
            candidates.append(holiday_candidate[:-1])
        if any(
            get_registered_holiday_resolver(candidate) is not None
            for candidate in candidates
        ):
            return True

    if re.fullmatch(r"\d{4}", token) and next_token == "on":
        return True

    if token in WEEKDAY_PLURAL_SET:
        return True

    if token == "every" and next_token in WEEKDAY_NAME_SET:
        return True

    if token in CARDINAL_NUMBER_WORD_SET and next_token in units.union(
        WEEKDAY_ALL_SET
    ).union({"quarter"}):
        return True

    if token in CARDINAL_NUMBER_WORD_SET and next_token:
        holiday_candidate = next_token
        candidates = [holiday_candidate]
        if holiday_candidate.endswith("ies"):
            candidates.append(holiday_candidate[:-3] + "y")
        if holiday_candidate.endswith("es"):
            candidates.append(holiday_candidate[:-2])
        if holiday_candidate.endswith("s"):
            candidates.append(holiday_candidate[:-1])
        if any(
            get_registered_holiday_resolver(candidate) is not None
            for candidate in candidates
        ):
            return True

    if (
        token
        in {
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
        }
        or re.fullmatch(r"\d{1,2}", token)
    ) and next_token == "and":
        return True

    if token in {
        *ORDINAL_DAY_MAP.keys(),
        "hundredth",
        "penultimate",
    } and next_token in units.union(days).union({"day", "week", "month", "year"}):
        return True

    if token == "the" and (
        next_token
        in {
            "other",
            "night",
            "nite",
            "day",
            "clock",
            "month",
            "start",
            "end",
            "beginning",
            "close",
            "bank",
            "morrow",
            "next",
            "mid",
            "middle",
            "last",
            "first",
            "full",
            "blue",
            "harvest",
            "spring",
            "summer",
            "autumn",
            "fall",
            "winter",
            "wolf",
            "strawberry",
            "hunter's",
            "hunters",
            "second",
            "third",
            "fourth",
            "fifth",
            "sixth",
            "seventh",
            "eighth",
            "ninth",
            "tenth",
            "eleventh",
            "twelfth",
            "thirteenth",
            "fourteenth",
            "fifteenth",
            "sixteenth",
            "seventeenth",
            "eighteenth",
            "nineteenth",
            "twentieth",
            "thirtieth",
            "hundredth",
            "hundreth",
            "twelth",
            "penultimate",
            "second-last",
            *WEEKDAY_NAME_SET,
        }
        or (next_token is not None and re.fullmatch(r"\d+(?:st|nd|rd|th)", next_token))
    ):
        return True

    if token == "day" and next_token in {"before", "after"}:
        return True

    if token == "night" and next_token in {"before", "b4"}:
        return True

    if token == "few" and next_token in units:
        return True

    if token == "several" and next_token in units.union({"leap"}):
        return True

    if token == "couple" and next_token == "of":
        return True

    if re.fullmatch(r"\d{4}", token) and next_token in {
        "at",
        "on",
        "the",
        "next",
        "last",
        "first",
        "second",
        "third",
        *MONTH_NAME_SET,
    }:
        return True

    return False


def extract_dates(text, *args, max_tokens=24, **kwargs):
    matches = []
    tokens = list(EXTRACTION_TOKEN_RE.finditer(text))
    parse_kwargs = dict(kwargs)
    timezone_aware = parse_kwargs.pop("timezone_aware", False)
    relative_to = parse_kwargs.pop("relative_to", None)
    reference = coerce_reference_date(relative_to)
    if reference is not None:
        parse_kwargs["relative_to"] = reference

    token = CURRENT_REFERENCE.set(reference)
    try:
        i = 0
        while i < len(tokens):
            token_text = tokens[i].group(0)
            next_token = tokens[i + 1].group(0) if i + 1 < len(tokens) else None

            if not is_extraction_anchor(token_text, next_token):
                i += 1
                continue

            best_match = None
            max_j = min(len(tokens), i + max_tokens)

            for j in range(max_j, i, -1):
                candidate = text[tokens[i].start() : tokens[j - 1].end()]
                parsed = parse_natural_date_strict(
                    candidate,
                    *args,
                    timezone_aware=timezone_aware,
                    fuzzy=True,
                    matched_text=candidate.strip(" \t\r\n,.;:!?()[]{}\"'"),
                    **parse_kwargs,
                )
                if parsed is None:
                    continue

                best_match = DateMatch(
                    text=candidate.strip(" \t\r\n,.;:!?()[]{}\"'"),
                    start=tokens[i].start(),
                    end=tokens[j - 1].end(),
                    date=parsed,
                )
                break

            if best_match is None:
                i += 1
                continue

            matches.append(best_match)

            while i < len(tokens) and tokens[i].start() < best_match.end:
                i += 1
    finally:
        CURRENT_REFERENCE.reset(token)

    return matches


def get_date(date, *args, **kwargs):
    relative_to = kwargs.pop("relative_to", None)
    reference = coerce_reference_date(relative_to)
    parse_kwargs = dict(kwargs)
    if reference is not None:
        parse_kwargs["relative_to"] = reference
    token = CURRENT_REFERENCE.set(reference)
    try:
        parsed = parse_natural_date_strict(date, *args, **parse_kwargs)
        if parsed is not None:
            return parsed
        kwargs.pop("timezone_aware", None)
    except TypeError as e:
        # if debug raise the error
        if DEBUG:
            raise e
        fallback = stDate(date, *args, **kwargs)
        return attach_parse_metadata(
            fallback,
            build_parse_metadata(
                str(date),
                str(date),
                str(date).strip().lower(),
                exact=False,
                fuzzy=False,
                used_dateutil=True,
            ),
        )
    except Exception as e:
        if DEBUG:
            raise e
        fallback = stDate()
        return attach_parse_metadata(
            fallback,
            build_parse_metadata(
                str(date),
                str(date),
                str(date).strip().lower(),
                exact=False,
                fuzzy=False,
                used_dateutil=True,
            ),
        )
    finally:
        CURRENT_REFERENCE.reset(token)
    fallback = stDate(date, *args, **kwargs)
    return attach_parse_metadata(
        fallback,
        build_parse_metadata(
            str(date),
            str(date),
            str(date).strip().lower(),
            exact=False,
            fuzzy=False,
            used_dateutil=True,
        ),
    )


def until(*args, from_=None, to=None, **kwargs):
    used_default_start = from_ is None and "from" not in kwargs
    from_, to = resolve_duration_arguments(*args, from_=from_, to=to, kwargs=kwargs)
    start = coerce_value_date(from_, argument_name="from_", default_now=True)
    end = coerce_value_date(to, argument_name="to")
    if used_default_start:
        end = maybe_roll_until_target_forward(end, start)
    return format_duration_string(start.to_datetime(), end.to_datetime())


def after(*args, from_=None, to=None, **kwargs):
    from_, to = resolve_duration_arguments(*args, from_=from_, to=to, kwargs=kwargs)
    start = coerce_value_date(from_, argument_name="from_")
    end = coerce_value_date(to, argument_name="to")
    return format_duration_string(start.to_datetime(), end.to_datetime())


def is_before(a, b):
    first = coerce_value_date(a, argument_name="a")
    second = coerce_value_date(b, argument_name="b")
    return compare_date_values(first, second) < 0


def is_after(a, b):
    first = coerce_value_date(a, argument_name="a")
    second = coerce_value_date(b, argument_name="b")
    return compare_date_values(first, second) > 0


def is_same_day(a, b):
    first = coerce_value_date(a, argument_name="a")
    second = coerce_value_date(b, argument_name="b")
    if getattr(first, "is_infinite", False) or getattr(second, "is_infinite", False):
        return compare_date_values(first, second) == 0
    return comparable_datetime(first).date() == comparable_datetime(second).date()


def is_same_time(a, b):
    first = coerce_value_date(a, argument_name="a")
    second = coerce_value_date(b, argument_name="b")
    if getattr(first, "is_infinite", False) or getattr(second, "is_infinite", False):
        return compare_date_values(first, second) == 0
    first_dt = comparable_datetime(first)
    second_dt = comparable_datetime(second)
    return (
        first_dt.hour,
        first_dt.minute,
        first_dt.second,
    ) == (
        second_dt.hour,
        second_dt.minute,
        second_dt.second,
    )


def Date(date=None, *args, length: int = None, **kwargs):
    """
    # if 2nd argument is a string its a date range
    # if a length is passed, and there's a range, then we need to split it
    # by filling and array with dates between the range
    # print(date, args)
    if len(args) > 0 and isinstance(args[0], str):
        first_date = get_date(date, *args, **kwargs)
        second_date = get_date(args[0], *args, **kwargs)
        if length:
            # return [first_date + i for i in range(length)]
            # get the difference between the two dates
            diff = second_date.get_time() - first_date.get_time()
            # divide by the length
            diff = diff / length
            # populate an array with the dates
            dates = []
            dates.append(first_date)
            for i in range(length-2):
                d = Date('now')
                d.set_seconds(d.seconds + (diff/1000))
                dates.append(d)
            dates.append(second_date)
            return dates
        return [first_date, second_date]
    """
    extract = kwargs.pop("extract", False)
    if extract:
        return extract_dates(date, *args, **kwargs)
    return get_date(date, *args, **kwargs)
