__version__ = "0.0.6"
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
import datetime
import contextvars
import math
import re
import warnings
from dataclasses import dataclass

import ply.lex as lex
import ply.yacc as yacc
from dateutil.easter import easter
from dateutil.relativedelta import relativedelta

from stringtime.date import Date as stDate
from stringtime.holidays import (
    HOLIDAY_FIRST_TOKENS,
    builtin_holiday_alias_count,
    builtin_holiday_definition_count,
    clear_custom_holidays,
    get_registered_holiday_resolver,
    register_holiday,
    register_holiday_date,
    register_holiday_dates,
    register_holidays,
)

DEBUG = False
try:
    ERR_ICN = "\U0000274C"
    WARN_ICN = "\U000026A0"
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

NORMALIZATION_ALIASES = {
    "the end of time": "forever",
    "end of time": "forever",
    "for eternity": "forever",
    "eternity": "forever",
    "2moro": "tomorrow",
    "2morro": "tomorrow",
    "2moz": "tomorrow",
    "2mrw": "tomorrow",
    "tmro": "tomorrow",
    "tmmrw": "tomorrow",
    "tomoro": "tomorrow",
    "tmoro": "tomorrow",
    "tmorow": "tomorrow",
    "tomorow": "tomorrow",
    "hr ": "hour",
    "hrs": "hour",
    "min ": "minute",
    "mins": "minute",
    "sec ": "second",
    "secs": "second",
    "dy": "day",
    "dys": "day",
    "mos": "month",
    "mnth": "month",
    "mnths": "month",
    "wk": "week",
    "wks": "week",
    "yr": "year",
    "yrs": "year",
    "oclock": "",
    "o'clock": "",
    "febuary": "february",
    "feburary": "february",
    "twelth": "twelfth",
    "janurary": "january",
    "januray": "january",
    "ocotber": "october",
    "decemeber": "december",
    "harveset": "harvest",
    "wensday": "wednesday",
    "wednsday": "wednesday",
    "thurday": "thursday",
    "thrusday": "thursday",
    "mid-summer": "midsummer",
}

