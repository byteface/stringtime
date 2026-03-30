import calendar
import datetime
import re


def get_registered_anchor_definitions(*args, timezone_aware=False, **kwargs):
    import stringtime as core

    return (
        core.AnchorDefinition("special", ("event", "named"), lambda phrase: core.get_special_phrase_date(phrase)),
        core.AnchorDefinition("holiday", ("event", "calendar"), lambda phrase: core.get_holiday_date(phrase)),
        core.AnchorDefinition("solar", ("event", "astronomical"), lambda phrase: core.get_solar_event_phrase_date(phrase, *args, timezone_aware=timezone_aware, **kwargs)),
        core.AnchorDefinition("moon", ("event", "astronomical"), lambda phrase: core.get_moon_phase_phrase_date(phrase)),
        core.AnchorDefinition("named_lunar", ("event", "astronomical"), lambda phrase: core.get_named_lunar_event_date(phrase)),
        core.AnchorDefinition("season", ("event", "structural", "calendar"), lambda phrase: core.get_season_anchor_date(phrase)),
        core.AnchorDefinition("solstice_equinox", ("event", "astronomical", "calendar"), lambda phrase: core.get_solstice_equinox_date(phrase)),
        core.AnchorDefinition("quarter", ("structural", "boundary"), lambda phrase: core.get_quarter_phrase_date(phrase)),
        core.AnchorDefinition("boundary", ("structural", "boundary"), lambda phrase: core.get_boundary_phrase_date(phrase)),
        core.AnchorDefinition("ordinal_weekday", ("structural", "calendar"), lambda phrase: core.get_ordinal_weekday_date(phrase)),
        core.AnchorDefinition("month_anchor", ("structural", "calendar"), lambda phrase: core.get_month_anchor_date(phrase)),
        core.AnchorDefinition("half_period", ("structural", "calendar"), lambda phrase: core.get_half_period_anchor_date(phrase)),
        core.AnchorDefinition("week_of_month", ("structural", "calendar"), lambda phrase: core.get_week_of_month_anchor_date(phrase)),
        core.AnchorDefinition("day_of_year", ("structural", "calendar"), lambda phrase: core.get_day_of_year_phrase_date(phrase)),
        core.AnchorDefinition("leap_anchor", ("structural", "calendar"), lambda phrase: core.get_leap_year_anchor_date(phrase)),
        core.AnchorDefinition("relative_weekday", ("structural", "relative"), lambda phrase: core.get_relative_weekday_phrase_date(phrase, *args, timezone_aware=timezone_aware, **kwargs)),
        core.AnchorDefinition("recurring_week", ("event", "structural", "calendar"), lambda phrase: core.get_recurring_week_anchor_date(phrase)),
        core.AnchorDefinition("fiscal", ("event", "structural", "business"), lambda phrase: core.get_fiscal_anchor_date(phrase)),
    )


def resolve_registered_anchor(phrase, *args, families=None, timezone_aware=False, **kwargs):
    import stringtime as core

    requested_families = set(families or ())
    reference = (
        core.coerce_reference_date(kwargs["relative_to"])
        if "relative_to" in kwargs and kwargs["relative_to"] is not None
        else core.get_reference_date()
    )
    token = core.CURRENT_REFERENCE.set(reference)
    try:
        for definition in get_registered_anchor_definitions(*args, timezone_aware=timezone_aware, **kwargs):
            if requested_families and requested_families.isdisjoint(definition.families):
                continue
            resolved = definition.resolver(phrase)
            if resolved is not None:
                return resolved, definition
    finally:
        core.CURRENT_REFERENCE.reset(token)
    return None, None


def get_anchor_metadata_overrides(definition):
    if definition is None:
        return {}
    if definition.name == "month_anchor":
        return {"semantic_kind": "period", "representative_granularity": "month"}
    if definition.name == "half_period":
        return {"semantic_kind": "period", "representative_granularity": "half"}
    if definition.name == "week_of_month":
        return {"semantic_kind": "period", "representative_granularity": "week"}
    if definition.name in {"leap_anchor"}:
        return {"semantic_kind": "period", "representative_granularity": "year"}
    if definition.name in {"day_of_year"}:
        return {"semantic_kind": "period", "representative_granularity": "day"}
    if definition.name in {"moon", "solar", "named_lunar", "solstice_equinox"}:
        return {"semantic_kind": "instant", "representative_granularity": "second"}
    if definition.name in {"season"}:
        return {"semantic_kind": "period", "representative_granularity": "season"}
    if definition.name in {"recurring_week"}:
        return {"semantic_kind": "period", "representative_granularity": "week"}
    if definition.name in {"fiscal"}:
        return {"semantic_kind": "boundary", "representative_granularity": "quarter"}
    return {}


