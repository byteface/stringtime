import datetime
import re


def split_recurring_phrase_parts(phrase):
    phrase = (phrase or "").strip().lower()
    phrase = re.sub(r"^recurring\s+", "every ", phrase)
    window_start = None
    window_end = None
    until_mode = None
    until_text = None
    start_text = None
    exclusions_text = None
    time_text = None

    window_match = re.fullmatch(
        r"(?P<base>.+?)\s+from\s+(?P<start>.+?)\s+to\s+(?P<end>.+)",
        phrase,
    )
    if window_match is not None:
        phrase = window_match.group("base").strip()
        window_start = window_match.group("start").strip()
        window_end = window_match.group("end").strip()

    until_match = re.fullmatch(
        r"(?P<base>.+?)\s+(?P<mode>until|through)\s+(?P<bound>.+)",
        phrase,
    )
    if until_match is not None:
        phrase = until_match.group("base").strip()
        until_mode = until_match.group("mode")
        until_text = until_match.group("bound").strip()

    time_match = re.fullmatch(r"(?P<base>.+?)\s+(?:at|@)\s+(?P<time>.+)", phrase)
    if time_match is not None:
        phrase = time_match.group("base").strip()
        time_text = time_match.group("time").strip()

    exclusions_match = re.fullmatch(r"(?P<base>.+?)\s+except\s+(?P<except>.+)", phrase)
    if exclusions_match is not None:
        phrase = exclusions_match.group("base").strip()
        exclusions_text = exclusions_match.group("except").strip()

    start_match = re.fullmatch(r"(?P<base>.+?)\s+from\s+(?P<start>.+)", phrase)
    if start_match is not None:
        phrase = start_match.group("base").strip()
        start_text = start_match.group("start").strip()

    return {
        "base": phrase,
        "time_text": time_text,
        "window_start": window_start,
        "window_end": window_end,
        "until_mode": until_mode,
        "until_text": until_text,
        "start_text": start_text,
        "exclusions_text": exclusions_text,
    }


def parse_recurring_weekday_series(text):
    import stringtime as core

    if text is None:
        return None
    normalized = re.sub(r"\s*,\s*", " and ", text.strip().lower())
    normalized = re.sub(r"\s+and\s+", " and ", normalized)
    weekdays = []
    for part in [segment.strip() for segment in normalized.split(" and ") if segment.strip()]:
        weekday = core.normalize_weekday_name(part)
        if weekday is None:
            return None
        weekdays.append(weekday)
    if not weekdays:
        return None
    return tuple(dict.fromkeys(weekdays))


def format_recurrence_time_value(time_text, *, part_of_day=None):
    import stringtime as core

    if time_text is None:
        return None, None, None

    candidate = core.parse_structured_time_text(time_text)
    if candidate is None:
        return None, None, None

    hour = candidate.get_hours()
    minute = candidate.get_minutes()
    if part_of_day in {"afternoon", "evening", "night"} and hour < 12:
        hour += 12
    elif part_of_day == "morning" and hour == 12:
        hour = 0

    return hour, minute, f"{hour:02d}:{minute:02d}:00"


def parse_recurring_exclusions(text):
    weekdays = parse_recurring_weekday_series(text)
    return weekdays or ()


