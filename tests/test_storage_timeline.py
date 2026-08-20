from datetime import datetime, timezone

from takeover.storage_timeline import add_months, storage_timeline


NOW = datetime(2026, 8, 19, 12, tzinfo=timezone.utc)


def test_timeline_starts_two_days_ago_and_extends_two_calendar_months() -> None:
    timeline = storage_timeline(
        [
            {"Size": 100, "LastModified": datetime(2026, 8, 16, tzinfo=timezone.utc)},
            {"Size": 20, "LastModified": datetime(2026, 8, 18, tzinfo=timezone.utc)},
            {"Size": 5, "LastModified": datetime(2026, 8, 19, 10, tzinfo=timezone.utc)},
        ],
        now=NOW,
    )

    assert timeline["window_start"] == datetime(2026, 8, 17, 12, tzinfo=timezone.utc)
    assert timeline["window_end"] == datetime(2026, 10, 19, 12, tzinfo=timezone.utc)
    assert timeline["actual_bytes"] == [100, 120, 125, 125]
    assert timeline["actual_counts"] == [1, 2, 3, 3]
    assert timeline["horizon_bytes"] == [125, 125]
    assert timeline["horizon_counts"] == [3, 3]


def test_missing_timestamps_are_reported_not_invented() -> None:
    timeline = storage_timeline([{"Size": 99}], now=NOW)
    assert timeline["missing_timestamps"] == 1
    assert timeline["actual_bytes"] == [0, 0]


def test_add_months_clamps_end_of_month() -> None:
    assert add_months(datetime(2026, 12, 31, tzinfo=timezone.utc), 2) == datetime(2027, 2, 28, tzinfo=timezone.utc)
