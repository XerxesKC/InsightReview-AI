from datetime import datetime, timedelta, timezone

from app.core.datetime_utils import to_rfc3339


def test_to_rfc3339_formats_naive_datetime_as_utc_z() -> None:
    dt = datetime(2026, 3, 18, 10, 20, 30)
    assert to_rfc3339(dt) == "2026-03-18T10:20:30Z"


def test_to_rfc3339_converts_offset_datetime_to_utc_z() -> None:
    dt = datetime(2026, 3, 18, 18, 20, 30, tzinfo=timezone(timedelta(hours=8)))
    assert to_rfc3339(dt) == "2026-03-18T10:20:30Z"


def test_to_rfc3339_allows_none() -> None:
    assert to_rfc3339(None) is None