def infer_recurring_details(phrase):
    import stringtime as core

    phrase = (phrase or "").strip().lower()
    ordinal_labels = {
        "1st": "first",
        "2nd": "second",
        "3rd": "third",
        "4th": "fourth",
        "5th": "fifth",
    }

    details = {}
    if phrase == "":
        return details

    parts = split_recurring_phrase_parts(phrase)
    base_phrase = parts["base"]
    time_text = parts["time_text"]
    window_start = parts["window_start"]
    window_end = parts["window_end"]
    until_text = parts["until_text"]
    start_text = parts["start_text"]
    exclusions = parse_recurring_exclusions(parts["exclusions_text"])

    part_of_day_hint = None
    part_match = re.fullmatch(
        r"(?:every\s+)?(?P<part>morning|afternoon|evening|night)",
        base_phrase,
    )
    if part_match is not None:
        part_of_day_hint = part_match.group("part")
    elif "weeknight" in base_phrase:
        part_of_day_hint = "night"

    parsed_hour, parsed_minute, parsed_time_text = format_recurrence_time_value(
        time_text,
        part_of_day=part_of_day_hint,
    )
    if parsed_time_text is not None:
        details["recurrence_byhour"] = parsed_hour
        details["recurrence_byminute"] = parsed_minute
    elif window_start is not None:
        start_hour, start_minute, start_value = format_recurrence_time_value(
            window_start,
            part_of_day=part_of_day_hint,
        )
        end_hour, end_minute, end_value = format_recurrence_time_value(
            window_end,
            part_of_day=part_of_day_hint,
        )
        if start_value is not None:
            details["recurrence_byhour"] = start_hour
            details["recurrence_byminute"] = start_minute
            details["recurrence_window_start"] = start_value
        if end_value is not None:
            if (
                start_hour is not None
                and end_hour is not None
                and end_hour <= start_hour
                and re.fullmatch(r"\d{1,2}", window_end or "")
            ):
                end_hour += 12
                end_value = f"{end_hour:02d}:{end_minute:02d}:00"
            details["recurrence_window_end"] = end_value

    if exclusions:
        details["recurrence_exclusions"] = exclusions
    if until_text is not None:
        details["recurrence_until"] = until_text
    if start_text is not None:
        details["recurrence_start"] = start_text

    if re.fullmatch(r"(?:every|each)\s+day|daily", base_phrase):
        details["recurrence_frequency"] = "daily"
        return details

    if part_match is not None:
        details["recurrence_frequency"] = "daily"
        return details

    if re.fullmatch(r"(?:every\s+)?weeknights?", base_phrase):
        details["recurrence_frequency"] = "weekly"
        details["recurrence_byweekday"] = ("monday", "tuesday", "wednesday", "thursday", "friday")
        return details

    weekday_series_match = re.fullmatch(
        rf"(?:on\s+)?(?:every\s+)?(?P<days>(?:{core.WEEKDAY_OR_PLURAL_PATTERN})(?:\s+and\s+(?:{core.WEEKDAY_OR_PLURAL_PATTERN}))+)",
        base_phrase,
    )
    if weekday_series_match is not None:
        weekday_series = parse_recurring_weekday_series(weekday_series_match.group("days"))
        if weekday_series is not None:
            details["recurrence_frequency"] = "weekly"
            details["recurrence_byweekday"] = weekday_series
            return details

    weekday_match = re.fullmatch(
        rf"(?:on\s+)?(?:(?:every)\s+)?(?P<weekday>{core.WEEKDAY_PLURAL_PATTERN})|every\s+(?P<singular>{core.WEEKDAY_PATTERN})",
        base_phrase,
    )
    if weekday_match is not None:
        weekday_name = weekday_match.group("weekday") or weekday_match.group("singular")
        if weekday_name.endswith("s"):
            weekday_name = weekday_name[:-1]
        details["recurrence_frequency"] = "weekly"
        details["recurrence_byweekday"] = (core.normalize_weekday_name(weekday_name),)
        return details

    if re.fullmatch(r"(?:on\s+)?(?:every\s+)?(?:weekday|weekdays)", base_phrase):
        details["recurrence_frequency"] = "weekly"
        details["recurrence_byweekday"] = tuple(
            day
            for day in ("monday", "tuesday", "wednesday", "thursday", "friday")
            if day not in exclusions
        )
        return details

    if re.fullmatch(r"(?:on\s+)?(?:every\s+)?(?:weekend|weekends)", base_phrase):
        details["recurrence_frequency"] = "weekly"
        details["recurrence_byweekday"] = tuple(
            day for day in ("saturday", "sunday") if day not in exclusions
        )
        return details

    other_weekday_match = re.fullmatch(
        rf"every\s+other\s+(?P<weekday>{core.WEEKDAY_PATTERN})",
        base_phrase,
    )
    if other_weekday_match is not None:
        details["recurrence_frequency"] = "weekly"
        details["recurrence_interval"] = 2
        details["recurrence_byweekday"] = (core.normalize_weekday_name(other_weekday_match.group("weekday")),)
        return details

    interval_match = re.fullmatch(r"every\s+(?P<count>\d+)\s+(?P<unit>days?|weeks?|months?)", base_phrase)
    if interval_match is not None:
        unit = interval_match.group("unit")
        count = int(interval_match.group("count"))
        if "day" in unit:
            details["recurrence_frequency"] = "daily"
        elif "week" in unit:
            details["recurrence_frequency"] = "weekly"
        else:
            details["recurrence_frequency"] = "monthly"
        details["recurrence_interval"] = count
        return details

    monthly_day_match = re.fullmatch(
        rf"(?:every\s+month\s+on\s+|on\s+)?(?:the\s+)?(?P<day>{core.DATE_ORDINAL_PATTERN})\s+of\s+(?:each|every)\s+month|every\s+month\s+on\s+(?:the\s+)?(?P<day_alt>{core.DATE_ORDINAL_PATTERN})",
        base_phrase,
    )
    if monthly_day_match is not None:
        raw_day = monthly_day_match.group("day") or monthly_day_match.group("day_alt")
        details["recurrence_frequency"] = "monthly"
        details["recurrence_bymonthday"] = core.ORDINAL_DAY_MAP.get(raw_day)
        return details

    interval_month_day_match = re.fullmatch(
        rf"every\s+(?P<count>\d+)(?:st|nd|rd|th)?\s+months?\s+on\s+(?:the\s+)?(?P<day>{core.DATE_ORDINAL_PATTERN})",
        base_phrase,
    )
    if interval_month_day_match is not None:
        details["recurrence_frequency"] = "monthly"
        details["recurrence_interval"] = int(interval_month_day_match.group("count"))
        details["recurrence_bymonthday"] = core.ORDINAL_DAY_MAP.get(interval_month_day_match.group("day"))
        return details

    monthly_weekday_match = re.fullmatch(
        rf"(?:the\s+)?(?P<occurrence>{core.ORDINAL_OCCURRENCE_PATTERN})\s+"
        rf"(?P<weekday>{core.WEEKDAY_PATTERN})\s+of\s+"
        r"(?:each|every)\s+month",
        base_phrase,
    )
    if monthly_weekday_match is not None:
        details["recurrence_frequency"] = "monthly"
        details["recurrence_ordinal"] = ordinal_labels.get(
            monthly_weekday_match.group("occurrence"),
            monthly_weekday_match.group("occurrence"),
        )
        details["recurrence_byweekday"] = (
            core.normalize_weekday_name(monthly_weekday_match.group("weekday")),
        )
        return details

    nth_weekday_match = re.fullmatch(
        rf"every\s+(?P<ordinal>{core.POSITIVE_ORDINAL_OCCURRENCE_PATTERN})\s+(?P<weekday>{core.WEEKDAY_PATTERN})",
        base_phrase,
    )
    if nth_weekday_match is not None:
        details["recurrence_frequency"] = "monthly"
        details["recurrence_ordinal"] = ordinal_labels.get(
            nth_weekday_match.group("ordinal"),
            nth_weekday_match.group("ordinal"),
        )
        details["recurrence_byweekday"] = (
            core.normalize_weekday_name(nth_weekday_match.group("weekday")),
        )
        return details

    if re.fullmatch(
        rf"(?:the\s+)?(?:{core.BUSINESS_QUARTERLY_ORDINAL_PATTERN})\s+(?:business|working)\s+day\s+of\s+(?:each|every)\s+month",
        base_phrase,
    ):
        details["recurrence_frequency"] = "monthly"
        details["recurrence_ordinal"] = "business"
        return details

    if re.fullmatch(
        rf"(?:the\s+)?(?:{core.BUSINESS_MONTHLY_ORDINAL_PATTERN})\s+(?:business|working)\s+day\s+of\s+(?:each|every)\s+month",
        base_phrase,
    ):
        details["recurrence_frequency"] = "monthly"
        details["recurrence_ordinal"] = "third"
        return details

    if re.fullmatch(
        rf"(?:the\s+)?(?:{core.WEEKEND_ORDINAL_PATTERN})\s+weekend\s+of\s+(?:each|every)\s+month",
        base_phrase,
    ):
        details["recurrence_frequency"] = "monthly"
        details["recurrence_ordinal"] = "weekend"
        return details

    yearly_holiday_match = re.fullmatch(
        r"every\s+(?P<anchor>(?:christmas|boxing day|christmas eve|new year's day|new years day|halloween|easter))",
        base_phrase,
    )
    if yearly_holiday_match is not None:
        details["recurrence_frequency"] = "yearly"
        return details

    yearly_month_day_match = re.fullmatch(
        rf"every\s+(?:(?P<month>{core.MONTH_RE})\s+(?P<day>\d{{1,2}}(?:st|nd|rd|th))|(?:the\s+)?(?P<day_first>\d{{1,2}}(?:st|nd|rd|th))\s+of\s+(?P<month_first>{core.MONTH_RE}))",
        base_phrase,
    )
    if yearly_month_day_match is not None:
        month_name = core.normalize_month_name(
            yearly_month_day_match.group("month")
            or yearly_month_day_match.group("month_first")
        )
        day_text = yearly_month_day_match.group("day") or yearly_month_day_match.group("day_first")
        details["recurrence_frequency"] = "yearly"
        details["recurrence_bymonth"] = core.MONTH_INDEX[month_name]
        details["recurrence_bymonthday"] = int(re.match(r"\d+", day_text).group(0))
        return details

    yearly_month_weekday_match = re.fullmatch(
        rf"(?:the\s+)?(?P<occurrence>{core.ORDINAL_OCCURRENCE_PATTERN})\s+"
        rf"(?P<weekday>{core.WEEKDAY_PATTERN})\s+of\s+every\s+(?P<month>{core.MONTH_RE})",
        base_phrase,
    )
    if yearly_month_weekday_match is not None:
        details["recurrence_frequency"] = "yearly"
        details["recurrence_ordinal"] = ordinal_labels.get(
            yearly_month_weekday_match.group("occurrence"),
            yearly_month_weekday_match.group("occurrence"),
        )
        details["recurrence_byweekday"] = (
            core.normalize_weekday_name(yearly_month_weekday_match.group("weekday")),
        )
        details["recurrence_bymonth"] = core.MONTH_INDEX[
            core.normalize_month_name(yearly_month_weekday_match.group("month"))
        ]
        return details

    yearly_in_month_match = re.fullmatch(
        rf"every\s+(?P<ordinal>{core.ORDINAL_OCCURRENCE_PATTERN})\s+(?P<weekday>{core.WEEKDAY_PATTERN})\s+in\s+(?P<month>{core.MONTH_RE})",
        base_phrase,
    )
    if yearly_in_month_match is not None:
        details["recurrence_frequency"] = "yearly"
        details["recurrence_ordinal"] = ordinal_labels.get(
            yearly_in_month_match.group("ordinal"),
            yearly_in_month_match.group("ordinal"),
        )
        details["recurrence_byweekday"] = (
            core.normalize_weekday_name(yearly_in_month_match.group("weekday")),
        )
        details["recurrence_bymonth"] = core.MONTH_INDEX[
            core.normalize_month_name(yearly_in_month_match.group("month"))
        ]
        return details

    yearly_of_year_match = re.fullmatch(
        rf"(?:the\s+)?(?P<occurrence>{core.ORDINAL_OCCURRENCE_PATTERN})\s+(?P<weekday>{core.WEEKDAY_PATTERN})\s+of\s+every\s+year",
        base_phrase,
    )
    if yearly_of_year_match is not None:
        details["recurrence_frequency"] = "yearly"
        details["recurrence_ordinal"] = ordinal_labels.get(
            yearly_of_year_match.group("occurrence"),
            yearly_of_year_match.group("occurrence"),
        )
        details["recurrence_byweekday"] = (
            core.normalize_weekday_name(yearly_of_year_match.group("weekday")),
        )
        return details

    if re.fullmatch(r"every\s+(?:business|working)\s+day", base_phrase):
        details["recurrence_frequency"] = "weekly"
        details["recurrence_byweekday"] = ("monday", "tuesday", "wednesday", "thursday", "friday")
        return details

    if re.fullmatch(
        rf"(?:the\s+)?(?:{core.BUSINESS_QUARTERLY_ORDINAL_PATTERN})\s+(?:business|working)\s+day\s+of\s+(?:each|every)\s+quarter",
        base_phrase,
    ):
        details["recurrence_frequency"] = "quarterly"
        return details

    return details


