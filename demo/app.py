from __future__ import annotations

import calendar
import dataclasses
import json
import os
import pathlib
import re
import sys
from datetime import datetime

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from flask import Flask, jsonify, render_template, request
except ImportError as exc:  # pragma: no cover - convenience for local demo use
    raise SystemExit(
        "Flask is required for the demo app. Install requirements-dev.txt first."
    ) from exc

from stringtime import (
    Date,
    Phrase,
    extract_dates,
    nearest_phrase_for,
    nearest_phrases_for,
    parse_natural_date_strict,
    phrase_for,
    phrases_for,
)


app = Flask(__name__, template_folder="templates", static_folder="static")


EXAMPLE_PHRASES = [
    "tomorrow night",
    "3 days from next Wednesday",
    "the second to last day of the month",
    "tmrw@7",
    "5m ago",
    "1y from now",
    "the first Monday in May",
    "the fourteenth week after xmas",
    "twilight on the wednesday",
    "the day before the twelth second of the 14th minute on the 2nd week of the first month 2321",
]


def date_to_payload(date_obj):
    metadata = getattr(date_obj, "parse_metadata", None)
    metadata_payload = dataclasses.asdict(metadata) if metadata is not None else None
    dt = date_obj.to_datetime()
    return {
        "display": str(date_obj),
        "iso": dt.isoformat(),
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
        "hour": dt.hour,
        "minute": dt.minute,
        "second": dt.second,
        "weekday": dt.weekday(),
        "metadata": metadata_payload,
    }


def datetime_to_payload(dt, metadata=None):
    return {
        "display": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "iso": dt.isoformat(),
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
        "hour": dt.hour,
        "minute": dt.minute,
        "second": dt.second,
        "weekday": dt.weekday(),
        "metadata": metadata,
    }


def is_fallback_date(date_obj):
    metadata = getattr(date_obj, "parse_metadata", None)
    return bool(metadata is not None and metadata.used_dateutil)


def match_to_payload(match):
    return {
        "text": match.text,
        "start": match.start,
        "end": match.end,
        "date": date_to_payload(match.date),
    }


def _normalize_chunk(chunk):
    normalized = re.sub(r"\s+", " ", chunk.strip(" ,.;:-")).strip()
    normalized = re.sub(r"^(?:and|then|at|on|in)\s+", "", normalized, flags=re.I)
    return normalized.strip()


def _word_number(value):
    words = {
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
    }
    if value.isdigit():
        return int(value)
    return words.get(value)


def _reference_datetime(options):
    relative_to = options.get("relative_to")
    return Date(relative_to or "now").to_datetime()


def _parse_demo_clock_chunk(chunk, options):
    lowered = chunk.lower().strip()
    match = re.fullmatch(
        r"(?P<amount>\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\s+"
        r"(?P<direction>past|to)\s+"
        r"(?P<hour>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)",
        lowered,
    )
    if match is None:
        return None

    amount = _word_number(match.group("amount"))
    hour = _word_number(match.group("hour"))
    if amount is None or hour is None:
        return None

    reference = _reference_datetime(options)
    if match.group("direction") == "past":
        parsed_hour = hour % 24
        parsed_minute = amount
    else:
        parsed_hour = (hour - 1) % 24
        parsed_minute = 60 - amount

    return datetime(
        reference.year,
        reference.month,
        reference.day,
        parsed_hour,
        parsed_minute,
        0,
    )


def _find_additional_components(phrase, matches, options):
    components = []
    cursor = 0
    for match in matches:
        if cursor < match.start:
            chunk = _normalize_chunk(phrase[cursor:match.start])
            if chunk:
                clock_date = _parse_demo_clock_chunk(chunk, options)
                if clock_date is None:
                    clock_date = parse_natural_date_strict(chunk.lower(), **options)
                if clock_date is not None:
                    components.append(
                        {
                            "text": chunk,
                            "kind": "clock_phrase",
                            "date": datetime_to_payload(clock_date)
                            if isinstance(clock_date, datetime)
                            else date_to_payload(clock_date),
                        }
                    )
        cursor = match.end

    if cursor < len(phrase):
        chunk = _normalize_chunk(phrase[cursor:])
        if chunk:
            clock_date = _parse_demo_clock_chunk(chunk, options)
            if clock_date is None:
                clock_date = parse_natural_date_strict(chunk.lower(), **options)
            if clock_date is not None:
                components.append(
                    {
                        "text": chunk,
                        "kind": "clock_phrase",
                        "date": datetime_to_payload(clock_date)
                        if isinstance(clock_date, datetime)
                        else date_to_payload(clock_date),
                    }
                )

    return components


