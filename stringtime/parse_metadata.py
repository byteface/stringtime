from dataclasses import dataclass


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
    recurrence_frequency: str | None = None
    recurrence_interval: int | None = None
    recurrence_byweekday: tuple[str, ...] | None = None
    recurrence_bymonth: int | None = None
    recurrence_bymonthday: int | None = None
    recurrence_ordinal: str | None = None
    recurrence_byhour: int | None = None
    recurrence_byminute: int | None = None
    recurrence_until: str | None = None
    recurrence_start: str | None = None
    recurrence_exclusions: tuple[str, ...] | None = None
    recurrence_window_start: str | None = None
    recurrence_window_end: str | None = None


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
    import stringtime as core

    if semantic_kind is None or representative_granularity is None:
        semantic_kind, representative_granularity = core.infer_phrase_semantics(
            normalized_text
        )
    recurrence_details = core.infer_recurring_details(normalized_text)
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
        recurrence_details.get(key) is not None for key in recurring_signal_keys
    )
    if semantic_kind != "recurring" and has_recurring_signal:
        semantic_kind = "recurring"
        representative_granularity = core.get_recurring_schedule_granularity(
            normalized_text
        )
    if semantic_kind == "recurring":
        if recurrence_frequency is None:
            recurrence_frequency = recurrence_details.get("recurrence_frequency")
        if recurrence_interval is None:
            recurrence_interval = recurrence_details.get("recurrence_interval")
        if recurrence_byweekday is None:
            recurrence_byweekday = recurrence_details.get("recurrence_byweekday")
        if recurrence_bymonth is None:
            recurrence_bymonth = recurrence_details.get("recurrence_bymonth")
        if recurrence_bymonthday is None:
            recurrence_bymonthday = recurrence_details.get("recurrence_bymonthday")
        if recurrence_ordinal is None:
            recurrence_ordinal = recurrence_details.get("recurrence_ordinal")
        if recurrence_byhour is None:
            recurrence_byhour = recurrence_details.get("recurrence_byhour")
        if recurrence_byminute is None:
            recurrence_byminute = recurrence_details.get("recurrence_byminute")
        if recurrence_until is None:
            recurrence_until = recurrence_details.get("recurrence_until")
        if recurrence_start is None:
            recurrence_start = recurrence_details.get("recurrence_start")
        if recurrence_exclusions is None:
            recurrence_exclusions = recurrence_details.get("recurrence_exclusions")
        if recurrence_window_start is None:
            recurrence_window_start = recurrence_details.get("recurrence_window_start")
        if recurrence_window_end is None:
            recurrence_window_end = recurrence_details.get("recurrence_window_end")
    return ParseMetadata(
        input_text=input_text,
        matched_text=matched_text,
        normalized_text=normalized_text,
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
