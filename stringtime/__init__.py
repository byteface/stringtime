__version__ = "0.0.4"
__all__ = ["Date"]

import re
import warnings

import ply.lex as lex
import ply.yacc as yacc

from stringtime.date import Date as stDate

DEBUG = True
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


# -----------------------------------------------------------------------------

tokens = (
    "WORD_NUMBER",
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
)


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


def t_NUMBER(t):
    r"\d+"
    t.value = int(t.value)
    # print('number detected!', t.value)
    return t


# t_WORD_NUMBER = (
#     r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety"
# )


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

    print('time detected!', t.value)

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
t_AT = r"at|@"
t_ON = r"on"
t_OF = r"of"
# t_THE = r"the"


def t_THE(t):
    r"the"
    print('the detected!', t.value)
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

        Args:
            year (_type_, optional): The year. Defaults to None.
            month (_type_, optional): The month. Defaults to None.
            week (_type_, optional): _description_. Defaults to None.
            day (_type_, optional): _description_. Defaults to None.
            hour (_type_, optional): _description_. Defaults to None.
            minute (_type_, optional): _description_. Defaults to None.
            second (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        d = stDate()
        if year is not None:
            d.set_year(year)
        if month is not None:
            d.set_month(month)  # note - should this one be -1?
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
        # TODO - should maybe optionally pass and remember the phrase on a new 'description' prop on Date...?
        d = stDate()
        if year is not None:
            stlog(
                f"Creating new date {year} years from now: Current date:",
                str(d),
                lvl="g",
            )
            current_year = d.get_year()
            d.set_fullyear(current_year + year)
        if month is not None:
            stlog(
                f"Creating new date {month} months from now: Current date:",
                str(d),
            )
            currrent_month = d.get_month()
            d.set_month(
                currrent_month + (month)  # - 1)
            )  # note the minus one is because Date expects 0-11 but humans say 1-12. wrong cos its the offset?
        if week is not None:
            stlog(
                f"Creating new date {week} weeks from now: Current date:",
                str(d),
                lvl="g",
            )
            currrent_day = d.get_date()
            d.set_date(currrent_day + week * 7)
        if day is not None:
            stlog(
                f"Creating new date {day} days from now: Current date:",
                str(d),
                lvl="g",
            )
            currrent_day = d.get_date()
            d.set_date(currrent_day + day)
        if hour is not None:
            stlog(
                f"  - Creating new date {hour} hours from now: Current date:",
                str(d),
                lvl="g",
            )
            currrent_hour = d.get_hours()
            d.set_hours(currrent_hour + hour)
        if minute is not None:
            stlog(
                f"  - Creating new date {minute} minutes from now: Current date:",
                str(d),
                lvl="g",
            )
            currrent_minute = d.get_minutes()
            d.set_minutes(currrent_minute + minute)
        if second is not None:
            stlog(
                f"  - Creating new date {second} seconds from now: Current date:",
                str(d),
                lvl="g",
            )
            currrent_second = d.get_seconds()
            d.set_seconds(currrent_second + second)

        return d


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
    "date_list :  date_list date"
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
    date_list : date_before_yesterday
    date_list : date_after_tomorrow
    """
    p[0] = [p[1]]


# TIME - not strictly valid. but should do a single unit of that time
# NUMBER TIME - not strictly valid. but should work
# TIME PHRASE -  again not really valid. but should do a single unit of that time
# TODO - might be able to have 'past phrases' and 'future phrases'
def p_single_date(p):
    """
    date : TIME
    date : NUMBER TIME
    date : WORD_NUMBER TIME
    date : PHRASE TIME
    date : TIME PHRASE
    date : NUMBER TIME PHRASE
    date : WORD_NUMBER TIME PHRASE
    date : PHRASE TIME PHRASE
    """
    if len(p) == 2:
        p[0] = DateFactory(p[1], 1)
    elif len(p) == 3:
        params = {p[2]: 1}  # TODO - prepend offset_ to the key. passing 1 as no number
        p[0] = DateFactory.create_date_with_offsets(**params)  # 'In a minute'
    elif len(p) == 4:
        if p[1] == "an":
            p[1] = 1  # if no number is passed, assume 1
        params = {p[2]: p[1]}  # TODO - prepend offset_ to the key
        p[0] = DateFactory.create_date_with_offsets(**params)


# in : PHRASE WORD_NUMBER TIME?? not getting converted
def p_single_date_in(p):
    """
    in : PHRASE NUMBER TIME
    in : PHRASE WORD_NUMBER TIME
    """
    if len(p) == 2:
        p[0] = DateFactory(p[1], 1)
    elif len(p) == 3:
        p[0] = DateFactory(p[1], p[2])
    elif len(p) == 4:
        params = {p[3]: p[2]}  # TODO - prepend offset_ to the key
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


# WORD_NUMBER TIME & WORD_NUMBER TIME PHRASE
def p_single_date_past(p):
    """
    date_past : NUMBER TIME PAST_PHRASE
    date_past : WORD_NUMBER TIME PAST_PHRASE
    """
    params = {p[2]: -p[1]}  # TODO - prepend offset_ to the key
    p[0] = DateFactory.create_date_with_offsets(**params)


def p_single_date_yesterday(p):
    """
    date_yesterday : YESTERDAY
    date_yesterday : YESTERDAY AT NUMBER
    date_yesterday : YESTERDAY AT WORD_NUMBER
    """
    if len(p) == 2:
        params = {"day": -1}
        p[0] = DateFactory.create_date_with_offsets(**params)
    if len(p) == 4:
        params = {
            "day": stDate().get_date() - 1,
            "hour": p[3],
            "minute": 0,
            "second": 0,
        }
        p[0] = DateFactory.create_date(**params)


def p_single_date_2moro(p):
    """
    date_2moro : TOMORROW
    date_2moro : TOMORROW AT NUMBER
    date_2moro : TOMORROW AT WORD_NUMBER
    """
    if len(p) == 2:
        params = {"day": 1}
        p[0] = DateFactory.create_date_with_offsets(**params)
    if len(p) == 4:
        params = {
            "day": stDate().get_date() + 1,
            "hour": p[3],
            "minute": 0,
            "second": 0,
        }
        p[0] = DateFactory.create_date(**params)


def p_single_date_day(p):
    """
    date_day : DAY
    date_day : PHRASE DAY
    date_day : PAST_PHRASE DAY
    """
    if len(p) == 2:
        day_to_find = p[1]
        d = stDate()
        # go forward each day until it matches
        while day_to_find.lower() != d.get_day(to_string=True).lower():
            d.set_date(d.get_date() + 1)

        p[0] = d
    if len(p) == 3:
        day_to_find = p[2]
        d = stDate()
        # go forward each day until it matches
        while day_to_find.lower() != d.get_day(to_string=True).lower():
            if p[1] == "last":
                d.set_date(d.get_date() - 1)
            elif p[1] == "next":
                d.set_date(d.get_date() + 1)

        p[0] = d


def p_this_or_next_period(p):
    """
    date_or : PAST_PHRASE TIME
    """
    if len(p) == 3:
        d = stDate()
        if p[1] == "last":
            if p[2] == "week":
                d.set_date(d.get_date() - 7)
            elif p[2] == "year":
                d.set_year(d.get_year() - 1)
            elif p[2] == "month":
                # print(d.get_month())
                d.set_month(
                    d.get_month()
                )  # -1)  #??? not sure why this is not -1???????. this must be a bug in set_month?
                # print(d.get_month())
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
    print('before_yesterday decteted')
    d = stDate()
    d.set_date(d.get_date() - 2)
    p[0] = d


def p_after_tomorrow(p):
    """
    date_after_tomorrow : AFTER_TOMORROW
    date_after_tomorrow : THE TIME AFTER_TOMORROW
    """
    d = stDate()
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
    # print('TWONKER')
    if len(p) == 3:
        # print('p:', p[1], p[2])
        d = stDate()
        d.set_date(p[1])
        p[0] = d
    if len(p) == 4:
        # print('p-:', p[1], p[2], p[3])
        d = stDate()
        d.set_date(p[2])
        # print(p[1], "the", p[1] == "the")
        if p[1] == "the":  # the-2-nd
            d.set_date(p[2])
        else:  # january-14-th
            # print('y!', p[1], p[2])
            m = d.get_month_index_by_name(p[1])
            # print('THE MONTH IS:',m)
            d.set_month(m)
            d.set_date(p[2])
        p[0] = d
    if len(p) == 5:
        # print('p--:', p[1], p[2], p[3], p[4])
        d = stDate()
        if p[1] == "on":  # on-the-1-st
            d.set_date(p[3])
        else:  # april-the-1-st
            # print('i think we are here::' , p[1], p[2], p[3], p[4])
            m = d.get_month_index_by_name(p[1])
            d.set_month(m)
            # print('THE date is:', p[3])
            d.set_date(p[3])
            # print('THE date isaaa:', d.get_date())
        p[0] = d
    if len(p) == 6:
        # print('p++:', p[1], p[2], p[3], p[4], p[5])
        d = stDate()  # the-18-th-of-january
        m = d.get_month_index_by_name(p[5])
        d.set_month(m)
        d.set_date(p[2])
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
        "immediately",
        "straight away",
        "at once",
        "as soon as possible",
        "asap",
        "here and now",
        "today",  # this one also requires a token. i.e. today at 5pm
    ]


def replace_short_words(phrase):
    """
    replace shortened words with normal equivalents
    """

    # TODO - regexes might be better here. allow space or number in front
    # phrase = re.sub(r'[\s*\d*](hrs)', 'hour', phrase)
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
    phrase = phrase.replace("ms", "millisecond")
    phrase = phrase.replace("mil", "millisecond")
    phrase = phrase.replace("mils", "millisecond")

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

    return phrase


def get_date(date, *args, **kwargs):
    try:
        phrase = date.lower()
        phrase = phrase.strip()
        phrase = replace_short_words(phrase)
        if is_now(phrase):
            return stDate()
        return yacc.parse(phrase)[0]
    except TypeError as e:
        # if debug raise the error
        if DEBUG:
            raise e
        return stDate(date, *args, **kwargs)
    except Exception as e:
        if DEBUG:
            raise e
        return stDate()


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
    return get_date(date)
