"""Cumulative Filebase bucket weight over a bounded display horizon."""

from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timedelta, timezone
from typing import Any


def add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month, day=min(value.day, monthrange(year, month)[1]))


def _timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=value.tzinfo or timezone.utc).astimezone(timezone.utc)
    if isinstance(value, str) and value.strip():
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)
    return None


def storage_timeline(
    objects: list[dict[str, Any]], *, now: datetime | None = None
) -> dict[str, Any]:
    """Build an observed step series from S3 LastModified timestamps."""
    observed_now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    window_start = observed_now - timedelta(days=2)
    window_end = add_months(observed_now, 2)
    timestamped: list[tuple[datetime, int]] = []
    missing_timestamps = 0
    for item in objects:
        modified = _timestamp(item.get("LastModified"))
        if modified is None:
            missing_timestamps += 1
            continue
        timestamped.append((modified, int(item.get("Size", 0))))
    timestamped.sort(key=lambda item: item[0])

    running = sum(size for modified, size in timestamped if modified < window_start)
    actual_times = [window_start]
    actual_bytes = [running]
    for modified, size in timestamped:
        if window_start <= modified <= observed_now:
            running += size
            actual_times.append(modified)
            actual_bytes.append(running)
    actual_times.append(observed_now)
    actual_bytes.append(running)
    return {
        "window_start": window_start,
        "now": observed_now,
        "window_end": window_end,
        "actual_times": actual_times,
        "actual_bytes": actual_bytes,
        "horizon_times": [observed_now, window_end],
        "horizon_bytes": [running, running],
        "timestamped_objects": len(timestamped),
        "missing_timestamps": missing_timestamps,
    }
