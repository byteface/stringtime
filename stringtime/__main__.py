"""
stringtime CLI entry point.
"""

import argparse
import json
from dataclasses import asdict, is_dataclass

from stringtime import Date, __version__, extract_dates


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="stringtime",
        description=(
            "Parse natural language dates and extract date phrases from sentences."
        ),
        epilog=(
            "examples:\n"
            '  stringtime "an hour from now"\n'
            '  stringtime --relative-to "2020-12-25 17:05:55" "tomorrow night"\n'
            '  stringtime --extract "I will do it in 5 days from tomorrow"'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="Phrase or datetime input. If omitted, --phrase can still be used.",
    )
    parser.add_argument(
        "-p",
        "--phrase",
        nargs="*",
        default=None,
        help="Deprecated alias for the main positional input.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show the installed stringtime version.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "-e",
        "--extract",
        action="store_true",
        help="Extract matching date phrases from a longer sentence.",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Return all matches in extract mode.",
    )
    parser.add_argument(
        "--relative-to",
        type=str,
        default=None,
        help="Reference datetime to use instead of now for relative phrases.",
    )
    parser.add_argument(
        "--timezone-aware",
        action="store_true",
        help="Keep timezone info when the parsed phrase includes a timezone suffix.",
    )
    parser.add_argument(
        "--metadata",
        action="store_true",
        help="Include parse metadata in normal parse output, or structured match metadata in extract mode.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON output.",
    )
    return parser.parse_args(argv), parser


def _resolve_input_text(arguments):
    if arguments.text:
        return " ".join(arguments.text).strip()
    if arguments.phrase:
        return " ".join(arguments.phrase).strip()
    return None


def _serialize(value):
    if hasattr(value, "to_datetime"):
        return str(value)
    if is_dataclass(value):
        data = asdict(value)
        if "date" in data and hasattr(value, "date"):
            data["date"] = str(value.date)
            metadata = getattr(value.date, "parse_metadata", None)
            if metadata is not None:
                data["parse_metadata"] = asdict(metadata)
        return data
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value


def _print_result(result, *, as_json=False):
    if as_json:
        print(json.dumps(_serialize(result), indent=2))
        return

    if isinstance(result, list):
        for item in result:
            print(item)
        return

    print(result)


def do_things(arguments, parser):
    if arguments.version:
        print(__version__)
        return __version__

    text = _resolve_input_text(arguments)
    if text is None:
        parser.error("a phrase or datetime input is required")

    parse_kwargs = {
        "relative_to": arguments.relative_to,
        "timezone_aware": arguments.timezone_aware,
    }

    if arguments.extract:
        result = extract_dates(text, **parse_kwargs)
        if arguments.metadata or arguments.json:
            _print_result(result, as_json=True)
        elif arguments.all:
            for match in result:
                print(f"{match.text} -> {match.date}")
        elif result:
            print(result[0].date)
        return result

    result = Date(text, **parse_kwargs)
    if arguments.metadata or arguments.json:
        payload = {
            "date": str(result),
            "parse_metadata": (
                asdict(result.parse_metadata)
                if getattr(result, "parse_metadata", None) is not None
                else None
            ),
        }
        _print_result(payload, as_json=True)
    else:
        print(result)
    return result


def run(argv=None):
    args, parser = parse_args(argv)
    return do_things(args, parser)


if __name__ == "__main__":
    run()
