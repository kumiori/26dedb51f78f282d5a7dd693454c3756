"""Observed cumulative storage projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..schemas import StorageObject


@dataclass(frozen=True, slots=True)
class StoragePoint:
    occurred_at: datetime
    object_count: int
    total_bytes: int


def project_storage(objects: tuple[StorageObject, ...]) -> tuple[StoragePoint, ...]:
    total = 0
    points: list[StoragePoint] = []
    for count, item in enumerate(sorted(objects, key=lambda row: (row.modified_at, row.key)), start=1):
        total += item.size_bytes
        points.append(StoragePoint(item.modified_at, count, total))
    return tuple(points)
