from __future__ import annotations

from datetime import date
from typing import Any

TRACKED_PERFS = {"bullet", "blitz", "rapid", "classical"}


def parse_rating_history(raw: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    parsed: dict[str, list[dict[str, Any]]] = {}

    for item in raw:
        perf_name_raw = item.get("name")
        if not isinstance(perf_name_raw, str):
            continue
        perf_name = perf_name_raw.strip().lower()
        if perf_name not in TRACKED_PERFS:
            continue

        points = item.get("points")
        if not isinstance(points, list):
            continue

        entries: list[tuple[date, int]] = []
        for point in points:
            if not isinstance(point, list) or len(point) < 4:
                continue

            year, month, day, rating = point[0], point[1], point[2], point[3]
            if not all(isinstance(value, int) for value in (year, month, day, rating)):
                continue

            # Lichess month values are zero-based in this endpoint payload.
            month_number = month + 1
            try:
                point_date = date(year, month_number, day)
            except ValueError:
                continue

            entries.append((point_date, rating))

        entries.sort(key=lambda value: value[0])
        parsed[perf_name] = [
            {"date": point_date.strftime("%Y-%m-%d"), "rating": rating}
            for point_date, rating in entries
        ]

    return parsed
