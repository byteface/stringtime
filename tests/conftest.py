import datetime

import pytest

import stringtime

REAL_DATETIME = datetime.datetime
FAKE_NOW = REAL_DATETIME(2020, 12, 25, 17, 5, 55)


class FrozenDateTime(REAL_DATETIME):
    @classmethod
    def now(cls, tz=None):
        if tz is not None:
            return FAKE_NOW.astimezone(tz)
        return FAKE_NOW

    @classmethod
    def utcnow(cls):
        return FAKE_NOW

    @classmethod
    def fromtimestamp(cls, ts, tz=None):
        if tz is not None:
            return REAL_DATETIME.fromtimestamp(ts, tz)
        return REAL_DATETIME.fromtimestamp(ts)


@pytest.fixture(autouse=True)
def freeze_now(monkeypatch):
    monkeypatch.setattr("stringtime.date.datetime.datetime", FrozenDateTime)


@pytest.fixture(autouse=True)
def clear_custom_holiday_registry():
    stringtime.clear_custom_holidays()
    yield
    stringtime.clear_custom_holidays()