def resolve_with_optional_leading_article(text, resolver, *args, timezone_aware=False, **kwargs):
    if not text:
        return None
    resolved = resolver(text, *args, timezone_aware=timezone_aware, **kwargs)
    if resolved is not None:
        return resolved
    normalized_text = re.sub(r"^the\s+", "", text)
    if normalized_text != text:
        return resolver(normalized_text, *args, timezone_aware=timezone_aware, **kwargs)
    return None


def parse_anchor_date(anchor_text, *args, timezone_aware=False, **kwargs):
    import stringtime as core

    anchor_date, _definition = resolve_registered_anchor(
        anchor_text, *args, families={"event", "structural"}, timezone_aware=timezone_aware, **kwargs
    )
    if anchor_date is None:
        anchor_date = core.parse_natural_date_strict(anchor_text, *args, timezone_aware=timezone_aware, **kwargs)
    return anchor_date


def resolve_anchor_target_text(text, *args, timezone_aware=False, **kwargs):
    return resolve_with_optional_leading_article(text, parse_anchor_date, *args, timezone_aware=timezone_aware, **kwargs)


def resolve_date_target_text(text, *args, timezone_aware=False, **kwargs):
    import stringtime as core

    return resolve_with_optional_leading_article(
        text,
        core.parse_natural_date_strict,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )


def resolve_nested_anchor_date_text(text, *args, timezone_aware=False, **kwargs):
    import stringtime as core

    def nested_resolver(candidate, *resolver_args, timezone_aware=False, **resolver_kwargs):
        anchor_date, _definition = resolve_registered_anchor(
            candidate, *resolver_args, families={"event", "structural"}, timezone_aware=timezone_aware, **resolver_kwargs
        )
        if anchor_date is not None:
            return anchor_date
        for resolver in (
            core.get_ordinal_time_coordinate_date,
            core.get_anchor_offset_phrase_date,
            core.get_relative_month_day_phrase_date,
            core.get_weekday_in_month_date,
            core.get_weekday_occurrence_period_phrase_date,
            core.get_weekday_anchor_date,
            core.get_ordinal_weekday_anchor_date,
            core.get_counted_weekday_anchor_date,
            core.get_ordinal_month_year_date,
            core.get_business_phrase_date,
            core.get_quarter_phrase_date,
            core.get_fiscal_anchor_date,
            core.get_season_anchor_date,
            core.get_solstice_equinox_date,
            core.get_month_anchor_date,
            core.get_week_of_month_anchor_date,
            core.get_leap_year_anchor_date,
            core.get_recurring_week_anchor_date,
        ):
            try:
                resolved = resolver(candidate, *resolver_args, timezone_aware=timezone_aware, **resolver_kwargs)
            except TypeError:
                resolved = resolver(candidate)
            if resolved is not None:
                return resolved
        return None

    return resolve_with_optional_leading_article(
        text,
        nested_resolver,
        *args,
        timezone_aware=timezone_aware,
        **kwargs,
    )


def parse_anchor_like_text(candidate, *args, timezone_aware=False, **kwargs):
    if not candidate:
        return None
    return resolve_anchor_target_text(candidate, *args, timezone_aware=timezone_aware, **kwargs)


def resolve_period_year_month(period):
    import stringtime as core

    period = period.strip()
    reference = core.get_reference_date()
    reference_year = reference.get_year()
    reference_month = reference.get_month() + 1

    if period in core.MONTH_INDEX:
        return reference_year, core.MONTH_INDEX[period]

    relative_named_month_match = re.fullmatch(
        rf"(?P<relation>last|next|this)\s+(?P<month>{core.MONTH_PATTERN})",
        period,
    )
    if relative_named_month_match is not None:
        month = core.MONTH_INDEX[relative_named_month_match.group("month")]
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
        rf"(?P<month>{core.MONTH_PATTERN})\s+(?P<year>\d{{2}}|\d{{4}})",
        period,
    )
    if month_year_match is not None:
        raw_year = month_year_match.group("year")
        return (
            core.coerce_two_digit_year(raw_year) if len(raw_year) == 2 else int(raw_year),
            core.MONTH_INDEX[month_year_match.group("month")],
        )

    if period in {"month", "the month", "this month"}:
        return reference_year, reference_month

    ordinal_month_match = re.fullmatch(
        rf"(?:the\s+)?(?P<month>{core.ORDINAL_MONTH_RE})\s+month(?:\s+(?P<year>\d{{2}}|\d{{4}}))?",
        period,
    )
    if ordinal_month_match is not None:
        raw_year = ordinal_month_match.group("year")
        year = (
            (
                core.coerce_two_digit_year(raw_year)
                if raw_year is not None and len(raw_year) == 2
                else int(raw_year)
            )
            if raw_year is not None
            else reference_year
        )
        return year, core.ORDINAL_MONTH_MAP[ordinal_month_match.group("month")]

    relative_period_date = get_relative_period_phrase_date(period)
    if relative_period_date is not None and period in {"next month", "last month"}:
        dt = relative_period_date.to_datetime()
        return dt.year, dt.month

    if re.fullmatch(r"\d{4}", period):
        return int(period), 1

    return None


