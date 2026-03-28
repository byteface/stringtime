import re

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
    "o'clock": "oclock",
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
    "nite": "night",
    "2nite": "tonight",
    "tonite": "tonight",
    "tnite": "tonight",
}

RELATIVE_DAY_WORDS = ("today", "tomorrow", "yesterday")
RELATIVE_DAY_WORD_SET = set(RELATIVE_DAY_WORDS)
FUZZY_QUALIFIER_WORDS = ("roughly", "approximately", "about", "around")
FUZZY_QUALIFIER_WORD_SET = set(FUZZY_QUALIFIER_WORDS)

WEEKDAY_NAMES = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)

WEEKDAY_INDEX = {name: index for index, name in enumerate(WEEKDAY_NAMES)}
WEEKDAY_PLURALS = tuple(f"{name}s" for name in WEEKDAY_NAMES)
WEEKDAY_NAME_SET = set(WEEKDAY_NAMES)
WEEKDAY_PLURAL_SET = set(WEEKDAY_PLURALS)
WEEKDAY_ALL_SET = WEEKDAY_NAME_SET | WEEKDAY_PLURAL_SET
BUSINESS_WEEKDAY_TUPLE = WEEKDAY_NAMES[:5]
WEEKDAY_PATTERN = "|".join(WEEKDAY_NAMES)
WEEKDAY_PLURAL_PATTERN = "|".join(WEEKDAY_PLURALS)
WEEKDAY_OR_PLURAL_PATTERN = "|".join((*WEEKDAY_NAMES, *WEEKDAY_PLURALS))

WEEKDAY_ALIASES = {
    "mon": "monday",
    "mondays": "mondays",
    "tue": "tuesday",
    "tues": "tuesday",
    "tuesdays": "tuesdays",
    "wed": "wednesday",
    "weds": "wednesday",
    "wednesdays": "wednesdays",
    "thu": "thursday",
    "thur": "thursday",
    "thurs": "thursday",
    "thursdays": "thursdays",
    "fri": "friday",
    "fridays": "fridays",
    "sat": "saturday",
    "sats": "saturdays",
    "sun": "sunday",
    "suns": "sundays",
    "snday": "sunday",
    "sndays": "sundays",
}

