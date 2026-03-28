import pytest

from stringtime import Date

pytestmark = [pytest.mark.parser]


@pytest.mark.parametrize(
    "phrase, expected",
    [
        ("now", "2020-12-25 17:05:55"),
        ("tomorrow", "2020-12-26 17:05:55"),
        ("yesterday", "2020-12-24 17:05:55"),
        ("in a minute", "2020-12-25 17:06:55"),
        ("10 minutes ago", "2020-12-25 16:55:55"),
        ("2 weeks from now", "2021-01-08 17:05:55"),
        ("today at noon", "2020-12-25 12:00:00"),
        ("today 5 pm", "2020-12-25 17:00:00"),
        ("5 oclock", "2020-12-25 05:00:00"),
        ("2:57pm", "2020-12-25 14:57:00"),
        ("quarter past 5", "2020-12-25 05:15:00"),
        ("half past 5", "2020-12-25 05:30:00"),
        ("quarter to 6", "2020-12-25 05:45:00"),
        ("Wednesday", "2020-12-30 17:05:55"),
        ("wednesday at 5 pm", "2020-12-30 17:00:00"),
        ("the first Monday in May", "2020-05-04 17:05:55"),
        ("the last Friday in June", "2020-06-26 17:05:55"),
        ("April the 1st", "2020-04-01 17:05:55"),
        ("the 16th of december 1997", "1997-12-16 17:05:55"),
        ("last month", "2020-11-25 17:05:55"),
        ("next year", "2021-12-25 17:05:55"),
        ("end of month", "2020-12-31 17:05:55"),
        ("start of week", "2020-12-21 17:05:55"),
        ("tomorrow night", "2020-12-26 21:00:00"),
        ("in the afternoon", "2020-12-26 15:00:00"),
        ("christmas", "2020-12-25 17:05:55"),
        ("easter", "2020-04-12 17:05:55"),
        ("full moon", "2020-12-29 22:44:26"),
        ("spring equinox", "2021-03-20 12:00:00"),
        ("fiscal year end", "2020-12-31 17:05:55"),
        ("the first business day after fiscal year end", "2021-01-01 17:05:55"),
        ("2 days before monday", "2020-12-26 17:05:55"),
        ("2 days after tomorrow", "2020-12-28 17:05:55"),
        ("3 decembers time", "2023-12-01 17:05:55"),
        ("5 fridays ago", "2020-11-20 17:05:55"),
        ("every wednesday at 3pm", "2020-12-30 15:00:00"),
        ("every christmas", "2021-12-25 17:05:55"),
        ("forever", "∞"),
    ],
)
def test_canonical_phrase_families(phrase, expected):
    assert str(Date(phrase)) == expected


def test_canonical_extract_smoke():
    matches = Date("can you come 2moz at 7ish", extract=True)

    assert len(matches) == 1
    assert matches[0].text == "2moz at 7ish"
    assert str(matches[0].date) == "2020-12-26 07:00:00"


def test_canonical_relative_to_smoke():
    assert (
        str(Date("1 years ago at 2pm", relative_to="2020-12-25 17:05:55"))
        == "2019-12-25 14:00:00"
    )


def test_canonical_parse_metadata_smoke():
    parsed = Date("Friday")

    assert parsed.parse_metadata.exact is True
    assert parsed.parse_metadata.semantic_kind == "period"
    assert parsed.parse_metadata.representative_granularity == "day"
