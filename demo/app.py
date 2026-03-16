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

from stringtime import Date, extract_dates, parse_natural_date_strict

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
    normalized = re.sub(r"^(?:and|then|at|on|in|@)\s+", "", normalized, flags=re.I)
    normalized = re.sub(r"^@\s*", "", normalized)
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


def _month_number_from_text(text):
    lowered = text.lower().strip()
    months = {
        "january": 1,
        "jan": 1,
        "february": 2,
        "feb": 2,
        "march": 3,
        "mar": 3,
        "april": 4,
        "apr": 4,
        "may": 5,
        "june": 6,
        "jun": 6,
        "july": 7,
        "jul": 7,
        "august": 8,
        "aug": 8,
        "september": 9,
        "sep": 9,
        "sept": 9,
        "october": 10,
        "oct": 10,
        "november": 11,
        "nov": 11,
        "december": 12,
        "dec": 12,
    }
    return months.get(lowered)


def _is_clock_like_text(text):
    lowered = text.lower().strip()
    return bool(
        re.fullmatch(r"@?\d{1,2}(?::\d{2})?(?::\d{2})?\s?(?:am|pm)?", lowered)
        or re.fullmatch(
            r"(?:about|around)\s+\d{1,2}(?::\d{2})?ish|\d{1,2}(?::\d{2})?ish", lowered
        )
        or re.search(
            r"\b(?:am|pm|noon|midnight|midday|morning|afternoon|evening|night|past|to|quarter|half)\b",
            lowered,
        )
    )


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


def _parse_demo_component_chunk(chunk, options):
    normalized = _normalize_chunk(chunk)
    if not normalized:
        return None

    if re.fullmatch(r"\d{4}", normalized):
        year = int(normalized)
        return {
            "text": normalized,
            "kind": "year",
            "date": {
                "display": normalized,
                "iso": f"{year:04d}-01-01T00:00:00",
                "year": year,
                "month": 1,
                "day": 1,
                "hour": 0,
                "minute": 0,
                "second": 0,
                "weekday": datetime(year, 1, 1).weekday(),
                "metadata": {
                    "semantic_kind": "date",
                    "representative_granularity": "year",
                },
            },
        }

    month_number = _month_number_from_text(normalized)
    if month_number is not None:
        reference = _reference_datetime(options)
        year = reference.year
        return {
            "text": normalized,
            "kind": "month",
            "date": {
                "display": f"{year:04d}-{month_number:02d}-01 00:00:00",
                "iso": f"{year:04d}-{month_number:02d}-01T00:00:00",
                "year": year,
                "month": month_number,
                "day": 1,
                "hour": 0,
                "minute": 0,
                "second": 0,
                "weekday": datetime(year, month_number, 1).weekday(),
                "metadata": {
                    "semantic_kind": "period",
                    "representative_granularity": "month",
                },
            },
        }

    parsed_clock = _parse_demo_clock_chunk(normalized, options)
    parsed_date = parse_natural_date_strict(normalized.lower(), **options)
    if parsed_clock is None and parsed_date is None:
        return None

    if parsed_clock is not None:
        return {
            "text": normalized,
            "kind": "clock_phrase",
            "date": datetime_to_payload(parsed_clock),
        }

    payload = date_to_payload(parsed_date)
    metadata = payload.get("metadata") or {}
    granularity = metadata.get("representative_granularity")
    kind = "date_fragment"
    if granularity == "year":
        kind = "year"
    elif granularity == "month":
        kind = "month"
    elif _is_clock_like_text(normalized):
        kind = "clock_phrase"

    return {
        "text": normalized,
        "kind": kind,
        "date": payload,
    }


def _find_additional_components(phrase, matches, options):
    components = []
    seen = set()
    cursor = 0

    def add_component_chunk(raw_chunk):
        for piece in re.split(r"[,.!?;]+", raw_chunk):
            component = _parse_demo_component_chunk(piece, options)
            if component is None:
                continue
            key = (component["kind"], component["text"].lower())
            if key in seen:
                continue
            seen.add(key)
            components.append(component)

    for match in matches:
        if cursor < match.start:
            add_component_chunk(phrase[cursor : match.start])
        cursor = match.end

    if cursor < len(phrase):
        add_component_chunk(phrase[cursor:])

    return components