def _weekday_index_from_text(text):
    lowered = text.lower()
    weekdays = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]
    for index, weekday in enumerate(weekdays):
        if weekday in lowered:
            return index
    return None


def _apply_time(dt, time_payload):
    return dt.replace(
        hour=time_payload["hour"],
        minute=time_payload["minute"],
        second=time_payload["second"],
    )


def build_aggregation_suggestion(phrase, options):
    matches = extract_dates(phrase, **options)
    if not matches:
        return None

    if len(matches) == 1:
        match = matches[0]
        return {
            "used": True,
            "status": "suggested",
            "message": "Observed one strong extracted date phrase inside the input and promoted it as a suggested result.",
            "consumed_parts": [match.text],
            "components": [
                {
                    "text": match.text,
                    "kind": "extracted_match",
                    "date": date_to_payload(match.date),
                }
            ],
            "candidate_dates": [],
            "suggested_date": date_to_payload(match.date),
        }

    components = [
        {
            "text": match.text,
            "kind": "extracted_match",
            "date": date_to_payload(match.date),
        }
        for match in matches
    ]
    components.extend(_find_additional_components(phrase, matches, options))

    time_component = next(
        (
            component
            for component in components
            if component["kind"] == "clock_phrase"
            or (
                component["date"]["metadata"]
                and component["date"]["metadata"].get("representative_granularity")
                in {"minute", "second"}
            )
        ),
        None,
    )
    month_component = next(
        (
            component
            for component in components
            if component["date"]["metadata"]
            and component["date"]["metadata"].get("representative_granularity") == "month"
        ),
        None,
    )
    weekday_component = next(
        (
            component
            for component in components
            if component["date"]["metadata"]
            and component["date"]["metadata"].get("representative_granularity") == "day"
            and _weekday_index_from_text(component["text"]) is not None
        ),
        None,
    )
    exact_day_component = next(
        (
            component
            for component in components
            if component["date"]["metadata"]
            and component["date"]["metadata"].get("representative_granularity") == "day"
            and _weekday_index_from_text(component["text"]) is None
        ),
        None,
    )

    if exact_day_component and time_component:
        base_payload = exact_day_component["date"]
        dt = datetime(
            base_payload["year"],
            base_payload["month"],
            base_payload["day"],
            base_payload["hour"],
            base_payload["minute"],
            base_payload["second"],
        )
        dt = _apply_time(dt, time_component["date"])
        return {
            "used": True,
            "status": "suggested",
            "message": "Aggregated extracted parts into a suggested datetime.",
            "consumed_parts": [time_component["text"], exact_day_component["text"]],
            "components": components,
            "candidate_dates": [],
            "suggested_date": datetime_to_payload(dt),
        }

    if month_component and weekday_component:
        month_payload = month_component["date"]
        weekday_index = _weekday_index_from_text(weekday_component["text"])
        year = month_payload["year"]
        month = month_payload["month"]
        _, last_day = calendar.monthrange(year, month)
        candidates = []
        for day in range(1, last_day + 1):
            dt = datetime(year, month, day, month_payload["hour"], month_payload["minute"], month_payload["second"])
            if dt.weekday() != weekday_index:
                continue
            if time_component is not None:
                dt = _apply_time(dt, time_component["date"])
            candidates.append(datetime_to_payload(dt))

        parts = []
        if time_component is not None:
            parts.append(time_component["text"])
        parts.append(weekday_component["text"])
        parts.append(month_component["text"])

        return {
            "used": True,
            "status": "ambiguous",
            "message": f"Aggregated extracted parts but the phrase is still ambiguous: which {calendar.day_name[weekday_index]} in {calendar.month_name[month]} {year}? ({len(candidates)} candidates)",
            "consumed_parts": parts,
            "components": components,
            "candidate_dates": candidates,
            "suggested_date": None,
        }

    return {
        "used": True,
        "status": "observed_only",
        "message": "Observed extracted parts, but could not compose a stronger suggestion yet.",
        "consumed_parts": [component["text"] for component in components],
        "components": components,
        "candidate_dates": [],
        "suggested_date": None,
    }


