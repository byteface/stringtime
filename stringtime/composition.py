import datetime
import re

from stringtime.parse_metadata import build_parse_metadata


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
    import stringtime as core

    if candidate is None:
        return None

    overrides = metadata_overrides or {}
    return core.attach_parse_metadata(
        core.apply_timezone(candidate, tzinfo, timezone_aware=timezone_aware),
        build_parse_metadata(
            raw_text,
            matched_text or raw_text,
            normalized_phrase,
            exact=not fuzzy,
            fuzzy=fuzzy,
            used_dateutil=False,
            **overrides,
        ),
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
    for candidate, metadata_overrides in candidates:
        finalized = finalize_parsed_candidate(
            candidate,
            tzinfo=tzinfo,
            timezone_aware=timezone_aware,
            raw_text=raw_text,
            matched_text=matched_text,
            normalized_phrase=normalized_phrase,
            fuzzy=fuzzy,
            metadata_overrides=metadata_overrides,
        )
        if finalized is not None:
            return finalized
    return None


def finalize_infinity_candidate(
    phrase,
    *,
    raw_text,
    matched_text,
    fuzzy,
):
    import stringtime as core

    if phrase not in {"forever", "for ever", "infinity", "∞"}:
        return None

    infinite_date = core.stDate("forever")
    return core.attach_parse_metadata(
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


def collect_direct_parse_candidates(phrase, *args, timezone_aware=False, **kwargs):
    import stringtime as core

    return {
        "simple_clock_instant_date": core.get_simple_clock_instant_date(phrase),
        "simple_numeric_instant_date": core.get_simple_numeric_instant_date(phrase),
        "leap_year_offset_date": core.get_leap_year_offset_date(phrase),
        "ordinal_time_coordinate_date": core.get_ordinal_time_coordinate_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "compact_offset_date": core.get_compact_offset_phrase_date(phrase),
        "relative_month_day_date": core.get_relative_month_day_phrase_date(phrase),
        "counted_weekday_date": core.get_counted_weekday_phrase_date(phrase),
        "counted_month_date": core.get_counted_month_phrase_date(phrase),
        "counted_holiday_date": core.get_counted_holiday_phrase_date(phrase),
        "weekday_and_date_date": core.get_weekday_and_date_phrase_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "weekday_in_month_date": core.get_weekday_in_month_date(phrase),
        "counted_weekday_anchor_date": core.get_counted_weekday_anchor_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "recurring_weekday_date": core.get_recurring_weekday_date(
            phrase, *args, timezone_aware=timezone_aware, **kwargs
        ),
        "recurring_schedule_date": core.get_recurring_schedule_date(
            phrase, *args, timezone_aware=timezone_aware, **kwargs
        ),
        "weekday_anchor_date": core.get_weekday_anchor_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "ordinal_weekday_anchor_date": core.get_ordinal_weekday_anchor_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "add_subtract_date": get_add_subtract_phrase_date(
            phrase, *args, timezone_aware=timezone_aware
        ),
        "ordinal_month_year_date": core.get_ordinal_month_year_date(phrase),
        "relative_period_date": core.get_relative_period_phrase_date(phrase),
        "weekday_occurrence_period_date": core.get_weekday_occurrence_period_phrase_date(phrase),
        "quarter_phrase_date": core.get_quarter_phrase_date(phrase),
        "month_anchor_date": core.get_month_anchor_date(phrase),
        "week_of_month_anchor_date": core.get_week_of_month_anchor_date(phrase),
        "leap_year_anchor_date": core.get_leap_year_anchor_date(phrase),
        "business_date": core.get_business_phrase_date(phrase),
        "sleep_date": core.get_sleep_phrase_date(phrase),
        "clock_date": core.get_clock_phrase_date(phrase),
        "compound_clock_date": core.get_compound_clock_phrase_date(
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


def finalize_part_of_day_stage(part_of_day_date, **kwargs):
    normalized_phrase = kwargs["normalized_phrase"]
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
        return finalize_parsed_candidate(part_of_day_date, **kwargs)
    return None


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
    import stringtime as core

    recurring_details = core.infer_recurring_details(normalized_phrase)
    recurring_signal_keys = {
        "recurrence_frequency",
        "recurrence_interval",
        "recurrence_byweekday",
        "recurrence_bymonth",
        "recurrence_bymonthday",
        "recurrence_ordinal",
        "recurrence_until",
        "recurrence_start",
        "recurrence_exclusions",
        "recurrence_window_start",
        "recurrence_window_end",
    }
    has_recurring_signal = any(
        recurring_details.get(key) is not None for key in recurring_signal_keys
    )
    if (
        composed_date_time is not None
        and re.search(
            r"(?:\b(?:at|when|past|to|half|quarter|noon|midnight|midday|morning|afternoon|evening|night|dawn|sunrise|sunset|dusk|twilight|business)\b|@)",
            normalized_phrase,
        )
        and (
            not re.search(r"\b(?:before|after|from|hence|ago)\b", normalized_phrase)
            or re.search(r"(?:@| at )\s*\d{1,2}:\d{2}(?::\d{2})?(?:\s?(?:am|pm))?$", normalized_phrase)
            or re.search(r"\bby\b", normalized_phrase)
        )
        and (registered_anchor_definition is None or registered_anchor_definition.name not in {"solar"})
        and not has_recurring_signal
        and not re.match(r"^(?:in|on)\s+the\s+(?:morning|afternoon|evening|night)\b", normalized_phrase)
    ):
        return finalize_parsed_candidate(
            composed_date_time,
            tzinfo=tzinfo,
            timezone_aware=timezone_aware,
            raw_text=raw_text,
            matched_text=matched_text,
            normalized_phrase=normalized_phrase,
            fuzzy=fuzzy,
            metadata_overrides=core.get_composed_metadata_overrides(normalized_phrase),
        )
    return None


def parse_structured_time_text(candidate, *args, reference_override=None, timezone_aware=False, **kwargs):
    import stringtime as core

    if not candidate:
        return None

    def parse_clock_with_part_of_day(value, part):
        clock_date = core.get_clock_phrase_date(value)
        if clock_date is None:
            return None
        hour = clock_date.get_hours()
        if part in {"afternoon", "evening", "night"} and hour < 12:
            hour += 12
        if part == "morning" and hour == 12:
            hour = 0
        d = core.clone_date(clock_date)
        d.set_hours(hour)
        return d

    token = None
    if reference_override is not None:
        token = core.CURRENT_REFERENCE.set(core.clone_date(reference_override))
    try:
        time_date = core.get_clock_phrase_date(candidate)
        if time_date is not None:
            return time_date
        if core.TIME_TOKEN_RE.fullmatch(candidate) or candidate in {"noon", "midnight", "midday"}:
            time_date = core.parse_natural_date_strict(candidate, *args, timezone_aware=timezone_aware, **kwargs)
            if time_date is not None:
                return time_date
        if re.fullmatch(r"\d{1,2}:\d{2}:\d{2}(?:\s?(?:am|pm))?", candidate, re.IGNORECASE):
            time_date = core.parse_natural_date_strict(candidate, *args, timezone_aware=timezone_aware, **kwargs)
            if time_date is not None:
                return time_date
        if re.fullmatch(r"(?:about|around)\s+\d{1,2}(?::\d{2})?(?:ish)?|\d{1,2}(?::\d{2})?ish", candidate, re.IGNORECASE):
            time_date = core.get_simple_clock_instant_date(candidate)
            if time_date is not None:
                return time_date
        part_of_day_match = re.fullmatch(r"(?P<clock>.+?)\s+in\s+the\s+(?P<part>morning|afternoon|evening|night)", candidate)
        if part_of_day_match is not None:
            time_date = parse_clock_with_part_of_day(part_of_day_match.group("clock"), part_of_day_match.group("part"))
            if time_date is not None:
                return time_date
        time_date = core.get_part_of_day_phrase_date(candidate, *args, timezone_aware=timezone_aware, **kwargs)
        if time_date is not None:
            return time_date
        time_date = core.get_business_phrase_date(candidate)
        if time_date is not None:
            return time_date
        if re.fullmatch(r"\d{1,2}", candidate):
            return core.build_structured_time_date(int(candidate), 0, 0)
        return None
    finally:
        if token is not None:
            core.CURRENT_REFERENCE.reset(token)


def try_merge_date_time_pattern(phrase, pattern, *, date_group, time_group, args=(), timezone_aware=False, **kwargs):
    import stringtime as core
    match = re.fullmatch(pattern, phrase)
    if match is None:
        return None
    date_part = core.parse_structured_date_text(match.group(date_group), *args, timezone_aware=timezone_aware, **kwargs)
    if date_part is None:
        return None
    time_part = parse_structured_time_text(match.group(time_group), *args, reference_override=date_part, timezone_aware=timezone_aware, **kwargs)
    if time_part is None:
        return None
    return core.merge_date_with_explicit_time(date_part, time_part)


def try_merge_time_date_pattern(phrase, pattern, *, time_group, date_group, args=(), timezone_aware=False, **kwargs):
    import stringtime as core
    match = re.fullmatch(pattern, phrase)
    if match is None:
        return None
    date_part = core.parse_structured_date_text(match.group(date_group), *args, timezone_aware=timezone_aware, **kwargs)
    if date_part is None:
        return None
    relative_time_merge = core.merge_date_with_relative_time_phrase(date_part, match.group(time_group))
    if relative_time_merge is not None:
        return relative_time_merge
    time_part = parse_structured_time_text(match.group(time_group), *args, reference_override=date_part, timezone_aware=timezone_aware, **kwargs)
    if time_part is None:
        return None
    return core.merge_date_with_explicit_time(date_part, time_part)


def apply_relative_offset(base_date, unit, amount, sign=1):
    import stringtime as core
    d = core.clone_date(base_date)
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
    import stringtime as core
    ordinal_match = re.fullmatch(r"(\d+)(?:st|nd|rd|th)", raw_number)
    if ordinal_match is not None:
        return int(ordinal_match.group(1))
    compound_match = re.fullmatch(r"(?P<tens>twenty|thirty|forty|fifty)(?:[- ](?P<ones>one|two|three|four|five|six|seven|eight|nine))?", raw_number)
    if compound_match is not None:
        tens_values = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}
        ones_values = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}
        value = tens_values[compound_match.group("tens")]
        if compound_match.group("ones") is not None:
            value += ones_values[compound_match.group("ones")]
        return value
    if raw_number == "several":
        return 7
    return core.parse_cardinal_number(raw_number)


def parse_compound_offset(offset_text):
    offset_text = re.sub(r"\bhalf\s+(?:a\s+|an\s+)?millisecond\b", "500 microseconds", offset_text)
    offset_text = re.sub(r"\bhalf\s+(?:a\s+|an\s+)?second\b", "500 milliseconds", offset_text)
    offset_text = re.sub(r"\bhalf\s+(?:a\s+|an\s+)?minute\b", "30 seconds", offset_text)
    offset_text = re.sub(r"\bhalf\s+(?:a\s+|an\s+)?hour\b", "30 minutes", offset_text)
    offset_text = re.sub(r"\bhalf\s+(?:a\s+|an\s+)?day\b", "12 hours", offset_text)
    number_pattern = r"(\\d+(?:st|nd|rd|th)?|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|twenty[- ]one|twenty[- ]two|twenty[- ]three|twenty[- ]four|twenty[- ]five|twenty[- ]six|twenty[- ]seven|twenty[- ]eight|twenty[- ]nine|thirty|thirty[- ]one|thirty[- ]two|thirty[- ]three|thirty[- ]four|thirty[- ]five|thirty[- ]six|thirty[- ]seven|thirty[- ]eight|thirty[- ]nine|forty|forty[- ]one|forty[- ]two|forty[- ]three|forty[- ]four|forty[- ]five|forty[- ]six|forty[- ]seven|forty[- ]eight|forty[- ]nine|fifty|fifty[- ]one|fifty[- ]two|fifty[- ]three|fifty[- ]four|fifty[- ]five|fifty[- ]six|fifty[- ]seven|fifty[- ]eight|fifty[- ]nine)"
    unit_pattern = r"(years?|months?|weeks?|days?|nights?|hours?|minutes?|seconds?|milliseconds?|microseconds?)"
    components = []
    half_match = re.fullmatch(rf"(?P<whole>{number_pattern})\s+(?P<unit>{unit_pattern})\s+and\s+(?:a|an|one)?\s*half", offset_text)
    if half_match is not None:
        amount = parse_offset_number(half_match.group("whole"))
        if amount is None:
            return None
        unit = half_match.group("unit")
        unit = unit[:-1] if unit.endswith("s") else unit
        if unit == "night":
            unit = "day"
        return [(unit, amount + 0.5)]
    for raw_number, raw_unit in re.findall(rf"{number_pattern}\s+{unit_pattern}", offset_text):
        amount = parse_offset_number(raw_number)
        if amount is None:
            return None
        unit = raw_unit[:-1] if raw_unit.endswith("s") else raw_unit
        if unit == "night":
            unit = "day"
        components.append((unit, amount))
    if not components:
        return None
    normalized = re.sub(rf"{number_pattern}\s+{unit_pattern}", "", offset_text)
    normalized = re.sub(r"\b(?:and|,)\b", "", normalized)
    if normalized.strip():
        return None
    return components


def apply_relative_offsets(base_date, components, sign=1):
    import stringtime as core
    d = core.clone_date(base_date)
    for unit, amount in components:
        d = apply_relative_offset(d, unit, amount, sign=sign)
    return d


def get_add_subtract_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    import stringtime as core
    reference = core.get_reference_date()
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
        offset_text = core.replace_short_words(match.group("offset").strip())
        components = parse_compound_offset(offset_text)
        if components is None:
            continue
        anchor_text = match.groupdict().get("anchor")
        if anchor_text is None:
            anchor_date = core.clone_date(reference)
        else:
            anchor_date = core.resolve_date_target_text(anchor_text, *args, timezone_aware=timezone_aware, **kwargs)
            if anchor_date is None:
                continue
        return apply_relative_offsets(anchor_date, components, sign=sign)
    return None


def get_anchor_offset_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    import stringtime as core
    phrase = re.sub(r"^(?:the\s+)?day\s+before\s+", "1 day before ", phrase)
    phrase = re.sub(r"^(?:the\s+)?day\s+after\s+", "1 day after ", phrase)
    shortcut_match = re.fullmatch(r"(?P<offset>.+?)\s+(?:(?P<direction>before|prior|earlier)\s+)?(?P<anchor>today|tomorrow|yesterday)", phrase)
    if shortcut_match is not None:
        components = parse_compound_offset(core.replace_short_words(shortcut_match.group("offset").strip()))
        if components is not None:
            anchor_date = core.resolve_date_target_text(shortcut_match.group("anchor"), *args, timezone_aware=timezone_aware, **kwargs)
            if anchor_date is not None:
                sign = -1 if shortcut_match.group("direction") in {"before", "prior", "earlier"} else 1
                return apply_relative_offsets(anchor_date, components, sign)
    match = re.fullmatch(r"(?:(?:in)\s+)?(?P<offset>.+?)\s+(?P<direction>from|after|before|prior|earlier)\s+(?P<anchor>.+)", phrase)
    if match is None:
        return None
    offset_text = core.replace_short_words(re.sub(r"^(?:the)\s+", "", match.group("offset").strip()))
    components = parse_compound_offset(offset_text)
    if components is None:
        return None
    sign = -1 if match.group("direction") in {"before", "prior", "earlier"} else 1
    anchor_date = core.parse_anchor_like_text(match.group("anchor").strip(), *args, timezone_aware=timezone_aware, **kwargs)
    if anchor_date is None:
        return None
    return apply_relative_offsets(anchor_date, components, sign)


def parse_with_shifted_reference(target_year, text, *args, timezone_aware=False, **kwargs):
    import stringtime as core
    shifted_reference = core.clone_date(core.get_reference_date())
    shifted_reference.set_fullyear(target_year)
    parse_kwargs = dict(kwargs)
    parse_kwargs["relative_to"] = shifted_reference
    return core.parse_natural_date_strict(text, *args, timezone_aware=timezone_aware, **parse_kwargs)


def get_year_wrapped_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    match = re.fullmatch(r"(?P<year>\d{4})\s+(?P<rest>.+)", phrase)
    if match is None:
        return None
    return parse_with_shifted_reference(int(match.group("year")), match.group("rest"), *args, timezone_aware=timezone_aware, **kwargs)


def get_year_suffix_wrapped_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    match = re.fullmatch(r"(?P<rest>.+?)\s+(?P<year>\d{4})", phrase)
    if match is None:
        return None
    target_year = int(match.group("year"))
    inner_date = parse_with_shifted_reference(target_year, match.group("rest"), *args, timezone_aware=timezone_aware, **kwargs)
    if inner_date is None:
        return None
    if inner_date.get_year() != target_year:
        inner_date = __import__("stringtime").clone_date(inner_date)
        inner_date.set_fullyear(target_year)
    return inner_date


def try_merge_date_and_time_texts(date_text, time_text, *args, timezone_aware=False, time_transform=None, **kwargs):
    import stringtime as core
    date_part = core.parse_structured_date_text(date_text, *args, timezone_aware=timezone_aware, **kwargs)
    if date_part is None:
        return None
    if time_transform is not None:
        time_text = time_transform(time_text)
    time_part = parse_structured_time_text(time_text, *args, reference_override=date_part, timezone_aware=timezone_aware, **kwargs)
    if time_part is None:
        return None
    return core.merge_date_with_explicit_time(date_part, time_part)


def try_merge_time_and_date_texts(time_text, date_text, *args, timezone_aware=False, time_transform=None, **kwargs):
    import stringtime as core
    date_part = core.parse_structured_date_text(date_text, *args, timezone_aware=timezone_aware, **kwargs)
    if date_part is None:
        return None
    if time_transform is not None:
        time_text = time_transform(time_text)
    time_part = parse_structured_time_text(time_text, *args, reference_override=date_part, timezone_aware=timezone_aware, **kwargs)
    if time_part is None:
        return None
    return core.merge_date_with_explicit_time(date_part, time_part)


def try_merge_token_split_date_time(phrase, *args, timezone_aware=False, max_tokens=8, **kwargs):
    if "@" in phrase or " at " in f" {phrase} ":
        return None
    tokens = phrase.split()
    max_span = min(len(tokens) - 1, max_tokens)
    for tail_size in range(max_span, 1, -1):
        merged = try_merge_date_and_time_texts(" ".join(tokens[:-tail_size]).strip(), " ".join(tokens[-tail_size:]).strip(), *args, timezone_aware=timezone_aware, **kwargs)
        if merged is not None:
            return merged
    for head_size in range(max_span, 1, -1):
        merged = try_merge_time_and_date_texts(" ".join(tokens[:head_size]).strip(), " ".join(tokens[head_size:]).strip(), *args, timezone_aware=timezone_aware, **kwargs)
        if merged is not None:
            return merged
    return None


def get_composed_date_time_phrase_date(phrase, *args, timezone_aware=False, **kwargs):
    import stringtime as core
    if re.fullmatch(rf"(?:the\s+)?(?:{core.POSITIVE_ORDINAL_OCCURRENCE_PATTERN})\s+week\s+(?:of|in)\s+.+", phrase) and not re.search(r"\s+(?:at|@)\s+", phrase):
        return None
    if re.fullmatch(rf"(?:the\s+)?(?:{core.DATE_ORDINAL_PATTERN})\s+minute\s+on\s+.+", phrase):
        return None
    if re.fullmatch(rf"(?:the\s+)?(?:{core.DATE_ORDINAL_PATTERN})\s+second\s+of\s+(?:the\s+)?(?:{core.DATE_ORDINAL_PATTERN})\s+minute\s+on\s+.+", phrase):
        return None
    for wrapped in (
        get_year_wrapped_phrase_date(phrase, *args, timezone_aware=timezone_aware, **kwargs),
        get_year_suffix_wrapped_phrase_date(phrase, *args, timezone_aware=timezone_aware, **kwargs),
    ):
        if wrapped is not None:
            return wrapped
    bare_date_then_clock_match = re.fullmatch(r"(?P<head>.+?)\s+(?P<tail>\d{1,2}(?::\d{2})?(?::\d{2})?\s?(?:am|pm)|noon|midnight|midday|.+ish)", phrase)
    if bare_date_then_clock_match is not None:
        merged = try_merge_date_and_time_texts(bare_date_then_clock_match.group("head"), bare_date_then_clock_match.group("tail"), *args, timezone_aware=timezone_aware, **kwargs)
        if merged is not None:
            return merged
    token_split_merged = try_merge_token_split_date_time(phrase, *args, timezone_aware=timezone_aware, **kwargs)
    if token_split_merged is not None:
        return token_split_merged
    for pattern in [
        r"(?P<head>.+?)\s+(?:at|@)\s+(?P<tail>.+)",
    ]:
        merged = try_merge_date_time_pattern(phrase, pattern, date_group="head", time_group="tail", args=args, timezone_aware=timezone_aware, **kwargs)
        if merged is not None:
            return merged
    for pattern in [
        r"(?P<time>.+?)\s+on\s+(?P<date>.+)",
        r"(?P<time>.+?)\s+(?P<date>(?:today|tomorrow|yesterday|this|next|last).+)",
    ]:
        merged = try_merge_time_date_pattern(phrase, pattern, time_group="time", date_group="date", args=args, timezone_aware=timezone_aware, **kwargs)
        if merged is not None:
            return merged
    return None
