import datetime
import re


def extract_timezone_suffix(phrase):
    import stringtime as core

    match = re.search(
        r"\s+(z|utc|gmt|est|edt|cst|cdt|mst|mdt|pst|pdt|bst|cet|cest|eet|eest|ist|jst|aest|aedt|acst|acdt|awst|(?:utc|gmt)[+-]\d{1,2}(?::?\d{2})?)$",
        phrase,
    )
    if match is None:
        return phrase, None

    tzinfo = core.build_tzinfo(match.group(1))
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
        r"\b(?:at|on)\s+(?P<time>\d{1,2}(?::\d{2})?(?::\d{2})?)\s+(?P<tz>utc|gmt|est|edt|cst|cdt|mst|mdt|pst|pdt|bst|cet|cest|eet|eest|ist|jst|aest|aedt|acst|acdt|awst)\b",
        r"at \g<time> \g<tz>",
        phrase,
        flags=re.IGNORECASE,
    )


def normalize_phrase(phrase):
    import stringtime as core

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
        rf"\bthe start of the month of (?P<month>{core.MONTH_RE})\b",
        r"the start of \g<month>",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(r"\bnew year's\b(?!\s+day)", "new year's day", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bthe bank holiday\b", "bank holiday", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bbank holiday monday\b", "bank holiday", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bthe night before christmas\b", "christmas eve", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\beop today\b", "eop", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bthe close of year\b", "close of year", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bthe start of next quarter\b", "start of next quarter", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bend of business by tomorrow\b", "end of business tomorrow", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\b(?:in|on)\s+the\s+morrow\b", "tomorrow", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bthe\s+morrow\b", "tomorrow", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\blunch\s+time\b", "lunchtime", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bdinner\s+time\b", "dinnertime", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\btea\s+time\b", "teatime", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\b(?:about|around)\s+(lunchtime|dinnertime|teatime)\b", r"\1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(rf"\bmidnight\s+(?P<weekday>{core.WEEKDAY_RE})\b", r"midnight on \g<weekday>", phrase, flags=re.IGNORECASE)
    phrase = re.sub(rf"\bthe\s+beginning\s+of\s+(?P<month>{core.MONTH_RE})\b", r"the start of \g<month>", phrase, flags=re.IGNORECASE)
    phrase = re.sub(rf"\bbeginning\s+of\s+(?P<month>{core.MONTH_RE})\b", r"start of \g<month>", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bfirst light\b", "dawn", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"^at\s+(dawn|sunrise|sunset|dusk|twilight)\s+(.+)$", r"\1 \2", phrase, flags=re.IGNORECASE)
    phrase = re.sub(
        r"\b(?P<hour>[01]?\d|2[0-3]):(?P<minute>\d{2})\b(?!:\d{2})(?!\s*(?:am|pm)\b)",
        normalize_24h_time,
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(r"\bthe\s+start\s+of\s+(q[1-4](?:\s+\d{4})?)\b", r"start of \1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bmiddle\s+of\s+(q[1-4](?:\s+\d{4})?)\b", r"mid \1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bmid\s+of\s+(q[1-4](?:\s+\d{4})?)\b", r"mid \1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bstart\s+of\s+the\s+(q[1-4](?:\s+\d{4})?)\b", r"start of \1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bnext\s+month\s+on\s+(?P<day>\d+)(?P<suffix>st|nd|rd|th)\b", r"\g<day>\g<suffix> of next month", phrase, flags=re.IGNORECASE)
    phrase = re.sub(rf"\bnext\s+month\s+on\s+(?P<day>{core.ORDINAL_MONTH_RE})\b", r"next month on the \g<day>", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\b(?P<day>\d{1,2}(?:st|nd|rd|th))\s+in\s+last\s+month\b", r"\g<day> of last month", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bthe\s+second-last\s+day\s+of\s+the\s+month\b", "the second to last day of the month", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bthe\s+penultimate\s+day\s+of\s+the\s+month\b", "the second to last day of the month", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bsecond-last\s+day\s+of\s+the\s+month\b", "second to last day of the month", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bpenultimate\s+day\s+of\s+the\s+month\b", "second to last day of the month", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bsecond\s+to\s+last\s+day\s+in\s+the\s+month\b", "second to last day of the month", phrase, flags=re.IGNORECASE)
    phrase = re.sub(rf"\bmidnight\s+on\s+the\s+({core.WEEKDAY_RE})\b", r"midnight on \1", phrase, flags=re.IGNORECASE)
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
    phrase = re.sub(r"^at\s+(noon|midnight|midday)\s+(today|tomorrow|yesterday)$", r"\2 at \1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"^at\s+(.+?\b(?:utc(?:[+-]\d+)?|pst|est|cst|mst|gmt))\s+(today|tomorrow|yesterday)$", r"\2 at \1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(rf"^by\s+(?=(?:{core.DATE_PREFIX_LOOKAHEAD_RE})\b)", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(rf"^as\s+of\s+(?=(?:{core.DATE_PREFIX_LOOKAHEAD_RE})\b)", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(rf"^on\s+(?=(?:the\s+)?(?:next|last|this|{core.WEEKDAY_RE}|\d{{1,2}}(?:st|nd|rd|th)|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\b)", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(rf"^in\s+(?=(?:{core.MONTH_RE})\b)", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"^at\s+(?=(?:noon|midnight|midday|lunchtime|dinnertime|teatime|\d{1,2}(?::\d{2})?(?:am|pm)?)\b)", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(rf"^from\s+(?=(?:today|tomorrow|yesterday|next|last|this|{core.WEEKDAY_RE}|{core.MONTH_RE})\b)", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"^from\s+the\s+(next|last)\b", r"\1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"^on\s+the\s+(next|last)\b", r"\1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"^the\s+(next|last)\b", r"\1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bthe\s+start\s+of\s+the\s+next\s+quarter\b", "start of next quarter", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bt[\s-]*minus\s+(?P<rest>.+)$", lambda match: f"{match.group('rest')} ago", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\b(noon|midnight|midday)ish\b", r"\1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\b(?:about|around)\s+(?=(?:\d{1,2}(?::\d{2})?(?:am|pm)?|\d{1,2}ish|noon|midnight|midday|dawn|sunrise|sunset|dusk|twilight)\b)", "", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\btonight\b", "today night", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\bclose of business\b", "end of business", phrase, flags=re.IGNORECASE)
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
    phrase = re.sub(r"^(in\s+.+?)\s+from now$", r"\1", phrase)
    return phrase


def normalize_ambiguity_preferences(phrase):
    import stringtime as core

    direction_preference = core.get_ambiguous_direction_preference()

    if direction_preference is not None:
        weekday_match = re.fullmatch(
            rf"(?:on\s+)?(?P<weekday>{core.WEEKDAY_RE})",
            phrase,
            flags=re.IGNORECASE,
        )
        if weekday_match is not None:
            weekday = weekday_match.group("weekday")
            reference_weekday = core.get_reference_date().to_datetime().weekday()
            target_weekday = core.WEEKDAY_INDEX[core.normalize_weekday_name(weekday)]
            forward_delta = (target_weekday - reference_weekday) % 7
            backward_delta = (reference_weekday - target_weekday) % 7

            if direction_preference == "future":
                return f"next {weekday}"
            if direction_preference == "past":
                return f"last {weekday}"
            if forward_delta == 0 and backward_delta == 0:
                return f"this {weekday}"
            if backward_delta < forward_delta:
                return f"last {weekday}"
            return f"next {weekday}"

        month_match = re.fullmatch(
            rf"(?:in\s+)?(?P<month>{core.MONTH_RE})",
            phrase,
            flags=re.IGNORECASE,
        )
        if month_match is not None:
            month = month_match.group("month")
            normalized_month = core.normalize_month_name(month)
            target_month = core.MONTH_INDEX[normalized_month]
            reference_dt = core.get_reference_date().to_datetime().replace(tzinfo=None)
            reference_month = reference_dt.month
            reference_year = reference_dt.year
            forward_months = (target_month - reference_month) % 12
            backward_months = (reference_month - target_month) % 12

            if direction_preference == "future":
                target_year = (
                    reference_year + 1 if target_month <= reference_month else reference_year
                )
                return f"{month} {target_year}"
            if direction_preference == "past":
                target_year = (
                    reference_year - 1 if target_month >= reference_month else reference_year
                )
                return f"{month} {target_year}"

            candidate_years = (reference_year - 1, reference_year, reference_year + 1)
            ranked_candidates = []
            for candidate_year in candidate_years:
                candidate_dt = reference_dt.replace(
                    year=candidate_year,
                    month=target_month,
                    day=1,
                )
                ranked_candidates.append(
                    (
                        abs(candidate_dt - reference_dt),
                        0 if candidate_dt >= reference_dt else 1,
                        candidate_year,
                    )
                )
            target_year = min(ranked_candidates)[2]
            return f"{month} {target_year}"

    return phrase


def apply_word_aliases(phrase):
    import stringtime as core

    for source, target in core.NORMALIZATION_WORD_ALIASES.items():
        phrase = re.sub(rf"\b{re.escape(source)}\b", target, phrase)
    return phrase


def apply_literal_aliases(phrase):
    import stringtime as core

    for source, target in core.NORMALIZATION_ALIASES.items():
        phrase = phrase.replace(source, target)
    return phrase


def normalize_duration_datetime(value):
    if getattr(value, "is_infinite", False):
        raise ValueError("Cannot format a bounded duration against infinity")
    if value.tzinfo is None:
        return value.replace(microsecond=0)
    return value.astimezone(datetime.timezone.utc).replace(tzinfo=None, microsecond=0)


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


def normalize_parse_input(raw_text, *, apply_ambiguity_preferences=True):
    phrase = raw_text.lower().strip()
    phrase = phrase.strip(" \t\r\n,.;:!?()[]{}\"'")
    if phrase == "":
        return phrase, None

    phrase = re.sub(r"(^|\s)@\s*", r"\1at ", phrase)
    phrase, tzinfo = extract_timezone_suffix(phrase)
    phrase = normalize_phrase(phrase)
    phrase = apply_word_aliases(phrase)
    phrase = normalize_phrase(phrase)
    phrase = apply_literal_aliases(phrase)
    phrase = normalize_phrase(phrase)
    if apply_ambiguity_preferences:
        phrase = normalize_ambiguity_preferences(phrase)
        phrase = normalize_phrase(phrase)
    phrase = re.sub(
        r"^before\s+(?P<time>\d{1,2}(?::\d{2})?(?::\d{2})?(?:am|pm))\s+yesterday$",
        r"before yesterday at \g<time>",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase = re.sub(
        r"^after\s+(?P<time>\d{1,2}(?::\d{2})?(?::\d{2})?(?:am|pm))\s+tomorrow$",
        r"after tomorrow at \g<time>",
        phrase,
        flags=re.IGNORECASE,
    )
    phrase, trailing_tzinfo = extract_timezone_suffix(phrase)
    if tzinfo is None:
        tzinfo = trailing_tzinfo
    return phrase, tzinfo