def _weekday_index_from_text(text):
    lowered = text.lower()
    weekday_aliases = {
        0: ("monday", "mon"),
        1: ("tuesday", "tues", "tue"),
        2: ("wednesday", "weds", "wed"),
        3: ("thursday", "thurs", "thur", "thu"),
        4: ("friday", "fri"),
        5: ("saturday", "sat"),
        6: ("sunday", "sun"),
    }
    for index, aliases in weekday_aliases.items():
        if any(re.search(rf"\b{alias}\b", lowered) for alias in aliases):
            return index
    return None


def _apply_time(dt, time_payload):
    return dt.replace(
        hour=time_payload["hour"],
        minute=time_payload["minute"],
        second=time_payload["second"],
    )


def _resolve_component_year(component):
    text = component["text"].lower()
    if component["kind"] == "year":
        return component["date"]["year"]
    if re.fullmatch(r"\d{4}", text):
        return int(text)
    if re.search(r"\b(?:last|next|this)\s+year\b", text):
        return component["date"]["year"]
    return None


def _choose_exact_day_component(components):
    def score(component):
        text = component["text"].lower()
        metadata = component["date"]["metadata"] or {}
        granularity = metadata.get("representative_granularity")
        if re.search(r"\b(today|tomorrow|yesterday)\b", text):
            return 3
        if granularity != "day":
            return -1
        if _weekday_index_from_text(text) is not None:
            return -1
        if re.search(
            r"\b\d{1,2}(?:st|nd|rd|th)\b|\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth)\b",
            text,
        ):
            return 4
        return 1

    ranked = sorted(components, key=score, reverse=True)
    if not ranked or score(ranked[0]) < 0:
        return None
    return ranked[0]


def build_aggregation_suggestion(phrase, options):
    matches = extract_dates(phrase, **options)
    if not matches:
        return None

    components = [
        {
            "text": match.text,
            "kind": "extracted_match",
            "date": date_to_payload(match.date),
        }
        for match in matches
    ]
    components.extend(_find_additional_components(phrase, matches, options))

    if len(matches) == 1 and len(components) == 1:
        match = matches[0]
        return {
            "used": True,
            "status": "suggested",
            "message": "Observed one strong extracted date phrase inside the input and promoted it as a suggested result.",
            "consumed_parts": [match.text],
            "components": components,
            "candidate_dates": [],
            "suggested_date": date_to_payload(match.date),
        }

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
            if component["kind"] == "month"
            or (
                component["date"]["metadata"]
                and component["date"]["metadata"].get("representative_granularity")
                == "month"
            )
        ),
        None,
    )
    year_component = next(
        (
            component
            for component in components
            if _resolve_component_year(component) is not None
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
    exact_day_component = _choose_exact_day_component(components)

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

    if month_component and exact_day_component:
        month_payload = month_component["date"]
        day_payload = exact_day_component["date"]
        year = (
            _resolve_component_year(year_component)
            if year_component is not None
            else month_payload["year"]
        )
        dt = datetime(
            year,
            month_payload["month"],
            day_payload["day"],
            0,
            0,
            0,
        )
        if time_component is not None:
            dt = _apply_time(dt, time_component["date"])

        parts = [exact_day_component["text"], month_component["text"]]
        if year_component is not None:
            parts.insert(0, year_component["text"])
        if time_component is not None:
            parts.insert(0, time_component["text"])

        return {
            "used": True,
            "status": "suggested",
            "message": "Aggregated extracted parts into a suggested date.",
            "consumed_parts": parts,
            "components": components,
            "candidate_dates": [],
            "suggested_date": datetime_to_payload(dt),
        }

    if month_component and weekday_component:
        month_payload = month_component["date"]
        weekday_index = _weekday_index_from_text(weekday_component["text"])
        year = (
            year_component["date"]["year"]
            if year_component is not None
            else month_payload["year"]
        )
        month = month_payload["month"]
        _, last_day = calendar.monthrange(year, month)
        candidates = []
        for day in range(1, last_day + 1):
            dt = datetime(year, month, day, 0, 0, 0)
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
        if year_component is not None:
            parts.append(year_component["text"])

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
        else:
            parsed = Date(phrase, **options)
            fallback_only = is_fallback_date(parsed)
            aggregation = (
                build_aggregation_suggestion(phrase, options) if fallback_only else None
            )
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
