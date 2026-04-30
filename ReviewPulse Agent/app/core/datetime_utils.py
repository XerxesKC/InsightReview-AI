from __future__ import annotations

from datetime import datetime, timezone


def to_rfc3339(value: datetime | None) -> str | None:
    """Serialize datetimes as timezone-aware RFC3339 strings (UTC `Z`)."""
    if value is None:
        return None

    dt = value
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