def resolve_year_phrase(period):
    import stringtime as core

    period = period.strip()
    reference = core.get_reference_date()
    current_century_start = (reference.get_year() // 100) * 100

    explicit_year_match = re.fullmatch(r"(?:the\s+)?year\s+(?P<year>\d{2}|\d{4})", period)
    if explicit_year_match is not None:
        raw_year = explicit_year_match.group("year")
        return (
            core.coerce_two_digit_year(raw_year)
            if len(raw_year) == 2
            else int(raw_year)
        )

    if period in {"year", "the year", "this year"}:
        return reference.get_year()
    relative_period_date = get_relative_period_phrase_date(period)
    if relative_period_date is not None and period in {"next year", "last year"}:
        return relative_period_date.get_year()
    if period in {"century", "the century", "this century"}:
        return current_century_start
    if period == "next century":
        return current_century_start + 100
    if period == "last century":
        return current_century_start - 100
    if re.fullmatch(r"\d{2}|\d{4}", period):
        return core.coerce_two_digit_year(period) if len(period) == 2 else int(period)
    return None


def resolve_quarter_year(quarter_phrase):
    import stringtime as core

    quarter_phrase = quarter_phrase.strip()
    reference = core.get_reference_date()

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
        d = core.get_reference_date()
        d.set_month(d.get_month() + 3)
        month = d.get_month() + 1
        quarter = ((month - 1) // 3) + 1
        return d.get_year(), quarter

    if quarter_phrase == "last quarter":
        d = core.get_reference_date()
        d.set_month(d.get_month() - 3)
        month = d.get_month() + 1
        quarter = ((month - 1) // 3) + 1
        return d.get_year(), quarter

    return None


def get_ordinal_weekday_date(phrase):
    import stringtime as core

    phrase = re.sub(r"^(?:on|in)\s+", "", phrase)
    pattern = (
        rf"(?:the\s+)?(?P<occurrence>{core.ORDINAL_OCCURRENCE_PATTERN})\s+"
        rf"(?P<weekday>{core.WEEKDAY_RE})\s+(?:in|of)\s+(?P<period>.+)"
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
        two_digit_match = re.fullmatch(
            rf"(?:the\s+)?(?P<occurrence>{core.ORDINAL_OCCURRENCE_PATTERN})\s+"
            rf"(?P<weekday>{core.WEEKDAY_RE})\s+(?:in|of)\s+"
            rf"(?P<period>.+?)\s+(?P<year>\d{{2}})",
            phrase,
        )
        if two_digit_match is not None:
            phrase = (
                f"{two_digit_match.group('occurrence')} {two_digit_match.group('weekday')} "
                f"of {two_digit_match.group('period')} "
                f"{core.coerce_two_digit_year(two_digit_match.group('year'))}"
            )
            match = re.fullmatch(pattern, phrase)
    if match is None:
        return None

    occurrence = match.group("occurrence")
    weekday_name = match.group("weekday")
    period = match.group("period")
    year_match = re.fullmatch(r"\d{4}", period)

    weekday = core.WEEKDAY_INDEX[weekday_name]
    resolved_year = resolve_year_phrase(period)

    if year_match is not None or resolved_year is not None:
        year = int(period) if year_match is not None else resolved_year
        if occurrence in {"first", "1st"}:
            date_value = core.nth_weekday_of_year(year, weekday, 1)
        elif occurrence in {"second", "2nd"}:
            date_value = core.nth_weekday_of_year(year, weekday, 2)
        elif occurrence in {"third", "3rd"}:
            date_value = core.nth_weekday_of_year(year, weekday, 3)
        elif occurrence in {"fourth", "4th"}:
            date_value = core.nth_weekday_of_year(year, weekday, 4)
        elif occurrence in {"fifth", "5th"}:
            date_value = core.nth_weekday_of_year(year, weekday, 5)
        elif occurrence == "last":
            date_value = core.last_weekday_of_year(year, weekday)
        else:
            date_value = core.penultimate_weekday_of_year(year, weekday)
    else:
        resolved = resolve_period_year_month(period)
        if resolved is None:
            anchor_date = parse_anchor_like_text(period)
            if anchor_date is None:
                return None
            year, month = anchor_date.get_year(), anchor_date.get_month() + 1
        else:
            year, month = resolved
        if occurrence in {"first", "1st"}:
            date_value = core.nth_weekday_of_month(year, month, weekday, 1)
        elif occurrence in {"second", "2nd"}:
            date_value = core.nth_weekday_of_month(year, month, weekday, 2)
        elif occurrence in {"third", "3rd"}:
            date_value = core.nth_weekday_of_month(year, month, weekday, 3)
        elif occurrence in {"fourth", "4th"}:
            date_value = core.nth_weekday_of_month(year, month, weekday, 4)
        elif occurrence in {"fifth", "5th"}:
            date_value = core.nth_weekday_of_month(year, month, weekday, 5)
        elif occurrence == "last":
            date_value = core.last_weekday_of_month(year, month, weekday)
        else:
            date_value = core.penultimate_weekday_of_month(year, month, weekday)

    d = core.get_reference_date()
    d.set_fullyear(date_value.year)
    d.set_month(date_value.month - 1)
    d.set_date(date_value.day)
    return d


def get_weekday_occurrence_period_date(phrase):
    import stringtime as core

    pattern = (
        rf"(?P<weekday>{core.WEEKDAY_RE})\s+"
        rf"(?:the\s+)?(?P<occurrence>{core.POSITIVE_ORDINAL_OCCURRENCE_PATTERN})\s+"
        r"of\s+(?P<period>.+)"
    )
    match = re.fullmatch(pattern, phrase)
    if match is None:
        return None

    resolved = resolve_period_year_month(match.group("period"))
    if resolved is None:
        return None

    year, month = resolved
    date_value = core.nth_weekday_of_month(
        year,
        month,
        core.WEEKDAY_INDEX[match.group("weekday")],
        core.ORDINAL_OCCURRENCE_MAP[match.group("occurrence")],
    )
    d = core.get_reference_date()
    d.set_fullyear(date_value.year)
    d.set_month(date_value.month - 1)
    d.set_date(date_value.day)
    return d


def get_ordinal_month_year_date(phrase):
    import stringtime as core

    phrase = re.sub(r"^on\s+", "", phrase)
    ordinal_day_lookup = core.ORDINAL_DAY_MAP
    month_lookup = core.MONTH_INDEX
    ordinal_month_lookup = core.ORDINAL_MONTH_MAP
    word_year_lookup = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
        "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
        "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
        "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
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
    day_pattern = core.DATE_ORDINAL_PATTERN
    month_pattern = core.MONTH_OR_ORDINAL_MONTH_PATTERN

    relative_named_month_match = re.fullmatch(
        rf"(?P<relation>last|next|this)\s+(?P<month>{core.MONTH_RE})\s+(?P<day>{day_pattern})",
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

        month_name = core.normalize_month_name(relative_named_month_match.group("month"))
        if month_name is None:
            return None
        month = month_lookup[month_name]
        relation = relative_named_month_match.group("relation")
        reference = core.get_reference_date()
        year = reference.get_year()
        reference_month = reference.get_month() + 1

        if relation == "next":
            if month <= reference_month:
                year += 1
        elif relation == "last":
            if month >= reference_month:
                year -= 1

        return core.build_calendar_anchor_date(year, month, day)

    month_first_match = re.fullmatch(
        rf"(?P<month>{core.MONTH_RE})\s+(?:the\s+)?(?P<day>{day_pattern})(?:[,.]?\s+(?P<year>{year_pattern}))?",
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

        month_name = core.normalize_month_name(month_first_match.group("month"))
        if month_name is None:
            return None
        month = month_lookup[month_name]
        raw_year = month_first_match.group("year")
        reference = core.get_reference_date()
        if raw_year is None:
            year = reference.get_year()
        else:
            year = parse_year_value(raw_year)
            if year is None:
                return None

        return core.build_calendar_anchor_date(year, month, day)

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
        year = core.get_reference_date().get_year()
    else:
        year = parse_year_value(raw_year)
        if year is None:
            return None

    return core.build_calendar_anchor_date(year, month, day)


def get_quarter_phrase_date(phrase):
    import stringtime as core

    reference = core.get_reference_date()

    match = re.fullmatch(r"(start|end)\s+of\s+(q[1-4])(?:\s+(\d{4}))?", phrase)
    if match is not None:
        quarter_phrase = match.group(2)
        if match.group(3):
            quarter_phrase = f"{quarter_phrase} {match.group(3)}"
        year, quarter = resolve_quarter_year(quarter_phrase)
        start_month = core.quarter_start_month(quarter)
        d = core.clone_date(reference)
        d.set_fullyear(year)
        d.set_month(start_month - 1)
        d.set_date(1)
        if match.group(1) == "end":
            d.set_month(start_month + 2 - 1)
            last_day = core.stDate.get_month_length(start_month + 2, year)
            d.set_date(last_day)
        return d

    match = re.fullmatch(r"mid\s+(q[1-4])(?:\s+(\d{4}))?", phrase)
    if match is not None:
        quarter_phrase = match.group(1)
        if match.group(2):
            quarter_phrase = f"{quarter_phrase} {match.group(2)}"
        year, quarter = resolve_quarter_year(quarter_phrase)
        start_month = core.quarter_start_month(quarter)
        d = core.clone_date(reference)
        d.set_fullyear(year)
        d.set_month(start_month)
        d.set_date(15)
        return d

    match = re.fullmatch(r"(first|last)\s+day\s+of\s+(this|next|last)\s+quarter", phrase)
    if match is not None:
        year, quarter = resolve_quarter_year(f"{match.group(2)} quarter")
        start_month = core.quarter_start_month(quarter)
        d = core.clone_date(reference)
        d.set_fullyear(year)
        if match.group(1) == "first":
            d.set_month(start_month - 1)
            d.set_date(1)
        else:
            end_month = start_month + 2
            d.set_month(end_month - 1)
            d.set_date(core.stDate.get_month_length(end_month, year))
        return d

    return None


def get_weekday_occurrence_period_phrase_date(phrase):
    import stringtime as core

    match = re.fullmatch(
        rf"(?P<weekday>{core.WEEKDAY_RE})\s+(?:the\s+)?(?P<occurrence>1st|2nd|3rd|4th|5th|first|second|third|fourth|fifth)\s+of\s+(?P<period>.+)",
        phrase,
    )
    if match is None:
        return None

    resolved = resolve_period_year_month(match.group("period"))
    if resolved is None:
        return None

    year, month = resolved
    date_value = core.nth_weekday_of_month(
        year,
        month,
        core.WEEKDAY_INDEX[match.group("weekday")],
        core.ORDINAL_OCCURRENCE_MAP[match.group("occurrence")],
    )
    d = core.get_reference_date()
    d.set_fullyear(date_value.year)
    d.set_month(date_value.month - 1)
    d.set_date(date_value.day)
    return d


def get_relative_period_phrase_date(phrase):
    import stringtime as core

    after_next_match = re.fullmatch(
        r"(?:the\s+)?(?P<unit>week|month|year)\s+after\s+next",
        phrase,
    )
    if after_next_match is not None:
        relation = "after next"
        unit = after_next_match.group("unit")
    else:
        match = re.fullmatch(
            r"(?:the\s+)?(?P<relation>last|next|this)\s+(?P<unit>week|month|year)",
            phrase,
        )
        if match is None:
            return None
        relation = match.group("relation")
        unit = match.group("unit")

    d = core.get_reference_date()

    if relation == "this":
        return d
    step = 2 if relation == "after next" else (1 if relation == "next" else -1)
    if unit == "week":
        d.set_date(d.get_date() + (7 * step))
        return d
    if unit == "month":
        d.set_month(d.get_month() + step)
        return d

    d.set_year(d.get_year() + step)
    return d


def get_half_period_anchor_date(phrase):
    import stringtime as core

    match = re.fullmatch(
        r"(?:the\s+)?(?P<half>first|second|1st|2nd)\s+half\s+of\s+(?P<period>.+)",
        phrase,
    )
    if match is None:
        return None

    period = match.group("period").strip()
    half = match.group("half")
    start_month = 1 if half in {"first", "1st"} else 7

    resolved_year = resolve_year_phrase(period)
    if resolved_year is not None:
        year = resolved_year
    else:
        period_date = core.parse_natural_date_strict(period)
        if period_date is None:
            return None
        year = period_date.get_year()

    return core.build_calendar_anchor_date(year, start_month, 1)


def get_relative_month_day_phrase_date(phrase):
    import stringtime as core

    match = re.fullmatch(
        rf"(?P<relation>last|next)\s+month\s+on\s+(?:the\s+)?(?P<day>{core.DATE_ORDINAL_PATTERN})",
        phrase,
    )
    day_lookup = core.ORDINAL_DAY_MAP

    if match is None:
        match = re.fullmatch(
            rf"(?:the\s+)?(?P<day>{core.DATE_ORDINAL_PATTERN})\s+(?:of\s+)?(?P<relation>last|next)\s+month",
            phrase,
        )
    if match is None:
        match = re.fullmatch(
            rf"(?:the\s+)?(?P<day>{core.DATE_ORDINAL_PATTERN})\s+(?P<relation>last|next|this)\s+(?P<month>{core.MONTH_RE})",
            phrase,
        )
        if match is not None:
            raw_day = match.group("day")
            ordinal_match = re.fullmatch(r"(\d+)(?:st|nd|rd|th)?", raw_day)
            if ordinal_match is not None:
                day = int(ordinal_match.group(1))
            else:
                day = day_lookup.get(raw_day)
            if day is None:
                return None

            month_name = core.normalize_month_name(match.group("month"))
            if month_name is None:
                return None
            month = core.MONTH_INDEX[month_name]
            relation = match.group("relation")
            reference = core.get_reference_date()
            year = reference.get_year()
            reference_month = reference.get_month() + 1
            if relation == "next":
                if month <= reference_month:
                    year += 1
            elif relation == "last":
                if month >= reference_month:
                    year -= 1
            if day > core.stDate.get_month_length(month, year):
                return None
            return core.build_calendar_anchor_date(year, month, day)
    if match is None:
        return None

    raw_day = match.group("day")
    ordinal_match = re.fullmatch(r"(\d+)(?:st|nd|rd|th)?", raw_day)
    if ordinal_match is not None:
        day = int(ordinal_match.group(1))
    else:
        day = day_lookup.get(raw_day)
    if day is None:
        return None

    d = core.clone_date(core.get_reference_date())
    d.set_month(d.get_month() + (1 if match.group("relation") == "next" else -1))
    target_year = d.get_year()
    target_month = d.get_month() + 1
    if day > core.stDate.get_month_length(target_month, target_year):
        return None
    d.set_date(day)
    return d


def get_boundary_phrase_date(phrase):
    import stringtime as core

    reference = core.get_reference_date()
    month_lookup = core.MONTH_INDEX

    match = re.fullmatch(
        r"(?:the\s+)?(?P<boundary>start|end|close)\s+of\s+(?:the\s+)?(?P<period>next month|last month|this month|next year|last year|this year)",
        phrase,
    )
    if match is not None:
        d = core.clone_date(reference)
        period = match.group("period")
        boundary = "end" if match.group("boundary") == "close" else match.group("boundary")
        if period == "next month":
            d.set_month(d.get_month() + 1)
        elif period == "last month":
            d.set_month(d.get_month() - 1)
        elif period == "next year":
            d.set_fullyear(d.get_year() + 1)
        elif period == "last year":
            d.set_fullyear(d.get_year() - 1)

        if "month" in period:
            if boundary == "start":
                d.set_date(1)
            else:
                d.set_date(core.stDate.get_month_length(d.get_month() + 1, d.get_year()))
        else:
            if boundary == "start":
                d.set_month(0)
                d.set_date(1)
            else:
                d.set_month(11)
                d.set_date(31)
        return d

    match = re.fullmatch(
        rf"(?:the\s+)?(first|1st|last)\s+day\s+(?:of|in)\s+(?:the\s+month\s+of\s+)?(?P<month>{core.MONTH_RE})(?:\s+(?P<year>\d{{4}}))?",
        phrase,
    )
    if match is not None:
        target_month = month_lookup[match.group("month")]
        target_year = int(match.group("year")) if match.group("year") is not None else reference.get_year()
        d = core.clone_date(reference)
        d.set_fullyear(target_year)
        d.set_month(target_month - 1)
        if match.group(1) in {"first", "1st"}:
            d.set_date(1)
        else:
            d.set_date(core.stDate.get_month_length(target_month, target_year))
        return d

    match = re.fullmatch(
        rf"(?:on\s+)?(?:the\s+)?(?P<position>first|1st|last)\s+day\s+of\s+the\s+month\s+in\s+(?P<month>{core.MONTH_RE})(?:\s+(?P<year>\d{{4}}))?",
        phrase,
    )
    if match is not None:
        target_month = month_lookup[match.group("month")]
        target_year = int(match.group("year")) if match.group("year") is not None else reference.get_year()
        d = core.clone_date(reference)
        d.set_fullyear(target_year)
        d.set_month(target_month - 1)
        if match.group("position") in {"first", "1st"}:
            d.set_date(1)
        else:
            d.set_date(core.stDate.get_month_length(target_month, target_year))
        return d

    match = re.fullmatch(
        r"(?:the\s+)?second\s+to\s+last\s+day\s+(?:of|in)\s+(?:the\s+)?(?P<period>month|year)",
        phrase,
    )
    if match is not None:
        d = core.clone_date(reference)
        if match.group("period") == "month":
            d.set_date(core.stDate.get_month_length(d.get_month() + 1, d.get_year()) - 1)
        else:
            d.set_month(11)
            d.set_date(30)
        return d

    match = re.fullmatch(
        r"(?:the\s+)?(?P<position>penultimate|second\s+to\s+last)\s+day\s+(?:of|in)\s+(?P<period>next month|last month|this month)",
        phrase,
    )
    if match is not None:
        d = core.clone_date(reference)
        if match.group("period") == "next month":
            d.set_month(d.get_month() + 1)
        elif match.group("period") == "last month":
            d.set_month(d.get_month() - 1)
        d.set_date(core.stDate.get_month_length(d.get_month() + 1, d.get_year()) - 1)
        return d

    match = re.fullmatch(
        rf"(?:the\s+)?(?P<position>first|1st|last|second\s+to\s+last)\s+day\s+(?:of|in)\s+(?:the\s+)?(?P<month>{core.MONTH_RE})(?:\s+(?P<year>next year|last year|this year|\d{{4}}))?",
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

        d = core.clone_date(reference)
        d.set_fullyear(target_year)
        d.set_month(target_month - 1)
        if match.group("position") in {"first", "1st"}:
            d.set_date(1)
        elif match.group("position") == "second to last":
            d.set_date(core.stDate.get_month_length(target_month, target_year) - 1)
        else:
            d.set_date(core.stDate.get_month_length(target_month, target_year))
        return d

    match = re.fullmatch(
        rf"(?:the\s+)?(start|end|close)\s+of\s+(?:the\s+)?(?P<month>{core.MONTH_RE})",
        phrase,
    )
    if match is not None:
        target_month = month_lookup[match.group("month")]
        target_year = reference.get_year()
        d = core.clone_date(reference)
        d.set_fullyear(target_year)
        d.set_month(target_month - 1)
        if match.group(1) == "start":
            d.set_date(1)
        else:
            d.set_date(core.stDate.get_month_length(target_month, target_year))

        if d.to_datetime().replace(tzinfo=None) < reference.to_datetime().replace(tzinfo=None):
            target_year += 1
            d.set_fullyear(target_year)
            d.set_month(target_month - 1)
            if match.group(1) == "start":
                d.set_date(1)
            else:
                d.set_date(core.stDate.get_month_length(target_month, target_year))
        return d

    match = re.fullmatch(r"(start|end|close)\s+of\s+(?:the\s+)?(month|year)", phrase)
    if match is not None:
        boundary = "end" if match.group(1) == "close" else match.group(1)
        period = match.group(2)
        d = core.clone_date(reference)
        if period == "month":
            if boundary == "start":
                d.set_date(1)
            else:
                last_day = core.stDate.get_month_length(d.get_month() + 1, d.get_year())
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
        d = core.clone_date(reference)
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
    import stringtime as core

    month_lookup = core.MONTH_INDEX
    ordinal_month_lookup = core.ORDINAL_MONTH_MAP

    half_match = re.fullmatch(
        rf"(?:the\s+)?(?P<half>first|second)\s+half\s+of\s+(?P<month>{core.MONTH_RE})(?:\s+(?P<year>\d{{4}}))?",
        phrase,
    )
    mid_match = re.fullmatch(
        rf"(?:(?:the\s+)?(?P<edge>middle)\s+of\s+|(?P<bare_mid>mid)[- ]+)(?P<month>{core.MONTH_RE})(?:\s+(?P<year>\d{{4}}))?",
        phrase,
    )
    use_end_of_month = False
    use_middle_of_month = False
    half_day = None
    explicit_year = None
    if half_match is not None:
        target_month = month_lookup[half_match.group("month")]
        half_day = 1 if half_match.group("half") == "first" else 16
        explicit_year = int(half_match.group("year")) if half_match.group("year") is not None else None
    elif mid_match is not None:
        target_month = month_lookup[mid_match.group("month")]
        use_middle_of_month = True
        explicit_year = int(mid_match.group("year")) if mid_match.group("year") is not None else None
    else:
        match = re.fullmatch(
            rf"(?:(?P<boundary>end of)\s+)?(?P<month>{core.MONTH_RE})(?:\s+(?P<year>\d{{4}}))?(?:\s+(?P<edge>finishes|ends))?",
            phrase,
        )
        if match is not None:
            target_month = month_lookup[match.group("month")]
            use_end_of_month = match.group("boundary") is not None or match.group("edge") is not None
            explicit_year = int(match.group("year")) if match.group("year") is not None else None
        else:
            ordinal_match = re.fullmatch(
                rf"(?:the\s+)?(?P<month>{core.ORDINAL_MONTH_RE})\s+month(?:\s+of\s+the\s+year)?(?:\s+(?P<year>\d{{4}}))?",
                phrase,
            )
            if ordinal_match is None:
                return None
            target_month = ordinal_month_lookup[ordinal_match.group("month")]
            explicit_year = int(ordinal_match.group("year")) if ordinal_match.group("year") is not None else None

    reference = core.get_reference_date()
    reference_dt = reference.to_datetime().replace(tzinfo=None)
    year = explicit_year if explicit_year is not None else reference_dt.year
    d = core.clone_date(reference)

    def set_month_anchor_year(target_year):
        d.set_date(1)
        d.set_fullyear(target_year)
        d.set_month(target_month - 1)
        if use_end_of_month:
            last_day = core.stDate.get_month_length(target_month, target_year)
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
    import stringtime as core

    week_lookup = {
        "1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "5th": 5,
        "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    }
    match = re.fullmatch(
        r"(?:the\s+)?(?P<week>1st|2nd|3rd|4th|5th|first|second|third|fourth|fifth|last)\s+week\s+(?:of|in)\s+(?P<period>.+)",
        phrase,
    )
    if match is None:
        return None

    raw_week = match.group("week")
    period = match.group("period").strip()
    reference = core.get_reference_date()
    reference_dt = reference.to_datetime().replace(tzinfo=None)
    d = core.clone_date(reference)
    explicit_year_in_period = bool(
        re.search(r"\b\d{4}\b", period)
        or re.fullmatch(
            rf"(?:the\s+)?(?:{core.ORDINAL_MONTH_RE})\s+month",
            period,
        )
        or re.fullmatch(
            rf"(?:{core.MONTH_PATTERN})\s+\d{{4}}",
            period,
        )
    )

    resolved_year = resolve_year_phrase(period)
    if resolved_year is not None:
        d.set_fullyear(resolved_year)
        d.set_month(0)
        day = 25 if raw_week == "last" else 1
        if raw_week != "last":
            week_number = week_lookup[raw_week]
            day = ((week_number - 1) * 7) + 1
        d.set_date(day)
        return d

    resolved = resolve_period_year_month(period)
    if resolved is None:
        return None
    year, month = resolved

    def set_week_anchor_year(target_year):
        if raw_week == "last":
            day = max(1, core.stDate.get_month_length(month, target_year) - 6)
        else:
            week_number = week_lookup[raw_week]
            day = ((week_number - 1) * 7) + 1
        if day > core.stDate.get_month_length(month, target_year):
            return False
        d.set_fullyear(target_year)
        d.set_month(month - 1)
        d.set_date(day)
        return True

    if not set_week_anchor_year(year):
        return None
    if not explicit_year_in_period and d.to_datetime().replace(tzinfo=None) < reference_dt:
        year += 1
        if not set_week_anchor_year(year):
            return None
    return d


def get_leap_year_anchor_date(phrase):
    import stringtime as core

    match = re.fullmatch(r"(?:the\s+)?(?P<which>next|last)\s+leap\s+year", phrase)
    if match is None:
        return None

    reference = core.get_reference_date()
    year = reference.get_year()
    step = 1 if match.group("which") == "next" else -1
    candidate = year + step

    while not calendar.isleap(candidate):
        candidate += step

    d = core.clone_date(reference)
    d.set_date(1)
    d.set_fullyear(candidate)
    d.set_month(0)
    return d
