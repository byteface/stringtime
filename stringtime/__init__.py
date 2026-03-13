__version__ = "0.0.6"
__all__ = ["Date", "DateMatch", "ParseMetadata", "extract_dates"]

import datetime
import contextvars
import re
import warnings
from dataclasses import dataclass

import ply.lex as lex
import ply.yacc as yacc
from dateutil.easter import easter

from stringtime.date import Date as stDate

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
TIME_TOKEN_RE = re.compile(r"\d{1,2}(?::\d{2})?(?:am|pm)?$", re.IGNORECASE)
CURRENT_REFERENCE = contextvars.ContextVar("stringtime_reference", default=None)


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
        r"^((?:next|last)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|today|tomorrow|yesterday)\s+(\d{1,2}(?::\d{2})?(?:am|pm))$",
        r"\1 at \2",
        phrase,
    )


def normalize_phrase(phrase):
    phrase = normalize_timezone_phrase(phrase)
    phrase = re.sub(
        r"^(in\s+.+?)\s+from now$",
        r"\1",
        phrase,
    )
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


def clone_date(date_obj):
    cloned = stDate()
    cloned._date = date_obj.to_datetime().replace()
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


def get_reference_date():
    reference = CURRENT_REFERENCE.get()
    if reference is None:
        return stDate()
    return clone_date(reference)


def attach_parse_metadata(date_obj, metadata):
    date_obj.parse_metadata = metadata
    return date_obj


def build_parse_metadata(
    input_text, matched_text, normalized_text, *, exact, fuzzy, used_dateutil
):
    return ParseMetadata(
        input_text=input_text,
        matched_text=matched_text,
        normalized_text=normalized_text,
        exact=exact,
        fuzzy=fuzzy,
        used_dateutil=used_dateutil,
    )


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

    # TODO - regexes might be better here. allow space or number in front
    # phrase = re.sub(r'[\s*\d*](hrs)', 'hour', phrase)
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
        r"\b(?P<day_phrase>(?:(?:last|next)\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\s+(?:at|@)\s+(?P<time_phrase>\d{1,2}:\d{2}(?:\s?(?:am|pm))?)\b",
        rewrite_day_time_phrase,
        phrase,
    )
    phrase = re.sub(
        r"\b(?P<number>a|an|one|three)\s+quarters?\s+of\s+(?:an?\s+)?(?P<unit>years?|months?|weeks?|days?|hours?|minutes?|seconds?)\b",
        replace_quarter_words,
        phrase,
    )

    phrase = phrase.replace("hr ", "hour")
    phrase = phrase.replace("hrs", "hour")
    phrase = phrase.replace("min ", "minute")
    phrase = phrase.replace("mins", "minute")
    phrase = phrase.replace("sec ", "second")
    phrase = phrase.replace("secs", "second")
    phrase = phrase.replace("dy", "day")
    phrase = phrase.replace("dys", "day")

    phrase = phrase.replace("mos", "month")
    phrase = phrase.replace("mnth", "month")
    phrase = phrase.replace("mnths", "month")
    # phrase = phrase.replace("mo", "month")

    phrase = phrase.replace("wk", "week")
    phrase = phrase.replace("wks", "week")
    phrase = phrase.replace("yr", "year")
    phrase = phrase.replace("yrs", "year")
    # phrase = phrase.replace("ms", "millisecond")
    # phrase = phrase.replace("mil", "millisecond")
    phrase = re.sub(r"\bms\b", "millisecond", phrase)
    phrase = re.sub(r"\bmil\b", "millisecond", phrase)
    phrase = re.sub(r"\bmils\b", "millisecond", phrase)
    # phrase = phrase.replace("mils", "millisecond")

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
    phrase = phrase.replace("a few", "3")
    # phrase = re.sub(r"a few\b", "3", phrase)
    # phrase = re.sub(r"\bseveral\b", "7", phrase)

    phrase = phrase.replace("oclock", "")
    phrase = phrase.replace("o'clock", "")

    phrase = phrase.replace("2moro", "tomorrow")
    phrase = phrase.replace("2morro", "tomorrow")
    phrase = phrase.replace("tomorow", "tomorrow")

    # typos
    phrase = phrase.replace("febuary", "february")
    phrase = phrase.replace("feburary", "february")

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