def get_recurring_schedule_granularity(phrase):
    details = infer_recurring_details(phrase)
    frequency = details.get("recurrence_frequency")

    if frequency == "daily":
        return "day"
    if frequency == "weekly":
        return "week"
    if frequency == "monthly":
        return "month"
    if frequency == "quarterly":
        return "quarter"
    if frequency == "yearly":
        return "year"
    return "week"


def get_recurring_weekday_date(phrase, *args, timezone_aware=False, **kwargs):
    import stringtime as core

    match = re.fullmatch(
        rf"(?:on\s+)?(?:(?:every)\s+)?(?P<weekday>{core.WEEKDAY_PLURAL_PATTERN})|every\s+(?P<singular>{core.WEEKDAY_PATTERN})",
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

    return core.parse_natural_date_strict(
        weekday_name,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )


def get_recurring_schedule_date(phrase, *args, timezone_aware=False, **kwargs):
    import stringtime as core

    reference = core.get_reference_date()
    normalized_phrase = phrase.strip().lower()
    weekday_lookup = core.WEEKDAY_INDEX
    month_names = core.MONTH_RE
    parts = split_recurring_phrase_parts(normalized_phrase)
    base_phrase = parts["base"]
    time_text = parts["time_text"]
    window_start = parts["window_start"]
    window_end = parts["window_end"]
    until_mode = parts["until_mode"]
    until_text = parts["until_text"]
    start_text = parts["start_text"]
    exclusions = set(parse_recurring_exclusions(parts["exclusions_text"]))
    reference_dt = reference.to_datetime().replace(tzinfo=None)

    part_of_day_hint = None
    part_match = re.fullmatch(
        r"(?:every\s+)?(?P<part>morning|afternoon|evening|night)",
        base_phrase,
    )
    if part_match is not None:
        part_of_day_hint = part_match.group("part")
    elif "weeknight" in base_phrase:
        part_of_day_hint = "night"

    explicit_hour, explicit_minute, _ = format_recurrence_time_value(
        time_text,
        part_of_day=part_of_day_hint,
    )
    window_hour, window_minute, _ = format_recurrence_time_value(
        window_start,
        part_of_day=part_of_day_hint,
    )
    window_end_hour, window_end_minute, _ = format_recurrence_time_value(
        window_end,
        part_of_day=part_of_day_hint,
    )
    if (
        window_hour is not None
        and window_end_hour is not None
        and window_end_hour <= window_hour
        and re.fullmatch(r"\d{1,2}", window_end or "")
    ):
        window_end_hour += 12

    def first_business_day_of_month(year, month):
        candidate = core.build_calendar_anchor_date(year, month, 1)
        while not core.is_business_day(candidate):
            candidate.set_date(candidate.get_date() + 1)
        return candidate

    def last_business_day_of_month(year, month):
        candidate = core.build_calendar_anchor_date(
            year, month, core.stDate.get_month_length(month, year)
        )
        while not core.is_business_day(candidate):
            candidate.set_date(candidate.get_date() - 1)
        return candidate

    def apply_schedule_time(candidate):
        candidate = core.clone_date(candidate)
        if explicit_hour is not None:
            candidate.set_hours(explicit_hour)
            candidate.set_minutes(explicit_minute)
            candidate.set_seconds(0)
            return candidate
        if window_hour is not None:
            candidate.set_hours(window_hour)
            candidate.set_minutes(window_minute)
            candidate.set_seconds(0)
            return candidate
        if part_of_day_hint is not None:
            hour, minute = core.get_part_of_day_time(part_of_day_hint)
            candidate.set_hours(hour)
            candidate.set_minutes(minute)
            candidate.set_seconds(0)
        return candidate

    def parse_until_date():
        if until_text is None:
            return None
        month_name = core.normalize_month_name(until_text)
        if until_mode == "through" and month_name is not None:
            year = reference.get_year()
            month = core.MONTH_INDEX[month_name]
            if month < reference.get_month() + 1:
                year += 1
            candidate = core.build_calendar_anchor_date(
                year, month, core.stDate.get_month_length(month, year)
            )
            candidate.set_hours(23)
            candidate.set_minutes(59)
            candidate.set_seconds(59)
            return candidate
        candidate = core.parse_natural_date_strict(
            until_text,
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )
        if candidate is None:
            return None
        if until_mode == "through":
            candidate = core.clone_date(candidate)
            candidate.set_hours(23)
            candidate.set_minutes(59)
            candidate.set_seconds(59)
        return candidate

    until_date = parse_until_date()

    def parse_start_date():
        if start_text is None:
            return None
        return core.parse_natural_date_strict(
            start_text,
            *args,
            timezone_aware=timezone_aware,
            **kwargs,
        )

    start_date = parse_start_date()

    def candidate_is_valid(candidate):
        candidate = apply_schedule_time(candidate)
        candidate_dt = candidate.to_datetime().replace(tzinfo=None)
        if candidate_dt <= reference_dt:
            return False
        if start_date is not None:
            start_dt = start_date.to_datetime().replace(tzinfo=None)
            if candidate_dt < start_dt:
                return False
        weekday_name = core.WEEKDAY_NAMES[candidate_dt.weekday()]
        if weekday_name in exclusions:
            return False
        if until_date is not None:
            until_dt = until_date.to_datetime().replace(tzinfo=None)
            if candidate_dt > until_dt:
                return False
        return True

    def next_matching_date(weekday_values):
        current = reference.to_datetime().date()
        for offset in range(1, 32):
            candidate_date = current + datetime.timedelta(days=offset)
            if candidate_date.weekday() not in weekday_values:
                continue
            candidate = core.clone_date(reference)
            candidate.set_fullyear(candidate_date.year)
            candidate.set_month(candidate_date.month - 1)
            candidate.set_date(candidate_date.day)
            if candidate_is_valid(candidate):
                return apply_schedule_time(candidate)
        return None

    def candidate_from_date(date_value):
        candidate = core.clone_date(reference)
        candidate.set_fullyear(date_value.year)
        candidate.set_month(date_value.month - 1)
        candidate.set_date(date_value.day)
        return candidate

    interval_weekday_match = re.fullmatch(
        rf"every\s+other\s+(?P<weekday>{core.WEEKDAY_PATTERN})",
        base_phrase,
    )
    if interval_weekday_match is not None:
        return next_matching_date(
            {weekday_lookup[core.normalize_weekday_name(interval_weekday_match.group("weekday"))]}
        )

    interval_weeks_match = re.fullmatch(r"every\s+(?P<count>\d+)\s+weeks?", base_phrase)
    if interval_weeks_match is not None:
        candidate = (
            core.clone_date(start_date)
            if start_date is not None
            else core.apply_relative_offset(reference, "week", int(interval_weeks_match.group("count")))
        )
        return apply_schedule_time(candidate) if candidate_is_valid(candidate) else None

    interval_months_match = re.fullmatch(r"every\s+(?P<count>\d+)\s+months?", base_phrase)
    if interval_months_match is not None:
        candidate = (
            core.clone_date(start_date)
            if start_date is not None
            else core.apply_relative_offset(reference, "month", int(interval_months_match.group("count")))
        )
        return apply_schedule_time(candidate) if candidate_is_valid(candidate) else None

    if re.fullmatch(r"(?:every|each)\s+day|daily", base_phrase):
        candidate = (
            core.clone_date(start_date)
            if start_date is not None
            else core.apply_relative_offset(reference, "day", 1)
        )
        return apply_schedule_time(candidate) if candidate_is_valid(candidate) else None

    if part_match is not None:
        candidate = (
            core.clone_date(start_date)
            if start_date is not None
            else core.apply_relative_offset(reference, "day", 1)
        )
        return apply_schedule_time(candidate) if candidate_is_valid(candidate) else None

    if re.fullmatch(r"(?:every\s+)?weeknights?", base_phrase):
        return next_matching_date({0, 1, 2, 3, 4}.difference({weekday_lookup[day] for day in exclusions}))

    multi_weekday_match = re.fullmatch(
        rf"(?:on\s+)?(?:every\s+)?(?P<days>(?:{core.WEEKDAY_OR_PLURAL_PATTERN})(?:\s+and\s+(?:{core.WEEKDAY_OR_PLURAL_PATTERN}))+)",
        base_phrase,
    )
    if multi_weekday_match is not None:
        weekday_series = parse_recurring_weekday_series(multi_weekday_match.group("days"))
        if weekday_series is not None:
            return next_matching_date(
                {weekday_lookup[day] for day in weekday_series if day not in exclusions}
            )

    weekday_group_match = re.fullmatch(
        r"(?:on\s+)?(?:every\s+)?(?P<group>weekday|weekdays|weekend|weekends)",
        base_phrase,
    )
    if weekday_group_match is not None:
        group = weekday_group_match.group("group")
        if group in {"weekday", "weekdays"}:
            weekday_values = {0, 1, 2, 3, 4}
        else:
            weekday_values = {5, 6}
        weekday_values = weekday_values.difference({weekday_lookup[day] for day in exclusions})
        return next_matching_date(weekday_values)

    monthly_weekday_match = re.fullmatch(
        rf"(?:the\s+)?(?P<occurrence>{core.ORDINAL_OCCURRENCE_PATTERN})\s+"
        rf"(?P<weekday>{core.WEEKDAY_PATTERN})\s+of\s+"
        r"(?:each|every)\s+month",
        base_phrase,
    )
    if monthly_weekday_match is not None:
        weekday = weekday_lookup[core.normalize_weekday_name(monthly_weekday_match.group("weekday"))]
        occurrence = core.ORDINAL_OCCURRENCE_MAP[monthly_weekday_match.group("occurrence")]
        year = reference.get_year()
        month = reference.get_month() + 1
        for _ in range(24):
            if occurrence > 0:
                candidate_date = core.nth_weekday_of_month(year, month, weekday, occurrence)
            elif occurrence == -1:
                candidate_date = core.last_weekday_of_month(year, month, weekday)
            else:
                candidate_date = core.penultimate_weekday_of_month(year, month, weekday)
            candidate = candidate_from_date(candidate_date)
            if candidate_is_valid(candidate):
                return apply_schedule_time(candidate)
            month += 1
            if month > 12:
                month = 1
                year += 1

    nth_weekday_match = re.fullmatch(
        rf"every\s+(?P<ordinal>{core.POSITIVE_ORDINAL_OCCURRENCE_PATTERN})\s+(?P<weekday>{core.WEEKDAY_PATTERN})",
        base_phrase,
    )
    if nth_weekday_match is not None:
        occurrence = core.ORDINAL_OCCURRENCE_MAP[nth_weekday_match.group("ordinal")]
        weekday = weekday_lookup[core.normalize_weekday_name(nth_weekday_match.group("weekday"))]
        year = reference.get_year()
        month = reference.get_month() + 1
        for _ in range(24):
            candidate_date = core.nth_weekday_of_month(year, month, weekday, occurrence)
            candidate = candidate_from_date(candidate_date)
            if candidate_is_valid(candidate):
                return apply_schedule_time(candidate)
            month += 1
            if month > 12:
                month = 1
                year += 1

    monthly_business_match = re.fullmatch(
        rf"(?:the\s+)?(?P<occurrence>{core.BUSINESS_QUARTERLY_ORDINAL_PATTERN})\s+(?:business|working)\s+day\s+of\s+(?:each|every)\s+month",
        base_phrase,
    )
    if monthly_business_match is not None:
        occurrence = monthly_business_match.group("occurrence")
        year = reference.get_year()
        month = reference.get_month() + 1
        for _ in range(24):
            if occurrence in {"first", "1st"}:
                candidate = first_business_day_of_month(year, month)
            else:
                candidate = last_business_day_of_month(year, month)
            if candidate_is_valid(candidate):
                return apply_schedule_time(candidate)
            month += 1
            if month > 12:
                month = 1
                year += 1

    third_business_match = re.fullmatch(
        rf"(?:the\s+)?(?P<occurrence>{core.BUSINESS_MONTHLY_ORDINAL_PATTERN})\s+(?:business|working)\s+day\s+of\s+(?:each|every)\s+month",
        base_phrase,
    )
    if third_business_match is not None:
        if core.ORDINAL_OCCURRENCE_MAP[third_business_match.group("occurrence")] != 3:
            return None
        year = reference.get_year()
        month = reference.get_month() + 1
        for _ in range(24):
            candidate = core.shift_business_days(first_business_day_of_month(year, month), 2)
            if candidate_is_valid(candidate):
                return apply_schedule_time(candidate)
            month += 1
            if month > 12:
                month = 1
                year += 1

    weekend_of_month_match = re.fullmatch(
        rf"(?:the\s+)?(?P<occurrence>{core.WEEKEND_ORDINAL_PATTERN})\s+weekend\s+of\s+(?:each|every)\s+month",
        base_phrase,
    )
    if weekend_of_month_match is not None:
        year = reference.get_year()
        month = reference.get_month() + 1
        for _ in range(24):
            if weekend_of_month_match.group("occurrence") == "first":
                candidate = core.build_calendar_anchor_date(year, month, 1)
                while candidate.to_datetime().weekday() != 5:
                    candidate.set_date(candidate.get_date() + 1)
            else:
                candidate = core.build_calendar_anchor_date(
                    year, month, core.stDate.get_month_length(month, year)
                )
                while candidate.to_datetime().weekday() != 6:
                    candidate.set_date(candidate.get_date() - 1)
                candidate.set_date(candidate.get_date() - 1)
            if candidate_is_valid(candidate):
                return apply_schedule_time(candidate)
            month += 1
            if month > 12:
                month = 1
                year += 1

    monthly_day_match = re.fullmatch(
        rf"(?:every\s+month\s+on\s+|on\s+)?(?:the\s+)?(?P<day>{core.DATE_ORDINAL_PATTERN})\s+of\s+(?:each|every)\s+month|every\s+month\s+on\s+(?:the\s+)?(?P<day_alt>{core.DATE_ORDINAL_PATTERN})",
        base_phrase,
    )
    if monthly_day_match is not None:
        raw_day = monthly_day_match.group("day") or monthly_day_match.group("day_alt")
        target_day = core.ORDINAL_DAY_MAP.get(raw_day)
        year = reference.get_year()
        month = reference.get_month() + 1
        for _ in range(24):
            last_day = core.stDate.get_month_length(month, year)
            if target_day <= last_day:
                candidate = core.build_calendar_anchor_date(year, month, target_day)
                if candidate_is_valid(candidate):
                    return apply_schedule_time(candidate)
            month += 1
            if month > 12:
                month = 1
                year += 1

    interval_month_day_match = re.fullmatch(
        rf"every\s+(?P<count>\d+)(?:st|nd|rd|th)?\s+months?\s+on\s+(?:the\s+)?(?P<day>{core.DATE_ORDINAL_PATTERN})",
        base_phrase,
    )
    if interval_month_day_match is not None:
        count = int(interval_month_day_match.group("count"))
        target_day = core.ORDINAL_DAY_MAP.get(interval_month_day_match.group("day"))
        month = reference.get_month() + 1
        year = reference.get_year()
        for _ in range(24):
            month += count
            while month > 12:
                month -= 12
                year += 1
            if target_day > core.stDate.get_month_length(month, year):
                continue
            candidate = core.build_calendar_anchor_date(year, month, target_day)
            if candidate_is_valid(candidate):
                return apply_schedule_time(candidate)

    yearly_holiday_match = re.fullmatch(
        r"every\s+(?P<anchor>(?:christmas|boxing day|christmas eve|new year's day|new years day|halloween|easter))",
        base_phrase,
    )
    if yearly_holiday_match is not None:
        anchor_text = yearly_holiday_match.group("anchor")
        for year in range(reference.get_year(), reference.get_year() + 12):
            shifted_reference = core.clone_date(reference)
            shifted_reference.set_fullyear(year)
            candidate = core.parse_natural_date_strict(anchor_text, relative_to=shifted_reference)
            if candidate is None:
                continue
            if candidate_is_valid(candidate):
                return apply_schedule_time(candidate)

    yearly_month_day_match = re.fullmatch(
        rf"every\s+(?:(?P<month>{month_names})\s+(?P<day>\d{{1,2}}(?:st|nd|rd|th))|(?:the\s+)?(?P<day_first>\d{{1,2}}(?:st|nd|rd|th))\s+of\s+(?P<month_first>{month_names}))",
        base_phrase,
    )
    if yearly_month_day_match is not None:
        month_name = core.normalize_month_name(
            yearly_month_day_match.group("month")
            or yearly_month_day_match.group("month_first")
        )
        day_text = yearly_month_day_match.group("day") or yearly_month_day_match.group("day_first")
        month = core.MONTH_INDEX[month_name]
        day = int(re.match(r"\d+", day_text).group(0))
        for year in range(reference.get_year(), reference.get_year() + 12):
            if day > core.stDate.get_month_length(month, year):
                continue
            candidate = core.build_calendar_anchor_date(year, month, day)
            if candidate_is_valid(candidate):
                return apply_schedule_time(candidate)

    yearly_month_weekday_match = re.fullmatch(
        rf"(?:the\s+)?(?P<occurrence>{core.ORDINAL_OCCURRENCE_PATTERN})\s+"
        rf"(?P<weekday>{core.WEEKDAY_PATTERN})\s+of\s+every\s+(?P<month>{month_names})",
        base_phrase,
    )
    if yearly_month_weekday_match is not None:
        occurrence = core.ORDINAL_OCCURRENCE_MAP[yearly_month_weekday_match.group("occurrence")]
        weekday = weekday_lookup[core.normalize_weekday_name(yearly_month_weekday_match.group("weekday"))]
        month = core.MONTH_INDEX[core.normalize_month_name(yearly_month_weekday_match.group("month"))]
        for year in range(reference.get_year(), reference.get_year() + 12):
            if occurrence > 0:
                candidate_date = core.nth_weekday_of_month(year, month, weekday, occurrence)
            elif occurrence == -1:
                candidate_date = core.last_weekday_of_month(year, month, weekday)
            else:
                candidate_date = core.penultimate_weekday_of_month(year, month, weekday)
            candidate = candidate_from_date(candidate_date)
            if candidate_is_valid(candidate):
                return apply_schedule_time(candidate)

    yearly_in_month_match = re.fullmatch(
        rf"every\s+(?P<ordinal>{core.ORDINAL_OCCURRENCE_PATTERN})\s+(?P<weekday>{core.WEEKDAY_PATTERN})\s+in\s+(?P<month>{month_names})",
        base_phrase,
    )
    if yearly_in_month_match is not None:
        occurrence = core.ORDINAL_OCCURRENCE_MAP[yearly_in_month_match.group("ordinal")]
        weekday = weekday_lookup[core.normalize_weekday_name(yearly_in_month_match.group("weekday"))]
        month = core.MONTH_INDEX[core.normalize_month_name(yearly_in_month_match.group("month"))]
        for year in range(reference.get_year(), reference.get_year() + 12):
            candidate_date = core.nth_weekday_of_month(year, month, weekday, occurrence)
            candidate = candidate_from_date(candidate_date)
            if candidate_is_valid(candidate):
                return apply_schedule_time(candidate)

    yearly_of_year_match = re.fullmatch(
        rf"(?:the\s+)?(?P<occurrence>{core.ORDINAL_OCCURRENCE_PATTERN})\s+(?P<weekday>{core.WEEKDAY_PATTERN})\s+of\s+every\s+year",
        base_phrase,
    )
    if yearly_of_year_match is not None:
        occurrence = core.ORDINAL_OCCURRENCE_MAP[yearly_of_year_match.group("occurrence")]
        weekday = weekday_lookup[core.normalize_weekday_name(yearly_of_year_match.group("weekday"))]
        for year in range(reference.get_year(), reference.get_year() + 12):
            if occurrence > 0:
                candidate_date = core.nth_weekday_of_year(year, weekday, occurrence)
            elif occurrence == -1:
                candidate_date = core.last_weekday_of_year(year, weekday)
            else:
                candidate_date = core.penultimate_weekday_of_year(year, weekday)
            candidate = candidate_from_date(candidate_date)
            if candidate_is_valid(candidate):
                return apply_schedule_time(candidate)

    recurring_business_day_match = re.fullmatch(
        r"every\s+(?:business|working)\s+day",
        base_phrase,
    )
    if recurring_business_day_match is not None:
        weekday_values = {0, 1, 2, 3, 4}.difference(
            {weekday_lookup[day] for day in exclusions}
        )
        return next_matching_date(weekday_values)

    quarterly_business_match = re.fullmatch(
        rf"(?:the\s+)?(?P<occurrence>{core.BUSINESS_QUARTERLY_ORDINAL_PATTERN})\s+(?:business|working)\s+day\s+of\s+(?:each|every)\s+quarter",
        base_phrase,
    )
    if quarterly_business_match is not None:
        occurrence = quarterly_business_match.group("occurrence")
        current_month = reference.get_month() + 1
        quarter = ((current_month - 1) // 3) + 1
        year = reference.get_year()
        for _ in range(12):
            start_month = core.quarter_start_month(quarter)
            if occurrence in {"first", "1st"}:
                candidate = first_business_day_of_month(year, start_month)
            else:
                candidate = last_business_day_of_month(year, start_month + 2)
            if candidate_is_valid(candidate):
                return apply_schedule_time(candidate)
            quarter += 1
            if quarter > 4:
                quarter = 1
                year += 1

    weekday_match = re.fullmatch(
        rf"(?:on\s+)?(?:(?:every)\s+)?(?P<weekday>{core.WEEKDAY_PATTERN})s|every\s+(?P<singular>{core.WEEKDAY_PATTERN})",
        base_phrase,
    )
    if weekday_match is not None:
        weekday_name = core.normalize_weekday_name(
            weekday_match.group("weekday") or weekday_match.group("singular")
        )
        if weekday_name in exclusions:
            return None
        return next_matching_date({weekday_lookup[weekday_name]})

    return None