NORMALIZATION_WORD_ALIASES = {
    "2day": "today",
    "tdy": "today",
    "b4": "before",
    "xmas": "christmas",
    "hallowe'en": "halloween",
    "tmrw": "tomorrow",
    "tmr": "tomorrow",
    "tomo": "tomorrow",
    "tomoz": "tomorrow",
    "mrng": "morning",
    "frdy": "friday",
    "wknd": "weekend",
    "yday": "yesterday",
    "yest": "yesterday",
    "ystd": "yesterday",
    "ystrday": "yesterday",
    "ystrdy": "yesterday",
    "yestday": "yesterday",
    "2nite": "tonight",
    "tonite": "tonight",
    "tnite": "tonight",
    "nite": "night",
    "midnite": "midnight",
    "arvo": "afternoon",
    "eob": "end of business",
    "cob": "end of business",
    "cop": "end of play",
    "mid summer": "midsummer",
    "eom": "end of month",
    "eoy": "close of year",
    "coy": "close of year",
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
    match = re.search(
        r"\s+(z|utc|gmt|est|edt|cst|cdt|mst|mdt|pst|pdt|bst|cet|cest|eet|eest|ist|jst|aest|aedt|acst|acdt|awst|(?:utc|gmt)[+-]\d{1,2}(?::?\d{2})?)$",
        phrase,
    )
    if match is None:
        return phrase, None

    tzinfo = build_tzinfo(match.group(1))
    if tzinfo is None:
        return phrase, None

    return phrase[: match.start()].strip(), tzinfo


def apply_timezone(date_obj, tzinfo, timezone_aware=False):
    if tzinfo is None or not timezone_aware:
        return date_obj

    date_obj._date = date_obj._date.replace(tzinfo=tzinfo)
    return date_obj


def normalize_timezone_phrase(phrase):
    return re.sub(
        r"^((?:next|last)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|today|tomorrow|yesterday)\s+(\d{1,2}(?::\d{2})?(?:am|pm)?)$",
        r"\1 at \2",
        phrase,
    )


def normalize_phrase(phrase):
    def normalize_24h_time(match):
        hour = int(match.group("hour"))
        minute = int(match.group("minute"))
        meridiem = "am" if hour < 12 else "pm"
        normalized_hour = hour % 12
        if normalized_hour == 0:
            normalized_hour = 12
        if minute == 0:
            return f"{normalized_hour}{meridiem}"
        return f"{normalized_hour}:{minute:02d}{meridiem}"

    phrase = re.sub(r"(?<=\w)@(?=\w)", " @ ", phrase)
    phrase = re.sub(
        r"\b(?P<hour>\d{1,2})\s+(?P<meridiem>am|pm)\b",
        r"\g<hour>\g<meridiem>",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(r"(?<!\w)a\.m\.(?!\w)", "am", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"(?<!\w)p\.m\.(?!\w)", "pm", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bante meridiem\b", "am", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bpost meridiem\b", "pm", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bhundreth\b", "hundredth", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bthe end of month\b", "end of month", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bmonth end\b", "end of month", phrase, flags=re.IGNORECASE)
    phrase = re.sub(
        r"\bthe start of the month of (?P<month>january|february|march|april|may|june|july|august|september|october|november|december)\b",
        r"the start of \g<month>",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bnew year's\b(?!\s+day)",
        "new year's day",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(r"\bthe bank holiday\b", "bank holiday", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bbank holiday monday\b", "bank holiday", phrase, flags=re.IGNORECASE)
    phrase = re.sub(
        r"\bthe night before christmas\b", "christmas eve", phrase, flags=re.IGNORECASE
    )
    phrase = re.sub(r"\beop today\b", "eop", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bthe close of year\b", "close of year", phrase, flags=re.IGNORECASE)
    phrase = re.sub(
        r"\bthe start of next quarter\b", "start of next quarter", phrase, flags=re.IGNORECASE
    )
    phrase = re.sub(
        r"\bend of business by tomorrow\b",
        "end of business tomorrow",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(r"\b(?:in|on)\s+the\s+morrow\b", "tomorrow", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bthe\s+morrow\b", "tomorrow", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\blunch\s+time\b", "lunchtime", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bdinner\s+time\b", "dinnertime", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\btea\s+time\b", "teatime", phrase, flags=re.IGNORECASE)
    phrase = re.sub(
        r"\b(?:about|around)\s+(lunchtime|dinnertime|teatime)\b",
        r"\1",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bmidnight\s+(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"midnight on \g<weekday>",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bthe\s+beginning\s+of\s+(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)\b",
        r"the start of \g<month>",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bbeginning\s+of\s+(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)\b",
        r"start of \g<month>",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(r"\bfirst light\b", "dawn", phrase, flags=re.IGNORECASE)
    phrase = re.sub(
        r"^at\s+(dawn|sunrise|sunset|dusk|twilight)\s+(.+)$",
        r"\1 \2",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\b(?P<hour>[01]?\d|2[0-3]):(?P<minute>\d{2})\b(?!:\d{2})(?!\s*(?:am|pm)\b)",
        normalize_24h_time,
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bthe\s+start\s+of\s+(q[1-4](?:\s+\d{4})?)\b",
        r"start of \1",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bmiddle\s+of\s+(q[1-4](?:\s+\d{4})?)\b",
        r"mid \1",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bmid\s+of\s+(q[1-4](?:\s+\d{4})?)\b",
        r"mid \1",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bstart\s+of\s+the\s+(q[1-4](?:\s+\d{4})?)\b",
        r"start of \1",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bnext\s+month\s+on\s+(?P<day>\d+)(?P<suffix>st|nd|rd|th)\b",
        r"\g<day>\g<suffix> of next month",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bnext\s+month\s+on\s+(?P<day>first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\b",
        r"next month on the \g<day>",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\b(?P<day>\d{1,2}(?:st|nd|rd|th))\s+in\s+last\s+month\b",
        r"\g<day> of last month",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bthe\s+second-last\s+day\s+of\s+the\s+month\b",
        "the second to last day of the month",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bthe\s+penultimate\s+day\s+of\s+the\s+month\b",
        "the second to last day of the month",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bsecond-last\s+day\s+of\s+the\s+month\b",
        "second to last day of the month",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bpenultimate\s+day\s+of\s+the\s+month\b",
        "second to last day of the month",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bsecond\s+to\s+last\s+day\s+in\s+the\s+month\b",
        "second to last day of the month",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bmidnight\s+on\s+the\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"midnight on \1",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\b(?P<offset>.+?)\s+(from|after)\s+the\s+(?P<anchor>next\s+.+)\b",
        lambda match: f"{match.group('offset')} {match.group(2)} {match.group('anchor')}",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\b(?P<offset>.+?)\s+before\s+the\s+(midnight|noon|midday)\b",
        lambda match: f"{match.group('offset')} before {match.group(2)}",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\b(?P<offset>.+?)\s+after\s+the\s+(xmas|christmas)\b",
        lambda match: f"{match.group('offset')} after {match.group(2)}",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"^at\s+(noon|midnight|midday)\s+(today|tomorrow|yesterday)$",
        r"\2 at \1",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"^at\s+(.+?\b(?:utc(?:[+-]\d+)?|pst|est|cst|mst|gmt))\s+(today|tomorrow|yesterday)$",
        r"\2 at \1",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"^by\s+(?=(?:today|tomorrow|yesterday|next|last|this|noon|midnight|midday|monday|tuesday|wednesday|thursday|friday|saturday|sunday|january|february|march|april|may|june|july|august|september|october|november|december)\b)",
        "",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"^as\s+of\s+(?=(?:today|tomorrow|yesterday|next|last|this|noon|midnight|midday|monday|tuesday|wednesday|thursday|friday|saturday|sunday|january|february|march|april|may|june|july|august|september|october|november|december)\b)",
        "",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"^on\s+(?=(?:the\s+)?(?:next|last|this|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}(?:st|nd|rd|th)|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\b)",
        "",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"^in\s+(?=(?:january|february|march|april|may|june|july|august|september|october|november|december)\b)",
        "",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"^at\s+(?=(?:noon|midnight|midday|lunchtime|dinnertime|teatime|\d{1,2}(?::\d{2})?(?:am|pm)?)\b)",
        "",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"^from\s+(?=(?:today|tomorrow|yesterday|next|last|this|monday|tuesday|wednesday|thursday|friday|saturday|sunday|january|february|march|april|may|june|july|august|september|october|november|december)\b)",
        "",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(r"^from\s+the\s+(next|last)\b", r"\1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"^on\s+the\s+(next|last)\b", r"\1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"^the\s+(next|last)\b", r"\1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(
        r"\bthe\s+start\s+of\s+the\s+next\s+quarter\b",
        "start of next quarter",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"\bt[\s-]*minus\s+(?P<rest>.+)$",
        lambda match: f"{match.group('rest')} ago",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(r"\b(noon|midnight|midday)ish\b", r"\1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(
        r"\b(?:about|around)\s+(?=(?:\d{1,2}(?::\d{2})?(?:am|pm)?|\d{1,2}ish|noon|midnight|midday|dawn|sunrise|sunset|dusk|twilight)\b)",
        "",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(r"\btonight\b", "today night", phrase, flags=re.IGNORECASE)
    phrase = re.sub(
        r"\bclose of business\b", "end of business", phrase, flags=re.IGNORECASE
    )
    phrase = re.sub(r"\bclose of play\b", "end of play", phrase, flags=re.IGNORECASE)
    phrase = re.sub(
        r"\b(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s+in\s+the\s+morning\b",
        lambda match: (
            f"{int(match.group('hour')) % 12}:{match.group('minute')}am"
            if match.group("minute") is not None
            else f"{int(match.group('hour')) % 12}am"
        ),
        phrase,
    )
    phrase = normalize_timezone_phrase(phrase)
    phrase = re.sub(
        r"^(in\s+.+?)\s+from now$",
        r"\1",
        phrase,
    )
    return phrase


def apply_word_aliases(phrase):
    for source, target in NORMALIZATION_WORD_ALIASES.items():
        phrase = re.sub(rf"\b{re.escape(source)}\b", target, phrase)
    return phrase


def apply_literal_aliases(phrase):
    for source, target in NORMALIZATION_ALIASES.items():
        phrase = phrase.replace(source, target)
    return phrase


@dataclass
class DateMatch:
    text: str
    start: int
    end: int
    date: stDate


@dataclass
class ParseMetadata:
    input_text: str
    matched_text: str
    normalized_text: str
    exact: bool
    fuzzy: bool
    used_dateutil: bool
    semantic_kind: str
    representative_granularity: str


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
    if getattr(value, "is_infinite", False):
        raise ValueError("Cannot format a bounded duration against infinity")
    if value.tzinfo is None:
        return value.replace(microsecond=0)
    return value.astimezone(datetime.timezone.utc).replace(tzinfo=None, microsecond=0)


def comparable_datetime(value):
    if getattr(value, "is_infinite", False):
        return value
    return normalize_duration_datetime(value.to_datetime())


def compare_date_values(first, second):
    if getattr(first, "is_infinite", False) or getattr(second, "is_infinite", False):
        if getattr(first, "is_infinite", False) and getattr(second, "is_infinite", False):
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
    if kwargs is None:
        kwargs = {}

    kwargs = dict(kwargs)
    if "from" in kwargs and from_ is None:
        from_ = kwargs.pop("from")
    if "to" in kwargs and to is None:
        to = kwargs.pop("to")
    if kwargs:
        unexpected = ", ".join(sorted(kwargs))
        raise TypeError(f"unexpected keyword argument(s): {unexpected}")

    remaining = list(args)
    if remaining and from_ is None and to is None:
        to = remaining.pop(0)
    elif remaining and from_ is None:
        from_ = remaining.pop(0)

    if remaining and to is None:
        to = remaining.pop(0)

    if remaining:
        raise TypeError("too many positional arguments")

    return from_, to


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
):
    if semantic_kind is None or representative_granularity is None:
        semantic_kind, representative_granularity = infer_phrase_semantics(
            normalized_text
        )
    return ParseMetadata(
        input_text=input_text,
        matched_text=matched_text,
        normalized_text=normalized_text,
        exact=exact,
        fuzzy=fuzzy,
        used_dateutil=used_dateutil,
        semantic_kind=semantic_kind,
        representative_granularity=representative_granularity,
    )


def infer_phrase_semantics(phrase):
    phrase = (phrase or "").strip().lower()

    if phrase in {"forever", "for ever", "infinity", "∞"}:
        return "infinity", "unbounded"

    if phrase == "" or is_now(phrase):
        return "instant", "second"

    if (
        phrase.startswith(("end of", "start of", "close of", "first day of", "last day of"))
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
        r"(?:on\s+)?(?:(?:every)\s+)?(?:mondays|tuesdays|wednesdays|thursdays|fridays|saturdays|sundays)|every\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        phrase,
    ):
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

    if phrase in {"noon", "midday", "chinese dentist", "cowboy time"} or phrase.startswith(
        ("quarter past", "quarter to", "half past", "half ")
    ):
        return "instant", "minute"

    if re.search(
        r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow|yesterday)\b",
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

    recurring_with_time_patterns = (
        r"(?:on\s+)?(?:mondays|tuesdays|wednesdays|thursdays|fridays|saturdays|sundays)\s+(?:at|@)\s+.+",
        r"every\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?:at|@)\s+.+",
    )
    for pattern in recurring_with_time_patterns:
        if re.fullmatch(pattern, phrase):
            return {
                "semantic_kind": "recurring",
                "representative_granularity": "week",
            }

    return {}


# -----------------------------------------------------------------------------

tokens = (
    "WORD_NUMBER",
    "DECIMAL",
    "NUMBER",
    "YEAR",
    "DAY",
    "MONTH",
    "TIME",
    "PHRASE",
    "PAST_PHRASE",
    "PLUS",
    "MINUS",
    # AND,
    # SPACE,
    "YESTERDAY",
    "TOMORROW",
    "AFTER_TOMORROW",
    "BEFORE_YESTERDAY",
    "TODAY",
    "AT",
    "ON",
    "OF",
    "THE",
    "DATE_END",
    "AM",
    "PM",
    "A",
    "COLON",
    "AND",
    "HALF",
    # "DATESTAMP",
)


def t_COLON(t):
    r":"
    return t


def t_AND(t):
    r"and"
    return t


def t_HALF(t):
    r"half"
    return t


def t_A(t):
    r"\ba\b"
    t.value = 1
    t.type = "NUMBER"
    return t


def t_DATE_END(t):
    r"st\b|nd\b|rd\b|th\b"
    # print('date-end detected!', t.value)
    return t


# def t_SPACE(t):
#     r"\s+"
#     # ignore whitespace
#     pass


def t_PLUS(t):
    r"\+"
    t.value = "+"
    return t


def t_MINUS(t):
    r"-"
    t.value = "-"
    return t


def t_DECIMAL(t):
    r"\d+\.\d+"
    t.value = float(t.value)
    return t


def t_NUMBER(t):
    r"\d+"
    t.value = int(t.value)
    return t


# \d{4}-\d{2}-\d{2}|\d{4}-\d{2}|\d{4}|\d{2}-\d{2}
# strings in the form: 2020-12-24 or 2020/12/24 or 2020|12|24
# strings in the form: 2020-12 or 12/24 or 2020|12
# def t_DATESTAMP(t):
#     r"\d{4}-\d{2}-\d{2}|\d{4}-\d{2}|\d{4}|\d{2}-\d{2}|\d{4}/\d{2}/\d{2}|\d{4}/\d{2}|\d{4}|\d{2}/\d{2}|\d{4}|\d{2}|\d{2}|\d{4}|\d{2}|\d{4}|\d{2}|\d{2}"
#     print('datestamp detected!', t.value)
#     return t


# TODO - test for all numbers
def t_WORD_NUMBER(t):
    r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety"
    # convert to a normal number
    # print('word number detected!', t.value)

    number_to_word = {
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
    t.value = number_to_word[t.value]

    # number_to_word2 = {
    #     "first": 1,
    #     "second": 2,
    #     "third": 3,
    #     "fourth": 4,
    #     "fifth": 5,
    #     "sixth": 6,
    #     "seventh": 7,
    #     "eighth": 8,
    #     "ninth": 9,
    #     "tenth": 10,
    #     "eleventh": 11,
    #     "twelfth": 12,
    #     "thirteenth": 13,
    #     "fourteenth": 14,
    #     "fifteenth": 15,
    #     "sixteenth": 16,
    #     "seventeenth": 17,
    #     "eighteenth": 18,
    #     "nineteenth": 19,
    #     "twentieth": 20,
    #     "thirtieth": 30,
    #     "fortieth": 40,
    #     "fiftieth": 50,
    #     "sixtieth": 60,
    #     "seventieth": 70,
    #     "eightieth": 80,
    #     "ninetieth": 90,
    # }
    # t.value = number_to_word2[t.value]
    # return t

    return t


t_DAY = r"monday|tuesday|wednesday|thursday|friday|saturday|sunday"

t_MONTH = r"january|february|march|april|may|june|july|august|september|october|november|december"


def t_TIME(t):
    r"years|months|weeks|days|hours|minutes|seconds|milliseconds|year|month|week|day|hour|minute|second|millisecond"
    # print('time detected!', t.value)
    if t.value.endswith("s"):
        t.value = t.value[:-1]
        # TODO - set a flag to indicate this is a plural

    return t


# partial phrases that increment time
t_PHRASE = r"today\ plus|today\ add|now\ plus|now\ add|add|added|plus|from\ now|time|in\ the\ future|into\ the\ future|away|away\ from\ now|hence|past\ now|after\ now|beyond\ this\ current\ moment|in\ an|in\ a|in|next|an"

# partial phrases that decrement time
t_PAST_PHRASE = r"today\ minus|today\ take|today\ take\ away|now\ minus|now\ take|now\ take\ away|minus|take\ away|off|ago|in\ the\ past|the\ past|just\ been|before\ now|before\ this\ moment|before\ this\ current\ moment|before|last"


t_YESTERDAY = r"yesterday"
t_TOMORROW = r"tomorrow|2moro|2morro"
# t_AFTER_TOMORROW = r"after\ tomorrow|after\ 2moro|after\ 2morro"
def t_AFTER_TOMORROW(t):
    r"after\ tomorrow|after\ 2moro|after\ 2morro"
    return t


# t_BEFORE_YESTERDAY = r"before\ yesterday|other\ day"
def t_BEFORE_YESTERDAY(t):
    r"before\ yesterday|other\ day"
    # print('before yesterday detected!', t.value)
    return t


t_TODAY = r"today"


def t_AT(t):
    r"at|@"
    return t


t_ON = r"on"
t_OF = r"of"


def t_AM(t):
    r"am"
    # print('am:morning detected!', t.value)
    return t


def t_PM(t):
    r"pm"
    # print('pm:afternoon detected!', t.value)
    return t


def t_THE(t):
    r"the"
    return t


t_YEAR = r"\d{4}"
# t_DAYS = r"\d{1,2}"
# t_MONTHS = r"\d{1,2}"
# t_TIMES = r"\d{1,2}"
# t_PHRASES = r"\d{1,2}"
t_ignore = " \t"

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


# When parsing starts, try to make a "date_object" because it's
# the name on left-hand side of the first p_* function definition.
# The first rule is empty because I let the empty string be valid
def p_date_object(p):
    """
    date_object :
    date_object : date_list
    """
    if len(p) == 1:
        # the empty string means there are no adjustment. so NOW
        p[0] = []
    else:
        p[0] = p[1]


def p_date_list(p):
    "date_list : date_list date"
    p[0] = p[1] + [p[2]]


def p_date(p):
    """
    date_list : date
    date_list : date_past
    date_list : in
    date_list : adder
    date_list : remover
    date_list : date_yesterday
    date_list : date_2moro
    date_list : date_day
    date_list : date_end
    date_list : date_or
    date_list : date_month_relative
    date_list : date_before_yesterday
    date_list : date_after_tomorrow
    date_list : date_twice
    date_list : timestamp
    date_list : timestamp_adpt
    """
    p[0] = [p[1]]


# def p_datestamp(p):
#     """
#     datestamp : NUMBER MINUS NUMBER
#     datestamp : NUMBER MINUS NUMBER MINUS NUMBER
#     """
#     if len(p) == 4:
#         p[0] = stDate.create_date_with_offsets(
#             year=p[1], month=p[2], day=p[3]
#         )


def p_timestamp(p):
    """
    timestamp : NUMBER COLON NUMBER
    timestamp : NUMBER COLON NUMBER COLON NUMBER
    """
    if len(p) == 4:
        params = {"hour": p[1], "minute": p[3], "second": 0}
    elif len(p) == 6:
        params = {"hour": p[1], "minute": p[3], "second": p[5]}
    p[0] = DateFactory.create_date(**params)


# saves having multiple redefinitions inside timestamp
def p_timestamp_adapter(p):
    """
    timestamp_adpt : timestamp AM
    timestamp_adpt : timestamp PM
    timestamp_adpt : AT timestamp
    timestamp_adpt : AT timestamp PM
    timestamp_adpt : AT timestamp AM
    """
    if len(p) == 3:
        if p[1] == "at":
            p[0] = p[2]
        else:
            if p[2] == "pm":
                p[1].set_hours(p[1].get_hours() + 12)
                p[0] = p[1]
            if p[2] == "am":
                # print('its am!')
                p[0] = p[1]
    elif len(p) == 4:
        if p[1] == "at":
            if p[3] == "pm" and p[2].get_hours() < 12:
                p[2].set_hours(p[2].get_hours() + 12)
            elif p[3] == "am" and p[2].get_hours() == 12:
                p[2].set_hours(0)
            p[0] = p[2]
    # p[0] = p[2]


# TIME - not strictly valid. but should do a single unit of that time
# NUMBER TIME - not strictly valid. but should work
# TIME PHRASE -  again not really valid. but should do a single unit of that time
def p_single_date(p):
    """
    date : NUMBER
    date : DECIMAL
    date : WORD_NUMBER
    date : AT NUMBER
    date : AT WORD_NUMBER
    date : TIME
    date : NUMBER TIME
    date : DECIMAL TIME
    date : NUMBER AM
    date : NUMBER PM
    date : AT NUMBER AM
    date : AT NUMBER PM
    date : WORD_NUMBER TIME
    date : PHRASE TIME
    date : TIME PHRASE
    date : NUMBER TIME PHRASE
    date : DECIMAL TIME PHRASE
    date : WORD_NUMBER TIME PHRASE
    date : PHRASE TIME PHRASE
    date : PHRASE TIME AND NUMBER TIME
    date : PHRASE TIME AND WORD_NUMBER TIME
    date : WORD_NUMBER AND NUMBER HALF TIME
    date : WORD_NUMBER TIME AND NUMBER HALF
    date : WORD_NUMBER TIME AND NUMBER HALF TIME
    date : PHRASE TIME AND NUMBER HALF
    date : NUMBER TIME AND NUMBER TIME PHRASE
    date : NUMBER TIME AND WORD_NUMBER TIME PHRASE
    date : WORD_NUMBER TIME AND NUMBER TIME PHRASE
    date : WORD_NUMBER TIME AND WORD_NUMBER TIME PHRASE
    date : WORD_NUMBER AND NUMBER HALF TIME PHRASE
    date : WORD_NUMBER TIME AND NUMBER HALF PHRASE
    date : WORD_NUMBER TIME AND NUMBER HALF TIME PHRASE
    date : PHRASE TIME AND NUMBER HALF PHRASE
    """
    if len(p) == 2:
        params = {
            "hour": p[1],
            "minute": 0,
            "second": 0,
        }
        p[0] = DateFactory.create_date(**params)
    elif len(p) == 3:
        if isinstance(p[1], (int, float)):
            # 5-pm
            if p[2] == "am":
                if p[1] == 12:
                    p[1] = 0
                params = {
                    "hour": p[1],
                    "minute": 0,
                    "second": 0,
                }
                p[0] = DateFactory.create_date(**params)
            elif p[2] == "pm":
                if p[1] < 12:
                    p[1] += 12
                params = {
                    "hour": p[1],
                    "minute": 0,
                    "second": 0,
                }
                p[0] = DateFactory.create_date(**params)
            else:  # number time
                if isinstance(p[1], float):
                    p[0] = DateFactory.create_date_with_fractional_offset(p[2], p[1])
                else:
                    params = {p[2]: p[1]}
                    p[0] = DateFactory.create_date_with_offsets(**params)  # '3 days'
            return
        if isinstance(p[2], str):
            params = {
                p[2]: 1
            }  # TODO - prepend offset_ to the key. passing 1 as no number
            p[0] = DateFactory.create_date_with_offsets(**params)  # 'a minute'
        else:
            params = {
                "hour": p[2],
                "minute": 0,
                "second": 0,
            }
            p[0] = DateFactory.create_date(**params)  # 'at 4'

    elif len(p) == 4:
        # print("at-5-pm", p[1], p[2], p[3])
        if p[1] == "at" or p[1] == "@":
            # at-3-am
            if p[3] == "am":
                if p[2] == 12:
                    p[2] = 0
                params = {
                    "hour": p[2],
                    "minute": 0,
                    "second": 0,
                }
                p[0] = DateFactory.create_date(**params)
            elif p[3] == "pm":
                if p[2] < 12:
                    p[2] += 12
                params = {
                    "hour": p[2],
                    "minute": 0,
                    "second": 0,
                }
                p[0] = DateFactory.create_date(**params)
            return
        if p[1] == "an":
            p[1] = 1  # if no number is passed, assume 1
        if isinstance(p[1], float):
            p[0] = DateFactory.create_date_with_fractional_offset(p[2], p[1])
        else:
            params = {p[2]: p[1]}  # TODO - prepend offset_ to the key
            p[0] = DateFactory.create_date_with_offsets(**params)
    elif len(p) == 5 and p[4] == "half":
        whole = 1 if p[1] in ["in", "in a", "in an", "an"] else p[1]
        p[0] = DateFactory.create_date_with_half_offset(p[2], whole=whole)
    elif len(p) == 5 and p[3] == "half":
        p[0] = DateFactory.create_date_with_half_offset(p[4], whole=p[1])
    elif len(p) == 6 and p[5] == "half":
        whole = 1 if p[1] in ["in", "in a", "in an", "an"] else p[1]
        p[0] = DateFactory.create_date_with_half_offset(p[2], whole=whole)
    elif len(p) == 6 and p[4] == "half":
        p[0] = DateFactory.create_date_with_half_offset(p[2], whole=p[1])
    elif len(p) == 7 and p[5] == "half":
        whole = 1 if p[1] in ["in", "in a", "in an", "an"] else p[1]
        sign = -1 if p[6] in ["ago", "last", "minus", "before now", "in the past", "the past"] else 1
        p[0] = DateFactory.create_date_with_half_offset(p[2], whole=whole, sign=sign)
    elif len(p) == 8 and p[4] == "half":
        sign = -1 if p[7] in ["ago", "last", "minus", "before now", "in the past", "the past"] else 1
        p[0] = DateFactory.create_date_with_half_offset(p[2], whole=p[1], sign=sign)
    elif len(p) == 6:
        if p[1] == "in" or p[1] == "in a" or p[1] == "in an" or p[1] == "an":
            params = {p[2]: 1, p[5]: p[4]}
        else:
            params = {p[2]: p[1], p[5]: p[4]}
        p[0] = DateFactory.create_date_with_offsets(**params)
    elif len(p) == 7:
        params = {p[2]: p[1], p[5]: p[4]}
        if p[6] in ["ago", "last", "minus", "before now", "in the past", "the past"]:
            params = {key: -value for key, value in params.items()}
        p[0] = DateFactory.create_date_with_offsets(**params)


# combines rules test
def p_twice(p):
    """
    date_twice : date date
    date_twice : date_day date
    date_twice : date date_day
    date_twice : date_month_relative date
    date_twice : date_day timestamp
    date_twice : date_day timestamp_adpt
    date_twice : timestamp date_day
    date_twice : timestamp_adpt date_day
    """
    # print("Parse 2 phrases!", p[1], p[2])
    # i.e. '(2 days time) (at 4pm)'
    # i.e. date_day date = 'wednesday @ 5pm'

    p[0] = merge_date_parts(p[1], p[2])


# in : PHRASE WORD_NUMBER TIME?? not getting converted
def p_single_date_in(p):
    """
    in : PHRASE NUMBER TIME
    in : PHRASE DECIMAL TIME
    in : PHRASE WORD_NUMBER TIME
    """
    if len(p) == 2:
        p[0] = DateFactory(p[1], 1)
    elif len(p) == 3:
        p[0] = DateFactory(p[1], p[2])
    elif len(p) == 4:
        if isinstance(p[2], float):
            p[0] = DateFactory.create_date_with_fractional_offset(p[3], p[2])
        else:
            params = {p[3]: p[2]}  # TODO - prepend offset_ to the key
            p[0] = DateFactory.create_date_with_offsets(**params)


def p_compound_date_in(p):
    """
    in : PHRASE NUMBER TIME AND NUMBER TIME
    in : PHRASE WORD_NUMBER TIME AND NUMBER TIME
    in : PHRASE NUMBER TIME AND WORD_NUMBER TIME
    in : PHRASE WORD_NUMBER TIME AND WORD_NUMBER TIME
    """
    params = {p[3]: p[2], p[6]: p[5]}
    p[0] = DateFactory.create_date_with_offsets(**params)


def p_single_date_plus(p):
    """
    adder : PLUS NUMBER TIME
    adder : PLUS WORD_NUMBER TIME
    """
    if len(p) == 2:
        p[0] = DateFactory(p[1], 1)
    elif len(p) == 3:
        p[0] = DateFactory(p[1], p[2])
    elif len(p) == 4:
        params = {p[3]: p[2]}  # TODO - prepend offset_ to the key
        p[0] = DateFactory.create_date_with_offsets(**params)


def p_compound_date_plus(p):
    """
    adder : PLUS NUMBER TIME AND NUMBER TIME
    adder : PLUS WORD_NUMBER TIME AND NUMBER TIME
    adder : PLUS NUMBER TIME AND WORD_NUMBER TIME
    adder : PLUS WORD_NUMBER TIME AND WORD_NUMBER TIME
    """
    params = {p[3]: p[2], p[6]: p[5]}
    p[0] = DateFactory.create_date_with_offsets(**params)


def p_single_date_minus(p):
    """
    remover : MINUS NUMBER TIME
    remover : MINUS WORD_NUMBER TIME
    """
    if len(p) == 2:
        p[0] = DateFactory(p[1], 1)
    elif len(p) == 3:
        p[0] = DateFactory(p[1], p[2])
    elif len(p) == 4:
        params = {p[3]: -p[2]}  # TODO - prepend offset_ to the key
        p[0] = DateFactory.create_date_with_offsets(**params)


def p_compound_date_minus(p):
    """
    remover : MINUS NUMBER TIME AND NUMBER TIME
    remover : MINUS WORD_NUMBER TIME AND NUMBER TIME
    remover : MINUS NUMBER TIME AND WORD_NUMBER TIME
    remover : MINUS WORD_NUMBER TIME AND WORD_NUMBER TIME
    """
    params = {p[3]: -p[2], p[6]: -p[5]}
    p[0] = DateFactory.create_date_with_offsets(**params)


# WORD_NUMBER TIME & WORD_NUMBER TIME PHRASE
def p_single_date_past(p):
    """
    date_past : NUMBER TIME PAST_PHRASE
    date_past : DECIMAL TIME PAST_PHRASE
    date_past : WORD_NUMBER TIME PAST_PHRASE
    """
    if isinstance(p[1], float):
        p[0] = DateFactory.create_date_with_fractional_offset(p[2], p[1], sign=-1)
    else:
        params = {p[2]: -p[1]}  # TODO - prepend offset_ to the key
        p[0] = DateFactory.create_date_with_offsets(**params)


def p_compound_date_past(p):
    """
    date_past : NUMBER TIME AND NUMBER TIME PAST_PHRASE
    date_past : WORD_NUMBER TIME AND NUMBER TIME PAST_PHRASE
    date_past : NUMBER TIME AND WORD_NUMBER TIME PAST_PHRASE
    date_past : WORD_NUMBER TIME AND WORD_NUMBER TIME PAST_PHRASE
    """
    params = {p[2]: -p[1], p[5]: -p[4]}
    p[0] = DateFactory.create_date_with_offsets(**params)


def p_half_date_past(p):
    """
    date_past : WORD_NUMBER TIME AND NUMBER HALF PAST_PHRASE
    date_past : PHRASE TIME AND NUMBER HALF PAST_PHRASE
    """
    whole = 1 if p[1] in ["in", "in a", "in an", "an"] else p[1]
    p[0] = DateFactory.create_date_with_half_offset(p[2], whole=whole, sign=-1)


def p_single_date_yesterday(p):
    """
    date_yesterday : YESTERDAY
    date_yesterday : YESTERDAY AT NUMBER
    date_yesterday : YESTERDAY AT WORD_NUMBER
    date_yesterday : YESTERDAY AT NUMBER AM
    date_yesterday : YESTERDAY AT NUMBER PM
    """
    if len(p) == 2:
        params = {"day": -1}
        p[0] = DateFactory.create_date_with_offsets(**params)
    if len(p) == 4:
        params = {
            "day": get_reference_date().get_date() - 1,
            "hour": p[3],
            "minute": 0,
            "second": 0,
        }
        p[0] = DateFactory.create_date(**params)
    if len(p) == 5:
        hour = p[3]
        if p[4] == "pm" and hour < 12:
            hour += 12
        elif p[4] == "am" and hour == 12:
            hour = 0
        params = {
            "day": get_reference_date().get_date() - 1,
            "hour": hour,
            "minute": 0,
            "second": 0,
        }
        p[0] = DateFactory.create_date(**params)


def p_single_date_2moro(p):
    """
    date_2moro : TOMORROW
    date_2moro : TOMORROW AT NUMBER
    date_2moro : TOMORROW AT WORD_NUMBER
    date_2moro : TOMORROW AT NUMBER AM
    date_2moro : TOMORROW AT NUMBER PM
    """
    if len(p) == 2:
        params = {"day": 1}
        p[0] = DateFactory.create_date_with_offsets(**params)
    if len(p) == 4:
        params = {
            "day": get_reference_date().get_date() + 1,
            "hour": p[3],
            "minute": 0,
            "second": 0,
        }
        p[0] = DateFactory.create_date(**params)
    if len(p) == 5:
        hour = p[3]
        if p[4] == "pm" and hour < 12:
            hour += 12
        elif p[4] == "am" and hour == 12:
            hour = 0
        params = {
            "day": get_reference_date().get_date() + 1,
            "hour": hour,
            "minute": 0,
            "second": 0,
        }
        p[0] = DateFactory.create_date(**params)


def p_single_date_day(p):
    """
    date_day : DAY
    date_day : ON DAY
    date_day : PHRASE DAY
    date_day : PAST_PHRASE DAY
    """
    if len(p) == 2:
        day_to_find = p[1]
        d = get_reference_date()
        # go forward each day until it matches
        while day_to_find.lower() != d.get_day(to_string=True).lower():
            d.set_date(d.get_date() + 1)

        p[0] = d
    if len(p) == 3:
        day_to_find = p[2]
        d = get_reference_date()
        now = get_reference_date()
        # go forward each day until it matches
        while day_to_find.lower() != d.get_day(to_string=True).lower():
            if p[1] == "last":
                if d.get_date() == 1:
                    d.set_date(d.get_date() - 2)
                else:
                    d.set_date(d.get_date() - 1)
            elif p[1] == "next" or p[1] == "on":
                d.set_date(d.get_date() + 1)
            # else:
            #     print("an infinite loop?")

        if (
            p[1] == "next"
            and now.get_day(to_string=True).lower() == day_to_find.lower()
        ):
            d.set_date(d.get_date() + 7)
        elif (
            p[1] == "last"
            and now.get_day(to_string=True).lower() == day_to_find.lower()
        ):
            d.set_date(d.get_date() - 7)

        p[0] = d


def p_this_or_next_period(p):
    """
    date_or : PAST_PHRASE TIME
    """
    if len(p) == 3:
        d = get_reference_date()
        if p[1] == "last":
            if p[2] == "week":
                d.set_date(d.get_date() - 7)
            elif p[2] == "year":
                d.set_year(d.get_year() - 1)
            elif p[2] == "month":
                d.set_month(d.get_month() - 1)
            # elif p[2] == "century":
            #     d.set_year(d.get_year() - 100)
        elif p[1] == "next":
            d.set_date(d.get_date() + 1)
        p[0] = d


def p_before_yesterday(p):
    """
    date_before_yesterday : BEFORE_YESTERDAY
    date_before_yesterday : THE BEFORE_YESTERDAY
    date_before_yesterday : THE TIME BEFORE_YESTERDAY
    """
    d = get_reference_date()
    d.set_date(d.get_date() - 2)
    p[0] = d


def p_after_tomorrow(p):
    """
    date_after_tomorrow : AFTER_TOMORROW
    date_after_tomorrow : THE TIME AFTER_TOMORROW
    """
    d = get_reference_date()
    d.set_date(d.get_date() + 2)
    p[0] = d


# date_end : THE NUMBER ?? allow
def p_single_date_end(p):
    """
    date_end : NUMBER DATE_END
    date_end : THE NUMBER DATE_END
    date_end : MONTH NUMBER DATE_END
    date_end : NUMBER DATE_END OF MONTH
    date_end : ON THE NUMBER DATE_END
    date_end : MONTH THE NUMBER DATE_END
    date_end : THE NUMBER DATE_END OF MONTH
    """
    if len(p) == 3:
        d = get_reference_date()
        d.set_date(p[1])
        p[0] = d
    if len(p) == 4:
        # print('p-:', p[1], p[2], p[3])
        d = get_reference_date()
        d.set_date(p[2])
        if p[1] == "the":  # the-2-nd
            d.set_date(p[2])
        else:  # january-14-th
            m = d.get_month_index_by_name(p[1])
            d.set_month(m)
            d.set_date(p[2])
        p[0] = d
    if len(p) == 5:
        # print('p--:', p[1], p[2], p[3], p[4])
        d = get_reference_date()
        if p[1] == "on":  # on-the-1-st
            d.set_date(p[3])
        elif p[3] == "of":  # 18-th-of-march
            m = d.get_month_index_by_name(p[4])
            d.set_month(m)
            d.set_date(p[1])
        else:  # april-the-1-st
            m = d.get_month_index_by_name(p[1])
            d.set_month(m)
            d.set_date(p[3])
        p[0] = d
    if len(p) == 6:
        d = get_reference_date()  # the-18-th-of-january
        m = d.get_month_index_by_name(p[5])
        d.set_month(m)
        d.set_date(p[2])
        p[0] = d


def p_month_relative_date(p):
    """
    date_month_relative : THE NUMBER DATE_END OF PAST_PHRASE TIME
    date_month_relative : NUMBER DATE_END OF PAST_PHRASE TIME
    date_month_relative : THE NUMBER DATE_END OF PHRASE TIME
    date_month_relative : NUMBER DATE_END OF PHRASE TIME
    date_month_relative : PAST_PHRASE TIME ON THE NUMBER DATE_END
    date_month_relative : PHRASE TIME ON THE NUMBER DATE_END
    """
    d = get_reference_date()

    if len(p) == 6:
        day = p[1]
        direction = p[4]
    elif len(p) == 7:
        if p[1] == "the":
            day = p[2]
            direction = p[5]
        else:
            direction = p[1]
            day = p[5]
    else:
        direction = p[1]
        day = p[5]

    if direction == "last":
        d.set_month(d.get_month() - 1)
    elif direction == "next":
        d.set_month(d.get_month() + 1)

    d.set_date(day)
    p[0] = d


# t_TODAY = r"today"
# "SAME TIME ON" # TODO----


def p_error(p):
    raise TypeError("unknown text at %r" % (p.value,))


yacc.yacc()


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
        r"\b(?P<number>\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)\s+and\s+a\s+half\s+(?P<unit>years?|months?|weeks?|days?|hours?|minutes?|seconds?)\b",
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
        r"\b(?P<day_phrase>(?:(?:last|next)\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|today|tomorrow|yesterday)\s+(?:at|@)\s+(?P<time_phrase>\d{1,2}:\d{2}(?:\s?(?:am|pm))?)\b",
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

    phrase = re.sub(r"\bmon\b", "monday", phrase)
    phrase = re.sub(r"\btues\b", "tuesday", phrase)
    phrase = re.sub(r"\btue\b", "tuesday", phrase)
    phrase = re.sub(r"\bwed\b", "wednesday", phrase)
    phrase = re.sub(r"\bweds\b", "wednesday", phrase)
    phrase = re.sub(r"\bthurs\b", "thursday", phrase)
    phrase = re.sub(r"\bthur\b", "thursday", phrase)
    phrase = re.sub(r"\bthu\b", "thursday", phrase)
    phrase = re.sub(r"\bfri\b", "friday", phrase)
    phrase = re.sub(r"\bsat\b", "saturday", phrase)
    phrase = re.sub(r"\bsun\b", "sunday", phrase)

    phrase = re.sub(r"\bjan\b", "january", phrase)
    phrase = re.sub(r"\bfeb\b", "february", phrase)
    phrase = re.sub(r"\bmar\b", "march", phrase)
    phrase = re.sub(r"\bapr\b", "april", phrase)
    phrase = re.sub(r"\bmay\b", "may", phrase)
    phrase = re.sub(r"\bjun\b", "june", phrase)
    phrase = re.sub(r"\bjul\b", "july", phrase)
    phrase = re.sub(r"\baug\b", "august", phrase)
    phrase = re.sub(r"\bsept\b", "september", phrase)
    phrase = re.sub(r"\bsep\b", "september", phrase)
    phrase = re.sub(r"\boct\b", "october", phrase)
    phrase = re.sub(r"\bnov\b", "november", phrase)
    phrase = re.sub(r"\bdec\b", "december", phrase)

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
    period = period.strip()
    reference = get_reference_date()
    reference_year = reference.get_year()
    reference_month = reference.get_month() + 1

    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    ordinal_months = {
        "1st": 1,
        "2nd": 2,
        "3rd": 3,
        "4th": 4,
        "5th": 5,
        "6th": 6,
        "7th": 7,
        "8th": 8,
        "9th": 9,
        "10th": 10,
        "11th": 11,
        "12th": 12,
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
    }

    if period in months:
        return reference_year, months[period]

    relative_named_month_match = re.fullmatch(
        r"(?P<relation>last|next|this)\s+(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)",
        period,
    )
    if relative_named_month_match is not None:
        month = months[relative_named_month_match.group("month")]
        relation = relative_named_month_match.group("relation")
        year = reference_year

        if relation == "this":
            return year, month
        if relation == "next":
            if month <= reference_month:
                year += 1
            return year, month
        if month >= reference_month:
            year -= 1
        return year, month

    month_year_match = re.fullmatch(
        r"(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)\s+(?P<year>\d{4})",
        period,
    )
    if month_year_match is not None:
        return int(month_year_match.group("year")), months[month_year_match.group("month")]

    if period in {"month", "the month", "this month"}:
        return reference_year, reference_month

    ordinal_month_match = re.fullmatch(
        r"(?:the\s+)?(?P<month>1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\s+month(?:\s+(?P<year>\d{4}))?",
        period,
    )
    if ordinal_month_match is not None:
        year = (
            int(ordinal_month_match.group("year"))
            if ordinal_month_match.group("year") is not None
            else reference_year
        )
        return year, ordinal_months[ordinal_month_match.group("month")]

    if period == "next month":
        d = get_reference_date()
        d.set_month(d.get_month() + 1)
        return d.get_year(), d.get_month() + 1

    if period == "last month":
        d = get_reference_date()
        d.set_month(d.get_month() - 1)
        return d.get_year(), d.get_month() + 1

    if re.fullmatch(r"\d{4}", period):
        return int(period), 1

    return None


def resolve_year_phrase(period):
    period = period.strip()
    reference = get_reference_date()
    current_century_start = (reference.get_year() // 100) * 100

    explicit_year_match = re.fullmatch(r"(?:the\s+)?year\s+(?P<year>\d{4})", period)
    if explicit_year_match is not None:
        return int(explicit_year_match.group("year"))

    if period in {"year", "the year", "this year"}:
        return reference.get_year()
    if period == "next year":
        return reference.get_year() + 1
    if period == "last year":
        return reference.get_year() - 1
    if period in {"century", "the century", "this century"}:
        return current_century_start
    if period == "next century":
        return current_century_start + 100
    if period == "last century":
        return current_century_start - 100
    if re.fullmatch(r"\d{4}", period):
        return int(period)
    return None


def resolve_quarter_year(quarter_phrase):
    quarter_phrase = quarter_phrase.strip()
    reference = get_reference_date()

    match = re.fullmatch(r"q([1-4])(?:\s+(\d{4}))?", quarter_phrase)
    if match is not None:
        quarter = int(match.group(1))
        year = int(match.group(2)) if match.group(2) else reference.get_year()
        return year, quarter

    if quarter_phrase in {"this quarter", "the quarter"}:
        month = reference.get_month() + 1
        quarter = ((month - 1) // 3) + 1
        return reference.get_year(), quarter

    if quarter_phrase == "next quarter":
        d = get_reference_date()
        d.set_month(d.get_month() + 3)
        month = d.get_month() + 1
        quarter = ((month - 1) // 3) + 1
        return d.get_year(), quarter

    if quarter_phrase == "last quarter":
        d = get_reference_date()
        d.set_month(d.get_month() - 3)
        month = d.get_month() + 1
        quarter = ((month - 1) // 3) + 1
        return d.get_year(), quarter

    return None


def get_ordinal_weekday_date(phrase):
    phrase = re.sub(r"^(?:on|in)\s+", "", phrase)
    pattern = (
        r"(?:the\s+)?(?P<occurrence>first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th|last|penultimate)\s+"
        r"(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?:in|of)\s+(?P<period>.+)"
    )
    match = re.fullmatch(pattern, phrase)
    if match is None:
        year_prefixed = re.fullmatch(r"(?P<year>\d{4})\s+on\s+(?P<rest>.+)", phrase)
        if year_prefixed is not None:
            rest_match = re.fullmatch(pattern, year_prefixed.group("rest"))
            if rest_match is not None:
                period_text = rest_match.group("period")
                if not re.search(r"\b\d{4}\b", period_text):
                    phrase = (
                        f"{rest_match.group('occurrence')} {rest_match.group('weekday')} "
                        f"of {period_text} {year_prefixed.group('year')}"
                    )
                    match = re.fullmatch(pattern, phrase)
    if match is None:
        return None

    occurrence = match.group("occurrence")
    weekday_name = match.group("weekday")
    period = match.group("period")
    year_match = re.fullmatch(r"\d{4}", period)

    weekday = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }[weekday_name]

    resolved_year = resolve_year_phrase(period)

    if year_match is not None or resolved_year is not None:
        year = int(period) if year_match is not None else resolved_year
        if occurrence in {"first", "1st"}:
            date_value = nth_weekday_of_year(year, weekday, 1)
        elif occurrence in {"second", "2nd"}:
            date_value = nth_weekday_of_year(year, weekday, 2)
        elif occurrence in {"third", "3rd"}:
            date_value = nth_weekday_of_year(year, weekday, 3)
        elif occurrence in {"fourth", "4th"}:
            date_value = nth_weekday_of_year(year, weekday, 4)
        elif occurrence in {"fifth", "5th"}:
            date_value = nth_weekday_of_year(year, weekday, 5)
        elif occurrence == "last":
            date_value = last_weekday_of_year(year, weekday)
        else:
            date_value = penultimate_weekday_of_year(year, weekday)
    else:
        resolved = resolve_period_year_month(period)
        if resolved is None:
            anchor_date = parse_anchor_date(period)
            if anchor_date is None:
                return None
            year, month = anchor_date.get_year(), anchor_date.get_month() + 1
        else:
            year, month = resolved
        if occurrence in {"first", "1st"}:
            date_value = nth_weekday_of_month(year, month, weekday, 1)
        elif occurrence in {"second", "2nd"}:
            date_value = nth_weekday_of_month(year, month, weekday, 2)
        elif occurrence in {"third", "3rd"}:
            date_value = nth_weekday_of_month(year, month, weekday, 3)
        elif occurrence in {"fourth", "4th"}:
            date_value = nth_weekday_of_month(year, month, weekday, 4)
        elif occurrence in {"fifth", "5th"}:
            date_value = nth_weekday_of_month(year, month, weekday, 5)
        elif occurrence == "last":
            date_value = last_weekday_of_month(year, month, weekday)
        else:
            date_value = penultimate_weekday_of_month(year, month, weekday)

    d = get_reference_date()
    d.set_fullyear(date_value.year)
    d.set_month(date_value.month - 1)
    d.set_date(date_value.day)
    return d


def get_weekday_occurrence_period_date(phrase):
    pattern = (
        r"(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+"
        r"(?:the\s+)?(?P<occurrence>1st|2nd|3rd|4th|5th|first|second|third|fourth|fifth)\s+"
        r"of\s+(?P<period>.+)"
    )
    match = re.fullmatch(pattern, phrase)
    if match is None:
        return None

    occurrence_lookup = {
        "1st": 1,
        "2nd": 2,
        "3rd": 3,
        "4th": 4,
        "5th": 5,
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5,
    }
    weekday_lookup = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    resolved = resolve_period_year_month(match.group("period"))
    if resolved is None:
        return None

    year, month = resolved
    date_value = nth_weekday_of_month(
        year,
        month,
        weekday_lookup[match.group("weekday")],
        occurrence_lookup[match.group("occurrence")],
    )
    d = get_reference_date()
    d.set_fullyear(date_value.year)
    d.set_month(date_value.month - 1)
    d.set_date(date_value.day)
    return d


def get_ordinal_weekday_anchor_date(phrase, *args, timezone_aware=False, **kwargs):
    pattern = (
        r"(?:the\s+)?(?P<occurrence>first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th|last|penultimate)\s+"
        r"(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+"
        r"(?P<direction>before|after)\s+(?P<anchor>.+)"
    )
    match = re.fullmatch(pattern, phrase)
    if match is None:
        return None

    occurrence = match.group("occurrence")
    weekday_name = match.group("weekday")
    direction = match.group("direction")
    anchor_text = match.group("anchor").strip()

    anchor_date = parse_anchor_date(
        anchor_text,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if anchor_date is None:
        return None

    occurrence_count = {
        "first": 1,
        "1st": 1,
        "last": 1,
        "second": 2,
        "2nd": 2,
        "third": 3,
        "3rd": 3,
        "fourth": 4,
        "4th": 4,
        "fifth": 5,
        "5th": 5,
        "penultimate": 2,
    }[occurrence]
    weekday = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }[weekday_name]

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
        r"(?:the\s+)?(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+in\s+(?P<period>.+)",
        phrase,
    )
    if match is None:
        return None

    normalized_period = replace_short_words(match.group("period"))
    resolved = resolve_period_year_month(normalized_period)
    if resolved is None:
        return None

    year, month = resolved
    weekday_lookup = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    target_weekday = weekday_lookup[match.group("weekday")]

    def first_matching_weekday(target_year):
        d = build_calendar_anchor_date(target_year, month, 1)
        while d.to_datetime().weekday() != target_weekday:
            d.set_date(d.get_date() + 1)
        return d

    d = first_matching_weekday(year)
    if normalized_period in {
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
    } and d.to_datetime().replace(tzinfo=None) < get_reference_date().to_datetime().replace(tzinfo=None):
        d = first_matching_weekday(year + 1)
    return d


def get_weekday_anchor_date(phrase, *args, timezone_aware=False, **kwargs):
    match = re.fullmatch(
        r"(?:the\s+)?(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+"
        r"(?P<direction>before|after)\s+(?P<anchor>.+)",
        phrase,
    )
    if match is None:
        return None

    weekday = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }[match.group("weekday")]

    anchor_date = parse_anchor_date(
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
    match = re.fullmatch(
        r"(?:on\s+)?(?:(?:every)\s+)?(?P<weekday>mondays|tuesdays|wednesdays|thursdays|fridays|saturdays|sundays)|every\s+(?P<singular>monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        phrase,
        re.IGNORECASE,
    )
    if match is None:
        return None

    weekday_name = match.group("weekday") or match.group("singular")
    if weekday_name is None:
        return None
    if weekday_name.endswith("s"):
        weekday_name = weekday_name[:-1]

    return parse_natural_date_strict(
        weekday_name,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )


def get_ordinal_month_year_date(phrase):
    phrase = re.sub(r"^on\s+", "", phrase)
    ordinal_day_lookup = {
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
    month_lookup = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    ordinal_month_lookup = {
        "1st": 1,
        "2nd": 2,
        "3rd": 3,
        "4th": 4,
        "5th": 5,
        "6th": 6,
        "7th": 7,
        "8th": 8,
        "9th": 9,
        "10th": 10,
        "11th": 11,
        "12th": 12,
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
    }
    word_year_lookup = {
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

    def parse_year_value(raw_year):
        if re.fullmatch(r"\d{2}|\d{4}", raw_year):
            year = int(raw_year)
            if year < 100:
                return year + 1900 if year > 30 else year + 2000
            return year

        parts = raw_year.split()
        if len(parts) == 1 and parts[0] in word_year_lookup:
            year = word_year_lookup[parts[0]]
            return year + 1900 if year > 30 else year + 2000

        if (
            len(parts) == 2
            and parts[0] in word_year_lookup
            and parts[1] in word_year_lookup
            and word_year_lookup[parts[0]] >= 20
            and word_year_lookup[parts[1]] < 10
        ):
            year = word_year_lookup[parts[0]] + word_year_lookup[parts[1]]
            return year + 1900 if year > 30 else year + 2000

        return None

    year_pattern = (
        r"\d{2}|\d{4}|year|one|two|three|four|five|six|seven|eight|nine|ten|"
        r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|"
        r"nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|"
        r"(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)\s+"
        r"(?:one|two|three|four|five|six|seven|eight|nine)"
    )
    day_pattern = (
        r"\d{1,2}(?:st|nd|rd|th)?|first|second|third|fourth|fifth|sixth|"
        r"seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|"
        r"fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|"
        r"thirtieth"
    )
    month_pattern = (
        r"january|february|march|april|may|june|july|august|september|october|"
        r"november|december|1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th|"
        r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
        r"eleventh|twelfth"
    )

    relative_named_month_match = re.fullmatch(
        rf"(?P<relation>last|next|this)\s+(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)\s+(?P<day>{day_pattern})",
        phrase,
    )
    if relative_named_month_match is not None:
        raw_day = relative_named_month_match.group("day")
        ordinal_match = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?", raw_day)
        if ordinal_match is not None:
            day = int(ordinal_match.group(1))
        else:
            day = ordinal_day_lookup.get(raw_day)
            if day is None:
                return None

        month = month_lookup[relative_named_month_match.group("month")]
        relation = relative_named_month_match.group("relation")
        reference = get_reference_date()
        year = reference.get_year()
        reference_month = reference.get_month() + 1

        if relation == "next":
            if month <= reference_month:
                year += 1
        elif relation == "last":
            if month >= reference_month:
                year -= 1

        return build_calendar_anchor_date(year, month, day)

    month_first_match = re.fullmatch(
        rf"(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)\s+(?P<day>{day_pattern})(?:[,.]?\s+(?P<year>{year_pattern}))?",
        phrase,
    )
    if month_first_match is not None:
        raw_day = month_first_match.group("day")
        ordinal_match = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?", raw_day)
        if ordinal_match is not None:
            day = int(ordinal_match.group(1))
        else:
            day = ordinal_day_lookup.get(raw_day)
            if day is None:
                return None

        month = month_lookup[month_first_match.group("month")]
        raw_year = month_first_match.group("year")
        reference = get_reference_date()
        if raw_year is None:
            year = reference.get_year()
            candidate = build_calendar_anchor_date(year, month, day)
            if candidate.to_datetime().replace(tzinfo=None) < reference.to_datetime().replace(tzinfo=None):
                year += 1
        else:
            year = parse_year_value(raw_year)
            if year is None:
                return None

        return build_calendar_anchor_date(year, month, day)

    match = re.fullmatch(
        rf"(?:the\s+)?(?P<day>{day_pattern})\s+of\s+(?:the\s+)?(?P<month>{month_pattern})(?:\s+(?P<year>{year_pattern}))?",
        phrase,
    )
    if match is None:
        match = re.fullmatch(
            rf"(?:the\s+)?(?P<day>{day_pattern})\s+day\s+of\s+(?:the\s+)?(?P<month>{month_pattern})(?:\s+month)?(?:\s+of\s+(?P<year>{year_pattern}))?",
            phrase,
        )
    if match is None:
        return None

    raw_day = match.group("day")
    ordinal_match = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?", raw_day)
    if ordinal_match is not None:
        day = int(ordinal_match.group(1))
    else:
        day = ordinal_day_lookup.get(raw_day)
        if day is None:
            return None
    raw_month = match.group("month")
    month = month_lookup.get(raw_month, ordinal_month_lookup.get(raw_month))
    if month is None:
        return None

    raw_year = match.group("year")
    if raw_year is None or raw_year == "year":
        year = get_reference_date().get_year()
    else:
        year = parse_year_value(raw_year)
        if year is None:
            return None

    return build_calendar_anchor_date(year, month, day)


def get_quarter_phrase_date(phrase):
    reference = get_reference_date()

    match = re.fullmatch(r"(start|end)\s+of\s+(q[1-4])(?:\s+(\d{4}))?", phrase)
    if match is not None:
        quarter_phrase = match.group(2)
        if match.group(3):
            quarter_phrase = f"{quarter_phrase} {match.group(3)}"
        year, quarter = resolve_quarter_year(quarter_phrase)
        start_month = quarter_start_month(quarter)
        d = clone_date(reference)
        d.set_fullyear(year)
        d.set_month(start_month - 1)
        d.set_date(1)
        if match.group(1) == "end":
            d.set_month(start_month + 2 - 1)
            last_day = stDate.get_month_length(start_month + 2, year)
            d.set_date(last_day)
        return d

    match = re.fullmatch(r"mid\s+(q[1-4])(?:\s+(\d{4}))?", phrase)
    if match is not None:
        quarter_phrase = match.group(1)
        if match.group(2):
            quarter_phrase = f"{quarter_phrase} {match.group(2)}"
        year, quarter = resolve_quarter_year(quarter_phrase)
        start_month = quarter_start_month(quarter)
        d = clone_date(reference)
        d.set_fullyear(year)
        d.set_month(start_month)
        d.set_date(15)
        return d

    match = re.fullmatch(r"(first|last)\s+day\s+of\s+(this|next|last)\s+quarter", phrase)
    if match is not None:
        year, quarter = resolve_quarter_year(f"{match.group(2)} quarter")
        start_month = quarter_start_month(quarter)
        d = clone_date(reference)
        d.set_fullyear(year)
        if match.group(1) == "first":
            d.set_month(start_month - 1)
            d.set_date(1)
        else:
            end_month = start_month + 2
            d.set_month(end_month - 1)
            d.set_date(stDate.get_month_length(end_month, year))
        return d

    return None


def get_weekday_occurrence_period_phrase_date(phrase):
    match = re.fullmatch(
        r"(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?:the\s+)?(?P<occurrence>1st|2nd|3rd|4th|5th|first|second|third|fourth|fifth)\s+of\s+(?P<period>.+)",
        phrase,
    )
    if match is None:
        return None

    occurrence_lookup = {
        "1st": 1,
        "2nd": 2,
        "3rd": 3,
        "4th": 4,
        "5th": 5,
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5,
    }
    weekday_lookup = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    resolved = resolve_period_year_month(match.group("period"))
    if resolved is None:
        return None

    year, month = resolved
    date_value = nth_weekday_of_month(
        year,
        month,
        weekday_lookup[match.group("weekday")],
        occurrence_lookup[match.group("occurrence")],
    )
    d = get_reference_date()
    d.set_fullyear(date_value.year)
    d.set_month(date_value.month - 1)
    d.set_date(date_value.day)
    return d


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
        mid_year = start_year if season != "winter" or mid_month != 1 else start_year + 1
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
        moons = get_moon_phase_datetimes_for_month(search_year, target_month, "full moon")
        candidates.extend(moons[:1])

    if relation == "last":
        previous = [candidate for candidate in candidates if candidate < reference_dt]
        return date_from_datetime(max(previous)) if previous else None

    upcoming = [candidate for candidate in candidates if candidate > reference_dt]
    return date_from_datetime(min(upcoming)) if upcoming else None


def get_relative_weekday_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    match = re.fullmatch(
        r"(?:the\s+)?(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?P<relation>after next|before last|gone|past)",
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
        r"(?:the\s+)?(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+and\s+(?P<date>.+)",
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

    weekday_lookup = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    if date_part.to_datetime().weekday() != weekday_lookup[match.group("weekday")]:
        return None
    return date_part


def get_counted_weekday_phrase_date(phrase):
    match = re.fullmatch(
        r"(?:(?:in)\s+)?(?P<count>\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
        r"(?P<weekday>mondays?|tuesdays?|wednesdays?|thursdays?|fridays?|saturdays?|sundays?)\s+"
        r"(?:(?:from\s+now)|hence|ago|time)",
        phrase,
    )
    if match is None:
        return None

    count = parse_offset_number(match.group("count"))
    if count is None or count < 1:
        return None

    weekday_name = match.group("weekday")
    if weekday_name.endswith("s"):
        weekday_name = weekday_name[:-1]

    weekday = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }[weekday_name]

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

    weekday_name = match.group("weekday")
    if weekday_name.endswith("s"):
        weekday_name = weekday_name[:-1]

    weekday = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }[weekday_name]

    anchor_date = parse_anchor_date(
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
    match = re.fullmatch(
        r"(?P<relation>last|next)\s+month\s+on\s+(?:the\s+)?(?P<day>\d+(?:st|nd|rd|th)?|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|twenty first|twenty-first|twenty second|twenty-second|twenty third|twenty-third|twenty fourth|twenty-fourth|twenty fifth|twenty-fifth|twenty sixth|twenty-sixth|twenty seventh|twenty-seventh|twenty eighth|twenty-eighth|twenty ninth|twenty-ninth|thirtieth|thirty first|thirty-first)",
        phrase,
    )
    if match is None:
        return None

    day_lookup = {
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
        "twenty first": 21,
        "twenty-first": 21,
        "twenty second": 22,
        "twenty-second": 22,
        "twenty third": 23,
        "twenty-third": 23,
        "twenty fourth": 24,
        "twenty-fourth": 24,
        "twenty fifth": 25,
        "twenty-fifth": 25,
        "twenty sixth": 26,
        "twenty-sixth": 26,
        "twenty seventh": 27,
        "twenty-seventh": 27,
        "twenty eighth": 28,
        "twenty-eighth": 28,
        "twenty ninth": 29,
        "twenty-ninth": 29,
        "thirtieth": 30,
        "thirty first": 31,
        "thirty-first": 31,
    }

    raw_day = match.group("day")
    ordinal_match = re.fullmatch(r"(\d+)(?:st|nd|rd|th)?", raw_day)
    if ordinal_match is not None:
        day = int(ordinal_match.group(1))
    else:
        day = day_lookup.get(raw_day)
    if day is None:
        return None

    d = clone_date(get_reference_date())
    d.set_month(d.get_month() + (1 if match.group("relation") == "next" else -1))
    target_year = d.get_year()
    target_month = d.get_month() + 1
    if day > stDate.get_month_length(target_month, target_year):
        return None
    d.set_date(day)
    return d


def get_boundary_phrase_date(phrase):
    reference = get_reference_date()
    month_lookup = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    match = re.fullmatch(
        r"(?:the\s+)?(first|1st|last)\s+day\s+(?:of|in)\s+(?:the\s+month\s+of\s+)?(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(?P<year>\d{4}))?",
        phrase,
    )
    if match is not None:
        target_month = month_lookup[match.group("month")]
        target_year = (
            int(match.group("year")) if match.group("year") is not None else reference.get_year()
        )
        d = clone_date(reference)
        d.set_fullyear(target_year)
        d.set_month(target_month - 1)
        if match.group(1) in {"first", "1st"}:
            d.set_date(1)
        else:
            d.set_date(stDate.get_month_length(target_month, target_year))
        return d

    match = re.fullmatch(
        r"(?:on\s+)?(?:the\s+)?(?P<position>first|1st|last)\s+day\s+of\s+the\s+month\s+in\s+(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(?P<year>\d{4}))?",
        phrase,
    )
    if match is not None:
        target_month = month_lookup[match.group("month")]
        target_year = (
            int(match.group("year")) if match.group("year") is not None else reference.get_year()
        )
        d = clone_date(reference)
        d.set_fullyear(target_year)
        d.set_month(target_month - 1)
        if match.group("position") in {"first", "1st"}:
            d.set_date(1)
        else:
            d.set_date(stDate.get_month_length(target_month, target_year))
        return d

    match = re.fullmatch(
        r"(?:the\s+)?second\s+to\s+last\s+day\s+(?:of|in)\s+(?:the\s+)?(?P<period>month|year)",
        phrase,
    )
    if match is not None:
        d = clone_date(reference)
        if match.group("period") == "month":
            d.set_date(stDate.get_month_length(d.get_month() + 1, d.get_year()) - 1)
        else:
            d.set_month(11)
            d.set_date(30)
        return d

    match = re.fullmatch(
        r"(?:the\s+)?(?P<position>penultimate|second\s+to\s+last)\s+day\s+(?:of|in)\s+(?P<period>next month|last month|this month)",
        phrase,
    )
    if match is not None:
        d = clone_date(reference)
        if match.group("period") == "next month":
            d.set_month(d.get_month() + 1)
        elif match.group("period") == "last month":
            d.set_month(d.get_month() - 1)
        d.set_date(stDate.get_month_length(d.get_month() + 1, d.get_year()) - 1)
        return d

    match = re.fullmatch(
        r"(?:the\s+)?(?P<position>first|1st|last|second\s+to\s+last)\s+day\s+(?:of|in)\s+(?:the\s+)?(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(?P<year>next year|last year|this year|\d{4}))?",
        phrase,
    )
    if match is not None:
        target_month = month_lookup[match.group("month")]
        raw_year = match.group("year")
        if raw_year is None or raw_year == "this year":
            target_year = reference.get_year()
        elif raw_year == "next year":
            target_year = reference.get_year() + 1
        elif raw_year == "last year":
            target_year = reference.get_year() - 1
        else:
            target_year = int(raw_year)

        d = clone_date(reference)
        d.set_fullyear(target_year)
        d.set_month(target_month - 1)
        if match.group("position") in {"first", "1st"}:
            d.set_date(1)
        elif match.group("position") == "second to last":
            d.set_date(stDate.get_month_length(target_month, target_year) - 1)
        else:
            d.set_date(stDate.get_month_length(target_month, target_year))
        return d

    match = re.fullmatch(
        r"(?:the\s+)?(start|end|close)\s+of\s+(?:the\s+)?(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)",
        phrase,
    )
    if match is not None:
        target_month = month_lookup[match.group("month")]
        target_year = reference.get_year()
        d = clone_date(reference)
        d.set_fullyear(target_year)
        d.set_month(target_month - 1)
        if match.group(1) == "start":
            d.set_date(1)
        else:
            d.set_date(stDate.get_month_length(target_month, target_year))

        if d.to_datetime().replace(tzinfo=None) < reference.to_datetime().replace(tzinfo=None):
            target_year += 1
            d.set_fullyear(target_year)
            d.set_month(target_month - 1)
            if match.group(1) == "start":
                d.set_date(1)
            else:
                d.set_date(stDate.get_month_length(target_month, target_year))

        return d

    match = re.fullmatch(r"(start|end|close)\s+of\s+(?:the\s+)?(month|year)", phrase)
    if match is not None:
        boundary = "end" if match.group(1) == "close" else match.group(1)
        period = match.group(2)
        d = clone_date(reference)

        if period == "month":
            if boundary == "start":
                d.set_date(1)
            else:
                last_day = stDate.get_month_length(d.get_month() + 1, d.get_year())
                d.set_date(last_day)
            return d

        if boundary == "start":
            d.set_month(0)
            d.set_date(1)
        else:
            d.set_month(11)
            d.set_date(31)
        return d

    match = re.fullmatch(
        r"(?:the\s+)?(?P<position>first|1st|last)\s+day\s+of\s+(?:the\s+)?(?P<period>year|this year|next year|last year|century|this century|next century|last century|\d{4})",
        phrase,
    )
    if match is not None:
        target_year = resolve_year_phrase(match.group("period"))
        if target_year is None:
            return None

        d = clone_date(reference)
        d.set_fullyear(target_year)
        if match.group("position") in {"first", "1st"}:
            d.set_month(0)
            d.set_date(1)
        else:
            if "century" in match.group("period"):
                d.set_fullyear(target_year + 99)
            d.set_month(11)
            d.set_date(31)
        return d

    match = re.fullmatch(r"(?:the\s+)?start\s+of\s+(?:the\s+)?(this|next|last)\s+quarter", phrase)
    if match is not None:
        quarter_date = get_quarter_phrase_date(f"first day of {match.group(1)} quarter")
        if quarter_date is not None:
            return quarter_date

    return None


def get_month_anchor_date(phrase):
    month_lookup = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    ordinal_month_lookup = {
        "1st": 1,
        "2nd": 2,
        "3rd": 3,
        "4th": 4,
        "5th": 5,
        "6th": 6,
        "7th": 7,
        "8th": 8,
        "9th": 9,
        "10th": 10,
        "11th": 11,
        "12th": 12,
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
    }

    half_match = re.fullmatch(
        r"(?:the\s+)?(?P<half>first|second)\s+half\s+of\s+(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(?P<year>\d{4}))?",
        phrase,
    )
    mid_match = re.fullmatch(
        r"(?:(?:the\s+)?(?P<edge>middle)\s+of\s+|(?P<bare_mid>mid)[- ]+)(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(?P<year>\d{4}))?",
        phrase,
    )
    use_end_of_month = False
    use_middle_of_month = False
    half_day = None
    explicit_year = None
    if half_match is not None:
        target_month = month_lookup[half_match.group("month")]
        half_day = 1 if half_match.group("half") == "first" else 16
        explicit_year = (
            int(half_match.group("year")) if half_match.group("year") is not None else None
        )
    elif mid_match is not None:
        target_month = month_lookup[mid_match.group("month")]
        use_middle_of_month = True
        explicit_year = (
            int(mid_match.group("year")) if mid_match.group("year") is not None else None
        )
    else:
        match = re.fullmatch(
            r"(?:(?P<boundary>end of)\s+)?(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)(?:\s+(?P<year>\d{4}))?(?:\s+(?P<edge>finishes|ends))?",
            phrase,
        )
        if match is not None:
            target_month = month_lookup[match.group("month")]
            use_end_of_month = (
                match.group("boundary") is not None or match.group("edge") is not None
            )
            explicit_year = (
                int(match.group("year")) if match.group("year") is not None else None
            )
        else:
            ordinal_match = re.fullmatch(
                r"(?:the\s+)?(?P<month>1st|2nd|3rd|[4-9]th|10th|11th|12th|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\s+month(?:\s+of\s+the\s+year)?(?:\s+(?P<year>\d{4}))?",
                phrase,
            )
            if ordinal_match is None:
                return None
            target_month = ordinal_month_lookup[ordinal_match.group("month")]
            explicit_year = (
                int(ordinal_match.group("year"))
                if ordinal_match.group("year") is not None
                else None
            )

    reference = get_reference_date()
    reference_dt = reference.to_datetime().replace(tzinfo=None)
    year = explicit_year if explicit_year is not None else reference_dt.year
    d = clone_date(reference)

    def set_month_anchor_year(target_year):
        d.set_date(1)
        d.set_fullyear(target_year)
        d.set_month(target_month - 1)
        if use_end_of_month:
            last_day = stDate.get_month_length(target_month, target_year)
            d.set_date(last_day)
        elif half_day is not None:
            d.set_date(half_day)
        elif use_middle_of_month:
            d.set_date(15)

    set_month_anchor_year(year)
    if explicit_year is None and d.to_datetime().replace(tzinfo=None) < reference_dt:
        year += 1
        set_month_anchor_year(year)

    return d


def get_week_of_month_anchor_date(phrase):
    week_lookup = {
        "1st": 1,
        "2nd": 2,
        "3rd": 3,
        "4th": 4,
        "5th": 5,
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5,
    }

    match = re.fullmatch(
        r"(?:the\s+)?(?P<week>1st|2nd|3rd|4th|5th|first|second|third|fourth|fifth)\s+week\s+(?:of|in)\s+(?P<period>.+)",
        phrase,
    )
    if match is None:
        return None

    week_number = week_lookup[match.group("week")]
    day = ((week_number - 1) * 7) + 1
    reference = get_reference_date()
    reference_dt = reference.to_datetime().replace(tzinfo=None)
    d = clone_date(reference)

    resolved_year = resolve_year_phrase(match.group("period"))
    if resolved_year is not None:
        d.set_fullyear(resolved_year)
        d.set_month(0)
        d.set_date(day)
        return d

    resolved = resolve_period_year_month(match.group("period"))
    if resolved is None:
        return None

    year, month = resolved

    def set_week_anchor_year(target_year):
        if day > stDate.get_month_length(month, target_year):
            return False
        d.set_fullyear(target_year)
        d.set_month(month - 1)
        d.set_date(day)
        return True

    if not set_week_anchor_year(year):
        return None

    if d.to_datetime().replace(tzinfo=None) < reference_dt:
        year += 1
        if not set_week_anchor_year(year):
            return None

    return d


def get_leap_year_anchor_date(phrase):
    match = re.fullmatch(r"(?:the\s+)?(?P<which>next|last)\s+leap\s+year", phrase)
    if match is None:
        return None

    reference = get_reference_date()
    year = reference.get_year()
    step = 1 if match.group("which") == "next" else -1
    candidate = year + step

    def is_leap(test_year):
        return calendar.isleap(test_year)

    while not is_leap(candidate):
        candidate += step

    d = clone_date(reference)
    d.set_date(1)
    d.set_fullyear(candidate)
    d.set_month(0)
    return d


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
        day_number = int(ordinal_match.group(1)) if ordinal_match is not None else int(raw_day)

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
    ordinal_lookup = {
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
    ordinal_pattern = (
        r"\d+(?:st|nd|rd|th)|first|second|third|fourth|fifth|sixth|seventh|"
        r"eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|"
        r"sixteenth|seventeenth|eighteenth|nineteenth|twentieth|thirtieth"
    )

    def parse_ordinal(raw_value):
        match = re.fullmatch(r"(\d+)(?:st|nd|rd|th)", raw_value)
        if match is not None:
            return int(match.group(1))
        return ordinal_lookup.get(raw_value)

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

        anchor_date = parse_natural_date_strict(
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

        anchor_date = parse_natural_date_strict(
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
        1: {"dawn": (7, 30), "sunrise": (8, 5), "sunset": (16, 25), "dusk": (17, 0), "twilight": (17, 0)},
        2: {"dawn": (6, 45), "sunrise": (7, 20), "sunset": (17, 15), "dusk": (17, 50), "twilight": (17, 50)},
        3: {"dawn": (5, 45), "sunrise": (6, 20), "sunset": (18, 5), "dusk": (18, 40), "twilight": (18, 40)},
        4: {"dawn": (4, 45), "sunrise": (5, 25), "sunset": (19, 0), "dusk": (19, 35), "twilight": (19, 35)},
        5: {"dawn": (4, 0), "sunrise": (4, 45), "sunset": (19, 45), "dusk": (20, 20), "twilight": (20, 20)},
        6: {"dawn": (3, 30), "sunrise": (4, 15), "sunset": (20, 15), "dusk": (20, 50), "twilight": (20, 50)},
        7: {"dawn": (3, 45), "sunrise": (4, 30), "sunset": (20, 10), "dusk": (20, 45), "twilight": (20, 45)},
        8: {"dawn": (4, 30), "sunrise": (5, 15), "sunset": (19, 20), "dusk": (19, 55), "twilight": (19, 55)},
        9: {"dawn": (5, 20), "sunrise": (6, 0), "sunset": (18, 20), "dusk": (18, 55), "twilight": (18, 55)},
        10: {"dawn": (6, 10), "sunrise": (6, 45), "sunset": (17, 10), "dusk": (17, 45), "twilight": (17, 45)},
        11: {"dawn": (6, 55), "sunrise": (7, 30), "sunset": (16, 15), "dusk": (16, 50), "twilight": (16, 50)},
        12: {"dawn": (7, 25), "sunrise": (8, 0), "sunset": (15, 55), "dusk": (16, 30), "twilight": (16, 30)},
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
        previous = [candidate for candidate in candidates if candidate < reference_dt]
        return max(previous) if previous else None

    upcoming = [candidate for candidate in candidates if candidate > reference_dt]
    return min(upcoming) if upcoming else None


def get_month_name_number(raw_month):
    month_lookup = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    return month_lookup.get(raw_month)


def get_moon_phase_phrase_date(phrase):
    reference = get_reference_date()
    phrase = re.sub(r"^on\s+", "", phrase)
    if phrase in {"the full moon before last", "full moon before last"}:
        first = get_named_moon_datetime(reference.to_datetime(), "full moon", relation="last")
        if first is None:
            return None
        second = get_named_moon_datetime(first, "full moon", relation="last")
        return date_from_datetime(second) if second is not None else None
    constrained_match = re.fullmatch(
        r"(?:the\s+)?(?:(?P<which>first|last)\s+)?(?P<phase>new moon|first quarter moon|full moon|last quarter moon|harvest moon|blue moon)\s+in\s+(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)\s+(?P<year>\d{4})",
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
        r"(?:the\s+)?(?:(?P<which>first|last)\s+)?(?P<phase>new moon|first quarter moon|full moon|last quarter moon|harvest moon|blue moon)\s+in\s+(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)",
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
            if moment >= reference.to_datetime():
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
    return (
        AnchorDefinition(
            "special",
            ("event", "named"),
            lambda phrase: get_special_phrase_date(phrase),
        ),
        AnchorDefinition(
            "holiday",
            ("event", "calendar"),
            lambda phrase: get_holiday_date(phrase),
        ),
        AnchorDefinition(
            "solar",
            ("event", "astronomical"),
            lambda phrase: get_solar_event_phrase_date(
                phrase, *args, timezone_aware=timezone_aware, **kwargs
            ),
        ),
        AnchorDefinition(
            "moon",
            ("event", "astronomical"),
            lambda phrase: get_moon_phase_phrase_date(phrase),
        ),
        AnchorDefinition(
            "named_lunar",
            ("event", "astronomical"),
            lambda phrase: get_named_lunar_event_date(phrase),
        ),
        AnchorDefinition(
            "season",
            ("event", "structural", "calendar"),
            lambda phrase: get_season_anchor_date(phrase),
        ),
        AnchorDefinition(
            "solstice_equinox",
            ("event", "astronomical", "calendar"),
            lambda phrase: get_solstice_equinox_date(phrase),
        ),
        AnchorDefinition(
            "quarter",
            ("structural", "boundary"),
            lambda phrase: get_quarter_phrase_date(phrase),
        ),
        AnchorDefinition(
            "boundary",
            ("structural", "boundary"),
            lambda phrase: get_boundary_phrase_date(phrase),
        ),
        AnchorDefinition(
            "ordinal_weekday",
            ("structural", "calendar"),
            lambda phrase: get_ordinal_weekday_date(phrase),
        ),
        AnchorDefinition(
            "month_anchor",
            ("structural", "calendar"),
            lambda phrase: get_month_anchor_date(phrase),
        ),
        AnchorDefinition(
            "week_of_month",
            ("structural", "calendar"),
            lambda phrase: get_week_of_month_anchor_date(phrase),
        ),
        AnchorDefinition(
            "day_of_year",
            ("structural", "calendar"),
            lambda phrase: get_day_of_year_phrase_date(phrase),
        ),
        AnchorDefinition(
            "leap_anchor",
            ("structural", "calendar"),
            lambda phrase: get_leap_year_anchor_date(phrase),
        ),
        AnchorDefinition(
            "relative_weekday",
            ("structural", "relative"),
            lambda phrase: get_relative_weekday_phrase_date(
                phrase, *args, timezone_aware=timezone_aware, **kwargs
            ),
        ),
        AnchorDefinition(
            "recurring_week",
            ("event", "structural", "calendar"),
            lambda phrase: get_recurring_week_anchor_date(phrase),
        ),
        AnchorDefinition(
            "fiscal",
            ("event", "structural", "business"),
            lambda phrase: get_fiscal_anchor_date(phrase),
        ),
    )


def resolve_registered_anchor(
    phrase, *args, families=None, timezone_aware=False, **kwargs
):
    requested_families = set(families or ())
    reference = (
        coerce_reference_date(kwargs["relative_to"])
        if "relative_to" in kwargs and kwargs["relative_to"] is not None
        else get_reference_date()
    )
    token = CURRENT_REFERENCE.set(reference)
    try:
        for definition in get_registered_anchor_definitions(
            *args, timezone_aware=timezone_aware, **kwargs
        ):
            if requested_families and requested_families.isdisjoint(definition.families):
                continue
            resolved = definition.resolver(phrase)
            if resolved is not None:
                return resolved, definition
    finally:
        CURRENT_REFERENCE.reset(token)
    return None, None


def get_anchor_metadata_overrides(definition):
    if definition is None:
        return {}

    if definition.name == "month_anchor":
        return {
            "semantic_kind": "period",
            "representative_granularity": "month",
        }
    if definition.name == "week_of_month":
        return {
            "semantic_kind": "period",
            "representative_granularity": "week",
        }
    if definition.name in {"leap_anchor"}:
        return {
            "semantic_kind": "period",
            "representative_granularity": "year",
        }
    if definition.name in {"day_of_year"}:
        return {
            "semantic_kind": "period",
            "representative_granularity": "day",
        }
    if definition.name in {"moon", "solar"}:
        return {
            "semantic_kind": "instant",
            "representative_granularity": "second",
        }
    if definition.name in {"named_lunar", "solstice_equinox"}:
        return {
            "semantic_kind": "instant",
            "representative_granularity": "second",
        }
    if definition.name in {"season"}:
        return {
            "semantic_kind": "period",
            "representative_granularity": "season",
        }
    if definition.name in {"recurring_week"}:
        return {
            "semantic_kind": "period",
            "representative_granularity": "week",
        }
    if definition.name in {"fiscal"}:
        return {
            "semantic_kind": "boundary",
            "representative_granularity": "quarter",
        }
    return {}


def get_named_event_date(phrase, *args, timezone_aware=False, **kwargs):
    resolved, _definition = resolve_registered_anchor(
        phrase,
        *args,
        families={"event"},
        timezone_aware=timezone_aware,
        **kwargs,
    )
    return resolved


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

        date_part = parse_anchor_date(
            match.group("date"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if date_part is None:
            normalized_date = re.sub(r"^the\s+", "", match.group("date"))
            if normalized_date != match.group("date"):
                date_part = parse_anchor_date(
                    normalized_date,
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
        r"in the (?P<part>morning|late morning|afternoon|late afternoon|evening|night)", phrase
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
        r"(?P<date>today|tomorrow|yesterday|this|(?:next|last)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?P<part>morning|late morning|afternoon|late afternoon|evening|night|lunchtime|dinnertime|teatime|early in the morning|early morning|mid-morning|mid morning)",
        r"(?P<part>morning|late morning|afternoon|late afternoon|evening|night|lunchtime|dinnertime|teatime|early in the morning|early morning|mid-morning|mid morning)\s+(?P<date>today|tomorrow|yesterday|(?:next|last)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
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
        anchor_date = parse_anchor_date(match.group("anchor"))
        if anchor_date is None:
            anchor_date = parse_natural_date_strict(match.group("anchor"))
        if anchor_date is None:
            return None
        return set_date_time(anchor_date, 17, 0)

    match = re.fullmatch(
        r"(?:the\s+)?(?P<count>first|second|third|1st|2nd|3rd|\d+)\s+(?:business|working)\s+days?\s+(?P<direction>after|before)\s+(?P<anchor>.+)",
        phrase,
    )
    if match is not None:
        count_lookup = {"first": 1, "second": 2, "third": 3, "1st": 1, "2nd": 2, "3rd": 3}
        raw_count = match.group("count")
        count = count_lookup.get(raw_count, int(raw_count) if raw_count.isdigit() else None)
        if count is None:
            return None

        anchor_date = parse_anchor_date(match.group("anchor"))
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
        anchor_date = parse_anchor_date(match.group("anchor"))
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
    compound_amount_pattern = (
        r"(?:twenty|thirty|forty|fifty)(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?"
    )
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
                minutes = 1 if match.group("amount") in {"a", "an"} else int(
                    match.group("amount")
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
                            named_hour, _named_minute = get_named_clock_time(target_hour)
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
                                minutes = 1 if match.group("amount") in {"a", "an"} else int(
                                    match.group("amount")
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
    match = re.fullmatch(r"(?P<amount>a|an|\d+)\s+minutes?\s+past\s+the\s+hour", time_phrase)
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
    if not candidate:
        return None

    anchor_date = parse_anchor_date(
        candidate,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )
    if anchor_date is not None:
        return anchor_date

    return parse_structured_date_text(
        candidate,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )


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

    return {
        "a": 1,
        "an": 1,
        "several": 7,
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
    }.get(raw_number, int(raw_number) if raw_number.isdigit() else None)


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
    unit_pattern = r"(years?|months?|weeks?|days?|hours?|minutes?|seconds?|milliseconds?|microseconds?)"
    components = []

    for raw_number, raw_unit in re.findall(
        rf"{number_pattern}\s+{unit_pattern}", offset_text
    ):
        amount = parse_offset_number(raw_number)
        if amount is None:
            return None
        unit = raw_unit[:-1] if raw_unit.endswith("s") else raw_unit
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
            anchor_date = parse_natural_date_strict(
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
        r"(?P<offset>.+?)\s+(?P<anchor>today|tomorrow|yesterday)",
        phrase,
    )
    if shortcut_match is not None:
        components = parse_compound_offset(
            replace_short_words(shortcut_match.group("offset").strip())
        )
        if components is not None:
            anchor_date = parse_natural_date_strict(
                shortcut_match.group("anchor"),
                *args,
                timezone_aware=timezone_aware,
                **kwargs,
            )
            if anchor_date is not None:
                return apply_relative_offsets(anchor_date, components, 1)

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
        r"(?:(?:in)\s+)?(?P<offset>.+?)\s+(?P<direction>from|after|before)\s+(?P<anchor>.+)",
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
    sign = -1 if direction == "before" else 1

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


def get_year_wrapped_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    match = re.fullmatch(r"(?P<year>\d{4})\s+(?P<rest>.+)", phrase)
    if match is None:
        return None

    target_year = int(match.group("year"))
    shifted_reference = clone_date(get_reference_date())
    shifted_reference.set_fullyear(target_year)
    parse_kwargs = dict(kwargs)
    parse_kwargs["relative_to"] = shifted_reference
    inner_date = parse_natural_date_strict(
        match.group("rest"),
        *args,
        timezone_aware=timezone_aware,
        **parse_kwargs,
    )
    if inner_date is None:
        return None

    return inner_date


def get_year_suffix_wrapped_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    match = re.fullmatch(r"(?P<rest>.+?)\s+(?P<year>\d{4})", phrase)
    if match is None:
        return None

    target_year = int(match.group("year"))
    shifted_reference = clone_date(get_reference_date())
    shifted_reference.set_fullyear(target_year)
    parse_kwargs = dict(kwargs)
    parse_kwargs["relative_to"] = shifted_reference
    inner_date = parse_natural_date_strict(
        match.group("rest"),
        *args,
        timezone_aware=timezone_aware,
        **parse_kwargs,
    )
    if inner_date is None:
        return None

    if inner_date.get_year() != target_year:
        inner_date = clone_date(inner_date)
        inner_date.set_fullyear(target_year)

    return inner_date


def get_composed_date_time_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
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

    compound_amount_pattern = (
        r"(?:twenty|thirty|forty|fifty)(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?"
    )
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
        head_date = parse_structured_date_text(
            date_with_part_then_time_match.group("date"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        tail_clock = parse_structured_time_text(
            f"{date_with_part_then_time_match.group('time')} in the {date_with_part_then_time_match.group('part')}"
            ,
            *args,
            reference_override=head_date,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if head_date is not None and tail_clock is not None:
            return merge_date_with_explicit_time(head_date, tail_clock)

    generic_time_by_date_match = re.fullmatch(
        r"(?P<time>.+?)\s+by\s+(?P<date>.+)",
        phrase,
    )
    if generic_time_by_date_match is not None:
        tail_date = parse_structured_date_text(
            generic_time_by_date_match.group("date"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        head_time = parse_structured_time_text(
            generic_time_by_date_match.group("time"),
            *args,
            reference_override=tail_date,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if head_time is not None and tail_date is not None:
            return merge_date_with_explicit_time(tail_date, head_time)

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
        time_part = parse_time_like(explicit_time_relative_day_match.group("time"))
        date_part = parse_natural_date_strict(
            explicit_time_relative_day_match.group("date"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if time_part is not None and date_part is not None:
            return merge_date_with_explicit_time(date_part, time_part)

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
            tail_clock = get_clock_phrase_date(generic_date_when_time_match.group("tail"))
            if tail_clock is not None:
                return merge_date_with_explicit_time(head_date, tail_clock)

    bare_date_then_clock_match = re.fullmatch(
        rf"(?P<head>.+?)\s+(?P<tail>{clock_phrase_pattern})",
        phrase,
    )
    if bare_date_then_clock_match is not None:
        head_date = parse_structured_date_text(
            bare_date_then_clock_match.group("head"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        tail_clock = parse_structured_time_text(
            bare_date_then_clock_match.group("tail"),
            reference_override=head_date,
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if head_date is not None and tail_clock is not None:
            return merge_date_with_explicit_time(head_date, tail_clock)

    bare_clock_then_date_match = re.fullmatch(
        rf"(?P<head>{clock_phrase_pattern})\s+(?P<tail>.+)",
        phrase,
    )
    if bare_clock_then_date_match is not None:
        tail_date = parse_structured_date_text(
            bare_clock_then_date_match.group("tail"),
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        head_clock = parse_structured_time_text(
            bare_clock_then_date_match.group("head"),
            reference_override=tail_date,
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if head_clock is not None and tail_date is not None:
            return merge_date_with_explicit_time(tail_date, head_clock)

    tokens = phrase.split()
    max_tail_tokens = min(len(tokens) - 1, 8)
    for tail_size in range(max_tail_tokens, 1, -1):
        head_text = " ".join(tokens[:-tail_size]).strip()
        tail_text = " ".join(tokens[-tail_size:]).strip()
        if not head_text or not tail_text:
            continue
        head_date = parse_structured_date_text(
            head_text,
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if head_date is None:
            continue
        tail_time = parse_structured_time_text(
            tail_text,
            *args,
            reference_override=head_date,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if tail_time is None:
            continue
        return merge_date_with_explicit_time(head_date, tail_time)

    max_head_tokens = min(len(tokens) - 1, 8)
    for head_size in range(max_head_tokens, 1, -1):
        head_text = " ".join(tokens[:head_size]).strip()
        tail_text = " ".join(tokens[head_size:]).strip()
        if not head_text or not tail_text:
            continue
        tail_date = parse_structured_date_text(
            tail_text,
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if tail_date is None:
            continue
        head_time = parse_structured_time_text(
            head_text,
            *args,
            reference_override=tail_date,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if head_time is None:
            continue
        return merge_date_with_explicit_time(tail_date, head_time)

    date_then_time_patterns = [
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>\d{1,2}(?::\d{2})?(?:am|pm)|noon|midnight|midday)",
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>lunchtime|dinnertime|teatime|morning|afternoon|evening|night|early in the morning|early morning|mid-morning|mid morning)",
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>\d{1,2}(?::\d{2})?ish)",
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>(?:about|around)\s+\d{1,2}(?::\d{2})?ish)",
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>(?:about|around)\s+\d{1,2}(?::\d{2})?(?:am|pm))",
        rf"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>(?:a|an|\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|{compound_amount_pattern})\s+(?:minutes?\s+)?(?:past|to)\s+(?:the\s+hour|\d{1,2}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve))",
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>(?:a\s+)?quarter\s+(?:past|to)\s+(?:\d{1,2}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)|half\s+past\s+(?:\d{1,2}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)|half\s+(?:\d{1,2}(?:am|pm)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve))",
    ]
    time_then_date_patterns = [
        r"(?P<time>\d{1,2}(?::\d{2})?(?::\d{2})?\s?(?:am|pm)|noon|midnight|midday)\s+(?P<date>.+)",
        r"(?P<time>.+?)\s+(?P<date>(?:on\s+)?(?:today|tomorrow|yesterday|this)\b.*)",
        r"(?P<time>.+?)\s+(?P<date>(?:the\s+)?(?:first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th|last|penultimate)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b.*)",
        r"(?P<time>.+?)\s+on\s+(?P<date>.+)",
        r"(?P<time>.+?)\s+in\s+(?P<date>.+)",
        r"(?P<time>.+?)\s+(?P<date>(?:on\s+)?(?:(?:next|last)\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b.*)",
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

    if phrase in {"forever", "for ever", "infinity", "∞"}:
        infinite_date = stDate("forever")
        return attach_parse_metadata(
            infinite_date,
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="infinity",
                representative_granularity="unbounded",
            ),
        )

    phrase, tzinfo = extract_timezone_suffix(phrase)
    phrase = normalize_phrase(phrase)
    phrase = apply_word_aliases(phrase)
    phrase = normalize_phrase(phrase)
    phrase = apply_literal_aliases(phrase)
    phrase = normalize_phrase(phrase)
    if phrase in {"forever", "for ever", "infinity", "∞"}:
        infinite_date = stDate("forever")
        return attach_parse_metadata(
            infinite_date,
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="infinity",
                representative_granularity="unbounded",
            ),
        )
    phrase, trailing_tzinfo = extract_timezone_suffix(phrase)
    if tzinfo is None:
        tzinfo = trailing_tzinfo
    leap_year_offset_date = get_leap_year_offset_date(phrase)
    ordinal_time_coordinate_date = get_ordinal_time_coordinate_date(
        phrase, *args, timezone_aware=timezone_aware
    )
    compact_offset_date = get_compact_offset_phrase_date(phrase)
    relative_month_day_date = get_relative_month_day_phrase_date(phrase)
    counted_weekday_date = get_counted_weekday_phrase_date(phrase)
    counted_holiday_date = get_counted_holiday_phrase_date(phrase)
    weekday_and_date_date = get_weekday_and_date_phrase_date(
        phrase, *args, timezone_aware=timezone_aware
    )
    weekday_in_month_date = get_weekday_in_month_date(phrase)
    counted_weekday_anchor_date = get_counted_weekday_anchor_date(
        phrase, *args, timezone_aware=timezone_aware
    )
    recurring_weekday_date = get_recurring_weekday_date(
        phrase, *args, timezone_aware=timezone_aware, **kwargs
    )
    weekday_anchor_date = get_weekday_anchor_date(
        phrase, *args, timezone_aware=timezone_aware
    )
    ordinal_weekday_anchor_date = get_ordinal_weekday_anchor_date(
        phrase, *args, timezone_aware=timezone_aware
    )
    add_subtract_date = get_add_subtract_phrase_date(
        phrase, *args, timezone_aware=timezone_aware
    )
    ordinal_month_year_date = get_ordinal_month_year_date(phrase)
    weekday_occurrence_period_date = get_weekday_occurrence_period_phrase_date(phrase)
    business_date = get_business_phrase_date(phrase)
    sleep_date = get_sleep_phrase_date(phrase)
    clock_date = get_clock_phrase_date(phrase)
    compound_clock_date = get_compound_clock_phrase_date(
        phrase, *args, timezone_aware=timezone_aware
    )
    anchor_offset_date = get_anchor_offset_phrase_date(
        phrase, *args, timezone_aware=timezone_aware
    )
    year_wrapped_date = get_year_wrapped_phrase_date(
        phrase, *args, timezone_aware=timezone_aware, **kwargs
    )
    composed_date_time = get_composed_date_time_phrase_date(
        phrase, *args, timezone_aware=timezone_aware
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
    if (
        part_of_day_date is not None
        and re.search(
            r"\b(?:late morning|late afternoon|morning|afternoon|evening|night|lunchtime|dinnertime|teatime)\b",
            normalized_phrase,
        )
        and not re.search(
            r"\b(?:past|to|quarter|half|when the clock strikes|@| at )\b",
            normalized_phrase,
        )
    ):
        return attach_parse_metadata(
            apply_timezone(part_of_day_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
            ),
        )

    if composed_date_time is not None and re.search(
        r"(?:\b(?:at|when|past|to|half|quarter|noon|midnight|midday|morning|afternoon|evening|night|dawn|sunrise|sunset|dusk|twilight|business)\b|@)",
        normalized_phrase,
    ) and (
        not re.search(r"\b(?:before|after|from|hence|ago)\b", normalized_phrase)
        or re.search(
            r"(?:@| at )\s*\d{1,2}:\d{2}(?::\d{2})?(?:\s?(?:am|pm))?$",
            normalized_phrase,
        )
        or re.search(r"\bby\b", normalized_phrase)
    ) and (
        registered_anchor_definition is None
        or registered_anchor_definition.name not in {"solar"}
    ) and not re.match(
        r"^(?:in|on)\s+the\s+(?:morning|afternoon|evening|night)\b",
        normalized_phrase,
    ):
        metadata_overrides = get_composed_metadata_overrides(normalized_phrase)
        return attach_parse_metadata(
            apply_timezone(composed_date_time, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                **metadata_overrides,
            ),
        )

    if registered_anchor_date is not None:
        return attach_parse_metadata(
            apply_timezone(
                registered_anchor_date, tzinfo, timezone_aware=timezone_aware
            ),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                **get_anchor_metadata_overrides(registered_anchor_definition),
            ),
        )

    if leap_year_offset_date is not None:
        return attach_parse_metadata(
            apply_timezone(
                leap_year_offset_date, tzinfo, timezone_aware=timezone_aware
            ),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="relative_offset",
                representative_granularity="year",
            ),
        )

    if ordinal_time_coordinate_date is not None:
        return attach_parse_metadata(
            apply_timezone(
                ordinal_time_coordinate_date, tzinfo, timezone_aware=timezone_aware
            ),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="instant",
                representative_granularity="second",
            ),
        )

    if compact_offset_date is not None:
        return attach_parse_metadata(
            apply_timezone(compact_offset_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="relative_offset",
                representative_granularity="minute",
            ),
        )

    if counted_holiday_date is not None:
        return attach_parse_metadata(
            apply_timezone(counted_holiday_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="relative_offset",
                representative_granularity="day",
            ),
        )

    if relative_month_day_date is not None:
        return attach_parse_metadata(
            apply_timezone(relative_month_day_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="date",
                representative_granularity="day",
            ),
        )

    if counted_weekday_date is not None:
        return attach_parse_metadata(
            apply_timezone(counted_weekday_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="relative_offset",
                representative_granularity="week",
            ),
        )

    if weekday_and_date_date is not None:
        return attach_parse_metadata(
            apply_timezone(weekday_and_date_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="date",
                representative_granularity="day",
            ),
        )

    if weekday_in_month_date is not None:
        return attach_parse_metadata(
            apply_timezone(weekday_in_month_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="date",
                representative_granularity="day",
            ),
        )

    if counted_weekday_anchor_date is not None:
        return attach_parse_metadata(
            apply_timezone(
                counted_weekday_anchor_date, tzinfo, timezone_aware=timezone_aware
            ),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="date",
                representative_granularity="day",
            ),
        )

    if recurring_weekday_date is not None:
        return attach_parse_metadata(
            apply_timezone(recurring_weekday_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="recurring",
                representative_granularity="week",
            ),
        )

    if weekday_anchor_date is not None:
        return attach_parse_metadata(
            apply_timezone(weekday_anchor_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="date",
                representative_granularity="day",
            ),
        )

    if ordinal_weekday_anchor_date is not None:
        return attach_parse_metadata(
            apply_timezone(
                ordinal_weekday_anchor_date, tzinfo, timezone_aware=timezone_aware
            ),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="date",
                representative_granularity="day",
            ),
        )

    if add_subtract_date is not None:
        return attach_parse_metadata(
            apply_timezone(add_subtract_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="relative_offset",
                representative_granularity="day",
            ),
        )

    if ordinal_month_year_date is not None:
        return attach_parse_metadata(
            apply_timezone(
                ordinal_month_year_date, tzinfo, timezone_aware=timezone_aware
            ),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
            ),
        )

    if weekday_occurrence_period_date is not None:
        return attach_parse_metadata(
            apply_timezone(
                weekday_occurrence_period_date, tzinfo, timezone_aware=timezone_aware
            ),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                semantic_kind="date",
                representative_granularity="day",
            ),
        )

    if business_date is not None:
        return attach_parse_metadata(
            apply_timezone(business_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
            ),
        )

    if sleep_date is not None:
        return attach_parse_metadata(
            apply_timezone(sleep_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
            ),
        )

    if clock_date is not None:
        return attach_parse_metadata(
            apply_timezone(clock_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
            ),
        )

    if compound_clock_date is not None:
        return attach_parse_metadata(
            apply_timezone(compound_clock_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
            ),
        )

    if anchor_offset_date is not None:
        return attach_parse_metadata(
            apply_timezone(anchor_offset_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
            ),
        )

    if year_wrapped_date is not None:
        return attach_parse_metadata(
            apply_timezone(year_wrapped_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
            ),
        )

    if composed_date_time is not None and not re.match(
        r"^(?:in|on)\s+the\s+(?:morning|afternoon|evening|night)\b",
        normalized_phrase,
    ):
        metadata_overrides = get_composed_metadata_overrides(normalized_phrase)
        return attach_parse_metadata(
            apply_timezone(composed_date_time, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
                **metadata_overrides,
            ),
        )

    if part_of_day_date is not None:
        return attach_parse_metadata(
            apply_timezone(part_of_day_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
            ),
        )

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
            merge_date_parts(holiday_date, tail_date), tzinfo, timezone_aware=timezone_aware
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
        return attach_parse_metadata(
            apply_timezone(get_reference_date(), tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
            ),
        )

    try:
        parsed = yacc.parse(phrase)
    except Exception:
        return None

    if not parsed:
        return None

    return attach_parse_metadata(
        apply_timezone(parsed[0], tzinfo, timezone_aware=timezone_aware),
        build_parse_metadata(
            raw_text,
            matched_text or raw_text,
            normalized_phrase,
            exact=not fuzzy,
            fuzzy=fuzzy,
            used_dateutil=False,
        ),
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
            return is_extraction_anchor(left, right) or is_extraction_anchor(right, None)

    if "-" in token:
        left, _, right = token.partition("-")
        if left and right:
            return is_extraction_anchor(left, right) or is_extraction_anchor(token.replace("-", " "), None)

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
        "today",
        "2day",
        "tdy",
        "tomorrow",
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
        "yesterday",
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
        "roughly",
        "approximately",
        "about",
        "around",
        "valentine's",
        "valentines",
        "new",
        "st",
        "leap",
    }
    days = {
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    }
    months = {
        "january",
        "jan",
        "february",
        "feb",
        "march",
        "mar",
        "april",
        "apr",
        "may",
        "june",
        "jun",
        "july",
        "jul",
        "august",
        "aug",
        "september",
        "sep",
        "sept",
        "october",
        "oct",
        "november",
        "nov",
        "december",
        "dec",
    }
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
        "hour",
        "hours",
        "minute",
        "minutes",
        "second",
        "seconds",
        "millisecond",
        "milliseconds",
    }

    if token in direct_tokens or token in days or token in months or token in HOLIDAY_FIRST_TOKENS:
        return True

    if token == "month" and next_token in {"end", "close"}:
        return True

    if token == "t" and next_token == "minus":
        return True

    if token == "t-minus":
        return True

    if token == "as" and next_token == "of":
        return True

    if token in {"by", "from", "on"} and next_token in direct_tokens.union(days).union(months):
        return True

    if token in {"+", "-"} and re.fullmatch(r"\d+(?:\.\d+)?", next_token or ""):
        return True

    if token in {"plus", "minus", "add", "off"} and (
        re.fullmatch(r"\d+(?:\.\d+)?", next_token or "")
        or next_token in units
        or next_token in {"a", "an", "one", "two", "three", "four", "five", "six", "seven"}
    ):
        return True

    if token == "take" and next_token == "away":
        return True

    if token == "give" and next_token == "or":
        return True

    if token in {"roughly", "approximately", "about", "around"} and (
        re.fullmatch(r"\d+(?:\.\d+)?", next_token or "")
        or next_token in units
        or next_token in {"a", "an", "one", "two", "three", "four", "five", "six", "seven"}
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

    if re.fullmatch(r"\d+(?:\.\d+)?", token) and next_token in units:
        return True

    if re.fullmatch(r"\d+(?:\.\d+)?", token) and next_token in {
        "monday",
        "mondays",
        "tuesday",
        "tuesdays",
        "wednesday",
        "wednesdays",
        "thursday",
        "thursdays",
        "friday",
        "fridays",
        "saturday",
        "saturdays",
        "sunday",
        "sundays",
    }:
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
        if any(get_registered_holiday_resolver(candidate) is not None for candidate in candidates):
            return True

    if re.fullmatch(r"\d{4}", token) and next_token == "on":
        return True

    if token in {
        "mondays",
        "tuesdays",
        "wednesdays",
        "thursdays",
        "fridays",
        "saturdays",
        "sundays",
    }:
        return True

    if token == "every" and next_token in {
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
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
    } and next_token in units.union(
        {
            "monday",
            "mondays",
            "tuesday",
            "tuesdays",
            "wednesday",
            "wednesdays",
            "thursday",
            "thursdays",
            "friday",
            "fridays",
            "saturday",
            "saturdays",
            "sunday",
            "sundays",
            "quarter",
        }
    ):
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
    } and next_token:
        holiday_candidate = next_token
        candidates = [holiday_candidate]
        if holiday_candidate.endswith("ies"):
            candidates.append(holiday_candidate[:-3] + "y")
        if holiday_candidate.endswith("es"):
            candidates.append(holiday_candidate[:-2])
        if holiday_candidate.endswith("s"):
            candidates.append(holiday_candidate[:-1])
        if any(get_registered_holiday_resolver(candidate) is not None for candidate in candidates):
            return True

    if (
        token in {
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
        "penultimate",
    } and next_token in units.union(days).union({"day", "week", "month", "year"}):
        return True

    if token == "the" and (
        next_token in {
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
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
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
    from_, to = resolve_duration_arguments(
        *args, from_=from_, to=to, kwargs=kwargs
    )
    start = coerce_value_date(from_, argument_name="from_", default_now=True)
    end = coerce_value_date(to, argument_name="to")
    if used_default_start:
        end = maybe_roll_until_target_forward(end, start)
    return format_duration_string(start.to_datetime(), end.to_datetime())


def after(*args, from_=None, to=None, **kwargs):
    from_, to = resolve_duration_arguments(
        *args, from_=from_, to=to, kwargs=kwargs
    )
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