def get_holiday_date(phrase):
    current_year = get_reference_date().get_year()
    year_offset = 0

    if phrase.endswith(" next year"):
        year_offset = 1
        phrase = phrase[: -len(" next year")]
    elif phrase.endswith(" last year"):
        year_offset = -1
        phrase = phrase[: -len(" last year")]
    elif phrase.endswith(" this year"):
        phrase = phrase[: -len(" this year")]

    holiday_key = phrase.strip()
    year = current_year + year_offset

    holiday_builders = {
        "new year's day": lambda y: datetime.date(y, 1, 1),
        "new years day": lambda y: datetime.date(y, 1, 1),
        "new year's eve": lambda y: datetime.date(y, 12, 31),
        "new years eve": lambda y: datetime.date(y, 12, 31),
        "valentine's day": lambda y: datetime.date(y, 2, 14),
        "valentines day": lambda y: datetime.date(y, 2, 14),
        "st patrick's day": lambda y: datetime.date(y, 3, 17),
        "st patricks day": lambda y: datetime.date(y, 3, 17),
        "easter": lambda y: easter(y),
        "memorial day": lambda y: last_weekday_of_month(y, 5, 0),
        "independence day": lambda y: datetime.date(y, 7, 4),
        "fourth of july": lambda y: datetime.date(y, 7, 4),
        "labor day": lambda y: nth_weekday_of_month(y, 9, 0, 1),
        "halloween": lambda y: datetime.date(y, 10, 31),
        "thanksgiving": lambda y: nth_weekday_of_month(y, 11, 3, 4),
        "black friday": lambda y: nth_weekday_of_month(y, 11, 3, 4)
        + datetime.timedelta(days=1),
        "christmas eve": lambda y: datetime.date(y, 12, 24),
        "christmas": lambda y: datetime.date(y, 12, 25),
        "christmas day": lambda y: datetime.date(y, 12, 25),
        "boxing day": lambda y: datetime.date(y, 12, 26),
    }

    if holiday_key not in holiday_builders:
        return None

    holiday = holiday_builders[holiday_key](year)
    d = get_reference_date()
    d.set_fullyear(holiday.year)
    d.set_month(holiday.month - 1)
    d.set_date(holiday.day)
    return d


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

    if period in months:
        return reference_year, months[period]

    if period in {"month", "the month", "this month"}:
        return reference_year, reference_month

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


def get_ordinal_weekday_date(phrase):
    match = re.fullmatch(
        r"(?:the\s+)?(?P<occurrence>first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th|last|penultimate)\s+(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?:in|of)\s+(?P<period>.+)",
        phrase,
    )
    if match is None:
        return None

    occurrence = match.group("occurrence")
    weekday_name = match.group("weekday")
    period = match.group("period")

    resolved = resolve_period_year_month(period)
    if resolved is None:
        return None

    year, month = resolved
    weekday = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }[weekday_name]

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
    named_time = get_named_clock_time(phrase)
    if named_time is not None:
        hour, minute = named_time
        d = get_reference_date()
        d.set_hours(hour)
        d.set_minutes(minute)
        d.set_seconds(0)
        return d

    match = re.fullmatch(r"when the clock strikes (?P<hour>\d{1,2})", phrase)
    if match is not None:
        hour = int(match.group("hour")) % 24
        d = get_reference_date()
        d.set_hours(hour)
        d.set_minutes(0)
        d.set_seconds(0)
        return d

    match = re.fullmatch(r"(?:a\s+)?quarter\s+(?P<direction>past|to)\s+(?P<hour>\d{1,2})", phrase)
    if match is not None:
        minutes = 15
        direction = match.group("direction")
        hour = int(match.group("hour")) % 24
    else:
        match = re.fullmatch(r"half\s+past\s+(?P<hour>\d{1,2})", phrase)
        if match is not None:
            minutes = 30
            direction = "past"
            hour = int(match.group("hour")) % 24
        else:
            match = re.fullmatch(
                r"(?P<amount>a|an|\d+)\s+minutes?\s+(?P<direction>past|to)\s+(?P<hour>\d{1,2})",
                phrase,
            )
            if match is None:
                return None
            minutes = 1 if match.group("amount") in {"a", "an"} else int(match.group("amount"))
            direction = match.group("direction")
            hour = int(match.group("hour")) % 24

    d = get_reference_date()
    if direction == "past":
        d.set_hours(hour)
        d.set_minutes(minutes)
    else:
        d.set_hours((hour - 1) % 24)
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


