from stringtime.vocabulary import (
    CARDINAL_NUMBER_MAP,
    CARDINAL_NUMBER_PATTERN,
    FUTURE_RELATIVE_PHRASE_PATTERN,
    MONTH_PATTERN,
    PAST_RELATIVE_PHRASE_PATTERN,
    WEEKDAY_OR_PLURAL_PATTERN,
)


tokens = (
    "WORD_NUMBER",
    "DECIMAL",
    "NUMBER",
    "DAY",
    "REC_GROUP",
    "BUSINESS",
    "MONTH",
    "TIME",
    "PHRASE",
    "PAST_PHRASE",
    "NEXT",
    "EVERY",
    "UNTIL",
    "THROUGH",
    "EXCEPT",
    "FROM",
    "PLUS",
    "MINUS",
    "YESTERDAY",
    "TOMORROW",
    "AFTER_TOMORROW",
    "BEFORE_YESTERDAY",
    "TODAY",
    "THIS",
    "AT",
    "ON",
    "OF",
    "THE",
    "DATE_END",
    "AM",
    "PM",
    "COLON",
    "AND",
    "HALF",
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


def t_DATE_END(t):
    r"st\b|nd\b|rd\b|th\b"
    return t


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


def t_WORD_NUMBER(t):
    "placeholder"
    t.value = CARDINAL_NUMBER_MAP[t.value]
    return t


t_WORD_NUMBER.__doc__ = CARDINAL_NUMBER_PATTERN


def t_DAY(t):
    "placeholder"
    import stringtime as core

    normalized = core.normalize_weekday_name(t.value)
    if normalized is None:
        raise TypeError("Unknown day '%s'" % (t.value,))
    t.value = normalized
    return t


t_DAY.__doc__ = WEEKDAY_OR_PLURAL_PATTERN


def t_REC_GROUP(t):
    r"weekday|weekdays|weekend|weekends|weeknight|weeknights|daily"
    return t


def t_BUSINESS(t):
    r"business|working"
    return t


t_MONTH = MONTH_PATTERN


def t_TIME(t):
    r"years|months|weeks|days|hours|minutes|seconds|milliseconds|year|month|week|day|hour|minute|second|millisecond"
    if t.value.endswith("s"):
        t.value = t.value[:-1]
    return t


t_PHRASE = FUTURE_RELATIVE_PHRASE_PATTERN
t_PAST_PHRASE = PAST_RELATIVE_PHRASE_PATTERN

t_YESTERDAY = r"yesterday"
t_TOMORROW = r"tomorrow|2moro|2morro"
t_TODAY = r"today"
t_THIS = r"this"


def t_NEXT(t):
    r"next"
    return t


def t_EVERY(t):
    r"every|each|recurring"
    t.value = "every"
    return t


def t_UNTIL(t):
    r"until"
    return t


def t_THROUGH(t):
    r"through"
    return t


def t_EXCEPT(t):
    r"except"
    return t


def t_FROM(t):
    r"from"
    return t


def t_AFTER_TOMORROW(t):
    r"after\ tomorrow|after\ 2moro|after\ 2morro"
    return t


def t_BEFORE_YESTERDAY(t):
    r"before\ yesterday|other\ day"
    return t


def t_AT(t):
    r"at|@"
    return t


t_ON = r"on"
t_OF = r"of"


def t_AM(t):
    r"am"
    return t


def t_PM(t):
    r"pm"
    return t


def t_THE(t):
    r"the"
    return t


t_ignore = " \t"