@app.get("/")
def index():
    return render_template("index.html", examples=EXAMPLE_PHRASES)


@app.post("/api/parse")
def parse_api():
    payload = request.get_json(silent=True) or {}
    phrase = (payload.get("phrase") or "").strip()
    mode = payload.get("mode") or "parse"
    relative_to = (payload.get("relative_to") or "").strip() or None
    timezone_aware = bool(payload.get("timezone_aware"))
    include_all = bool(payload.get("all"))

    if not phrase:
        return jsonify({"ok": False, "error": "Enter a phrase first."}), 400

    options = {
        "relative_to": relative_to,
        "timezone_aware": timezone_aware,
    }

    try:
        if mode == "extract":
            matches = extract_dates(phrase, **options)
            highlight = matches[0].date if matches else None
            result = {
                "mode": mode,
                "input": phrase,
                "relative_to": relative_to,
                "timezone_aware": timezone_aware,
                "match_count": len(matches),
                "matches": [match_to_payload(match) for match in matches],
                "highlight_date": date_to_payload(highlight) if highlight else None,
            }
        elif mode == "reverse":
            candidates = phrases_for(phrase, relative_to=relative_to)
            if include_all:
                chosen = candidates[0] if candidates else None
                result = {
                    "mode": mode,
                    "input": phrase,
                    "relative_to": relative_to,
                    "timezone_aware": timezone_aware,
                    "phrase": chosen,
                    "phrases": candidates,
                    "highlight_date": date_to_payload(Date(phrase, relative_to=relative_to)) if chosen else None,
                }
            else:
                chosen = phrase_for(phrase, relative_to=relative_to)
                result = {
                    "mode": mode,
                    "input": phrase,
                    "relative_to": relative_to,
                    "timezone_aware": timezone_aware,
                    "phrase": chosen,
                    "phrases": candidates[:1] if chosen else [],
                    "highlight_date": date_to_payload(Date(phrase, relative_to=relative_to)) if chosen else None,
                }
        elif mode == "nearest":
            candidates = nearest_phrases_for(phrase, relative_to=relative_to, limit=6)
            chosen = candidates[0].phrase if candidates else nearest_phrase_for(
                phrase, relative_to=relative_to
            )
            result = {
                "mode": mode,
                "input": phrase,
                "relative_to": relative_to,
                "timezone_aware": timezone_aware,
                "phrase": chosen,
                "candidates": [
                    {
                        "phrase": candidate.phrase,
                        "parsed": candidate.parsed,
                        "delta_seconds": candidate.delta_seconds,
                        "phrase_count": candidate.phrase_count,
                        "categories": candidate.categories,
                        "locales": candidate.locales,
                        "styles": candidate.styles,
                    }
                    for candidate in candidates
                ],
                "highlight_date": date_to_payload(Date(phrase, relative_to=relative_to)) if chosen else None,
            }
        else:
            parsed = Date(phrase, **options)
            fallback_only = is_fallback_date(parsed)
            aggregation = build_aggregation_suggestion(phrase, options) if fallback_only else None
            message = (
                aggregation["message"]
                if aggregation is not None
                else "stringtime does not know this phrase yet, or there is no matching event for that period."
            )
            result = {
                "mode": "parse",
                "input": phrase,
                "relative_to": relative_to,
                "timezone_aware": timezone_aware,
                "recognized": not fallback_only,
                "date": None if fallback_only else date_to_payload(parsed),
                "fallback_date": date_to_payload(parsed) if fallback_only else None,
                "highlight_date": None if fallback_only else date_to_payload(parsed),
                "aggregation": aggregation,
                "message": message if fallback_only else None,
            }
    except Exception as exc:  # pragma: no cover - demo error surface
        return jsonify({"ok": False, "error": str(exc)}), 400

    return jsonify(
        {
            "ok": True,
            "result": result,
            "log": json.dumps(result, indent=2, sort_keys=True),
        }
    )


if __name__ == "__main__":  # pragma: no cover - local entrypoint
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("STRINGTIME_DEMO_PORT", "5050")),
        debug=True,
    )