MONTH_NAMES = (
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

MONTH_INDEX = {name: index + 1 for index, name in enumerate(MONTH_NAMES)}
MONTH_NAME_SET = set(MONTH_NAMES)
MONTH_PLURALS = tuple(f"{name}s" for name in MONTH_NAMES)
MONTH_PLURAL_SET = set(MONTH_PLURALS)
MONTH_ALL_SET = MONTH_NAME_SET | MONTH_PLURAL_SET
MONTH_PATTERN = "|".join(MONTH_NAMES)

MONTH_ALIASES = {
    "jan": "january",
    "feb": "february",
    "mar": "march",
    "apr": "april",
    "jun": "june",
    "jul": "july",
    "aug": "august",
    "sep": "september",
    "sept": "september",
    "oct": "october",
    "nov": "november",
    "dec": "december",
}

CARDINAL_NUMBER_MAP = {
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
CARDINAL_NUMBER_WORD_SET = set(CARDINAL_NUMBER_MAP)

FUTURE_RELATIVE_PHRASES = (
    "today plus",
    "today add",
    "now plus",
    "now add",
    "add",
    "added",
    "plus",
    "from now",
    "time",
    "in the future",
    "into the future",
    "away",
    "away from now",
    "hence",
    "past now",
    "after now",
    "beyond this current moment",
    "in an",
    "in a",
    "in",
    "next",
    "an",
)
PAST_RELATIVE_PHRASES = (
    "today minus",
    "today take",
    "today take away",
    "now minus",
    "now take",
    "now take away",
    "minus",
    "take away",
    "off",
    "ago",
    "in the past",
    "the past",
    "just been",
    "before now",
    "before this moment",
    "before this current moment",
    "before",
    "last",
)
FUTURE_RELATIVE_PHRASE_PATTERN = "|".join(
    phrase.replace(" ", r"\ ") for phrase in FUTURE_RELATIVE_PHRASES
)
PAST_RELATIVE_PHRASE_PATTERN = "|".join(
    phrase.replace(" ", r"\ ") for phrase in PAST_RELATIVE_PHRASES
)
INDEFINITE_RELATIVE_ARTICLES = frozenset({"in", "in a", "in an", "an"})
NEGATIVE_RELATIVE_SIGN_PHRASES = frozenset(PAST_RELATIVE_PHRASES)

ORDINAL_MONTH_MAP = {
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

ORDINAL_OCCURRENCE_MAP = {
    "first": 1,
    "1st": 1,
    "second": 2,
    "2nd": 2,
    "third": 3,
    "3rd": 3,
    "fourth": 4,
    "4th": 4,
    "fifth": 5,
    "5th": 5,
    "last": -1,
    "penultimate": -2,
}

POSITIVE_ORDINAL_OCCURRENCE_MAP = {
    key: value for key, value in ORDINAL_OCCURRENCE_MAP.items() if value > 0
}
BUSINESS_MONTHLY_ORDINAL_MAP = {
    key: value
    for key, value in ORDINAL_OCCURRENCE_MAP.items()
    if value in {1, 3, -1}
}
BUSINESS_QUARTERLY_ORDINAL_MAP = {
    key: value
    for key, value in ORDINAL_OCCURRENCE_MAP.items()
    if value in {1, -1}
}
WEEKEND_ORDINAL_MAP = {
    key: value for key, value in ORDINAL_OCCURRENCE_MAP.items() if value in {1, -1}
}

ORDINAL_DAY_MAP = {
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
    "13th": 13,
    "14th": 14,
    "15th": 15,
    "16th": 16,
    "17th": 17,
    "18th": 18,
    "19th": 19,
    "20th": 20,
    "21st": 21,
    "22nd": 22,
    "23rd": 23,
    "24th": 24,
    "25th": 25,
    "26th": 26,
    "27th": 27,
    "28th": 28,
    "29th": 29,
    "30th": 30,
    "31st": 31,
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
    "twenty second": 22,
    "twenty third": 23,
    "twenty fourth": 24,
    "twenty fifth": 25,
    "twenty sixth": 26,
    "twenty seventh": 27,
    "twenty eighth": 28,
    "twenty ninth": 29,
    "thirtieth": 30,
    "thirty first": 31,
}

ORDINAL_MONTH_PATTERN = "|".join(
    sorted((re.escape(key) for key in ORDINAL_MONTH_MAP), key=len, reverse=True)
)
ORDINAL_DAY_PATTERN = "|".join(
    sorted((re.escape(key) for key in ORDINAL_DAY_MAP), key=len, reverse=True)
)
DATE_ORDINAL_PATTERN = rf"\d{{1,2}}(?:st|nd|rd|th)?|{ORDINAL_DAY_PATTERN}"
MONTH_OR_ORDINAL_MONTH_PATTERN = rf"{MONTH_PATTERN}|{ORDINAL_MONTH_PATTERN}"
ORDINAL_OCCURRENCE_PATTERN = "|".join(
    sorted((re.escape(key) for key in ORDINAL_OCCURRENCE_MAP), key=len, reverse=True)
)
POSITIVE_ORDINAL_OCCURRENCE_PATTERN = "|".join(
    sorted(
        (re.escape(key) for key in POSITIVE_ORDINAL_OCCURRENCE_MAP),
        key=len,
        reverse=True,
    )
)
BUSINESS_MONTHLY_ORDINAL_PATTERN = "|".join(
    sorted(
        (re.escape(key) for key in BUSINESS_MONTHLY_ORDINAL_MAP),
        key=len,
        reverse=True,
    )
)
BUSINESS_QUARTERLY_ORDINAL_PATTERN = "|".join(
    sorted(
        (re.escape(key) for key in BUSINESS_QUARTERLY_ORDINAL_MAP),
        key=len,
        reverse=True,
    )
)
WEEKEND_ORDINAL_PATTERN = "|".join(
    sorted((re.escape(key) for key in WEEKEND_ORDINAL_MAP), key=len, reverse=True)
)
CARDINAL_NUMBER_PATTERN = r"(?<!\w)(?:%s)(?!\w)" % "|".join(
    sorted((re.escape(key) for key in CARDINAL_NUMBER_MAP), key=len, reverse=True)
)


def weekday_regex(*, include_plural=False):
    if include_plural:
        return WEEKDAY_OR_PLURAL_PATTERN
    return WEEKDAY_PATTERN


def month_regex():
    return MONTH_PATTERN


def normalize_weekday_name(token):
    if token is None:
        return None
    normalized = WEEKDAY_ALIASES.get(token.lower(), token.lower())
    if normalized.endswith("s") and normalized[:-1] in WEEKDAY_INDEX:
        normalized = normalized[:-1]
    return normalized if normalized in WEEKDAY_INDEX else None


def normalize_month_name(token):
    if token is None:
        return None
    normalized = MONTH_ALIASES.get(token.lower(), token.lower())
    if normalized.endswith("s") and normalized[:-1] in MONTH_INDEX:
        normalized = normalized[:-1]
    return normalized if normalized in MONTH_INDEX else None


def parse_cardinal_number(token):
    if token is None:
        return None
    lowered = token.lower()
    if lowered.isdigit():
        return int(lowered)
    return CARDINAL_NUMBER_MAP.get(lowered)
