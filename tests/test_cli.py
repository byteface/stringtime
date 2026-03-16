import json

from stringtime.__main__ import run


def test_cli_parses_phrase_with_positional_input(capsys):
    result = run(["an", "hour", "from", "now", "--relative-to", "2020-12-25 17:05:55"])

    captured = capsys.readouterr()

    assert str(result) == "2020-12-25 18:05:55"
    assert captured.out.strip() == "2020-12-25 18:05:55"


def test_cli_supports_legacy_phrase_flag(capsys):
    result = run(
        ["--phrase", "tomorrow", "night", "--relative-to", "2020-12-25 17:05:55"]
    )

    captured = capsys.readouterr()

    assert str(result) == "2020-12-26 21:00:00"
    assert captured.out.strip() == "2020-12-26 21:00:00"


def test_cli_extract_mode_outputs_full_match(capsys):
    result = run(
        [
            "--extract",
            "I",
            "will",
            "do",
            "it",
            "in",
            "5",
            "days",
            "from",
            "tomorrow",
            "--relative-to",
            "2020-12-25 17:05:55",
        ]
    )

    captured = capsys.readouterr()

    assert len(result) == 1
    assert result[0].text == "in 5 days from tomorrow"
    assert captured.out.strip() == "2020-12-31 17:05:55"


def test_cli_parse_metadata_json_output(capsys):
    run(
        [
            "--metadata",
            "--json",
            "Friday",
            "--relative-to",
            "2020-12-25 17:05:55",
        ]
    )

    payload = json.loads(capsys.readouterr().out)

    assert payload["date"] == "2020-12-25 17:05:55"
    assert payload["parse_metadata"]["semantic_kind"] == "period"
    assert payload["parse_metadata"]["representative_granularity"] == "day"


def test_cli_extract_mode_can_emit_json_metadata(capsys):
    run(
        [
            "--extract",
            "--json",
            "can",
            "you",
            "come",
            "2moz",
            "at",
            "7ish",
            "--relative-to",
            "2020-12-25 17:05:55",
        ]
    )

    payload = json.loads(capsys.readouterr().out)

    assert payload[0]["text"] == "2moz at 7ish"
    assert payload[0]["date"] == "2020-12-26 07:00:00"
    assert payload[0]["parse_metadata"]["fuzzy"] is True


def test_cli_help_mentions_new_modes(capsys):
    try:
        run(["--help"])
    except SystemExit as exc:
        assert exc.code == 0

    output = capsys.readouterr().out

    assert "--extract" in output
    assert "--relative-to" in output
    assert "examples:" in output