def parse_natural_date_strict(date, *args, **kwargs):
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

    phrase, tzinfo = extract_timezone_suffix(phrase)
    phrase = normalize_phrase(phrase)
    ordinal_weekday_date = get_ordinal_weekday_date(phrase)
    business_date = get_business_phrase_date(phrase)
    sleep_date = get_sleep_phrase_date(phrase)
    clock_date = get_clock_phrase_date(phrase)
    compound_clock_date = get_compound_clock_phrase_date(
        phrase, *args, timezone_aware=timezone_aware
    )
    normalized_phrase = replace_short_words(phrase)
    phrase = normalized_phrase

    holiday_date = get_holiday_date(phrase)
    if holiday_date is not None:
        return attach_parse_metadata(
            apply_timezone(holiday_date, tzinfo, timezone_aware=timezone_aware),
            build_parse_metadata(
                raw_text,
                matched_text or raw_text,
                normalized_phrase,
                exact=not fuzzy,
                fuzzy=fuzzy,
                used_dateutil=False,
            ),
        )

    if ordinal_weekday_date is not None:
        return attach_parse_metadata(
            apply_timezone(
                ordinal_weekday_date, tzinfo, timezone_aware=timezone_aware
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


def is_extraction_anchor(token, next_token=None):
    token = token.lower()
    next_token = next_token.lower() if next_token is not None else None

    direct_tokens = {
        "in",
        "on",
        "at",
        "@",
        "today",
        "tomorrow",
        "yesterday",
        "after",
        "before",
        "next",
        "last",
        "this",
        "christmas",
        "easter",
        "thanksgiving",
        "halloween",
        "labor",
        "memorial",
        "black",
        "boxing",
        "valentine's",
        "valentines",
        "new",
        "st",
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
    }
    units = {
        "year",
        "years",
        "month",
        "months",
        "week",
        "weeks",
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

    if token in direct_tokens or token in days or token in months:
        return True

    if token in TIMEZONE_OFFSETS or build_tzinfo(token) is not None:
        return True

    if TIME_TOKEN_RE.fullmatch(token):
        return True

    if re.fullmatch(r"\d+(?:st|nd|rd|th)", token):
        return True

    if re.fullmatch(r"\d+(?::\d{2})?", token) and next_token in {
        "am",
        "pm",
        "oclock",
    }:
        return True

    if re.fullmatch(r"\d+(?:\.\d+)?", token) and next_token in units:
        return True

    return False


def extract_dates(text, *args, max_tokens=12, **kwargs):
    matches = []
    tokens = list(EXTRACTION_TOKEN_RE.finditer(text))
    parse_kwargs = dict(kwargs)
    timezone_aware = parse_kwargs.pop("timezone_aware", False)
    relative_to = parse_kwargs.pop("relative_to", None)
    reference = coerce_reference_date(relative_to)

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
    token = CURRENT_REFERENCE.set(reference)
    try:
        parsed = parse_natural_date_strict(date, *args, **kwargs)
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
