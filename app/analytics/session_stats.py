from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from app.models import Game

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def build_calendar_heatmap(games: list[Game]) -> dict[str, Any]:
    today = datetime.now(UTC).date()
    start_date = today - timedelta(days=364)

    counts: Counter[str] = Counter()
    for game in games:
        game_dt = game.played_at or game.created_at
        if game_dt is None:
            continue
        game_date = game_dt.date()
        if start_date <= game_date <= today:
            counts[game_date.strftime("%Y-%m-%d")] += 1

    heatmap: dict[str, int] = {}
    max_count = 0
    for offset in range(365):
        current_date = start_date + timedelta(days=offset)
        key = current_date.strftime("%Y-%m-%d")
        day_count = counts.get(key, 0)
        heatmap[key] = day_count
        if day_count > max_count:
            max_count = day_count

    return {"heatmap": heatmap, "max_count": max_count}


def build_session_stats(games: list[Game]) -> dict[str, Any]:
    weekday_total = [0] * 7
    weekday_wins = [0] * 7
    hour_total = [0] * 24
    hour_wins = [0] * 24

    for game in games:
        game_dt = game.played_at or game.created_at
        if game_dt is None:
            continue

        weekday_index = game_dt.weekday()
        hour_index = game_dt.hour

        weekday_total[weekday_index] += 1
        hour_total[hour_index] += 1

        if game.result == "WIN":
            weekday_wins[weekday_index] += 1
            hour_wins[hour_index] += 1

    weekday_stats = [
        {
            "weekday": WEEKDAY_NAMES[index],
            "count": weekday_total[index],
            "winrate": round((weekday_wins[index] / max(weekday_total[index], 1)) * 100, 2),
        }
        for index in range(7)
    ]
    hour_stats = [
        {
            "hour": index,
            "count": hour_total[index],
            "winrate": round((hour_wins[index] / max(hour_total[index], 1)) * 100, 2),
        }
        for index in range(24)
    ]

    best_hour = _pick_bucket(hour_stats, key_name="hour", best=True)
    worst_hour = _pick_bucket(hour_stats, key_name="hour", best=False)
    best_weekday = _pick_bucket(weekday_stats, key_name="weekday", best=True)
    worst_weekday = _pick_bucket(weekday_stats, key_name="weekday", best=False)

    return {
        "weekday": weekday_stats,
        "hour": hour_stats,
        "best_hour": best_hour,
        "worst_hour": worst_hour,
        "best_weekday": best_weekday,
        "worst_weekday": worst_weekday,
    }


def _pick_bucket(
    buckets: list[dict[str, Any]],
    *,
    key_name: str,
    best: bool,
) -> dict[str, Any] | None:
    eligible = [bucket for bucket in buckets if bucket["count"] >= 2]
    if not eligible:
        return None

    if best:
        chosen = max(eligible, key=lambda item: (item["winrate"], item["count"], -_key_as_int(item[key_name])))
    else:
        chosen = min(eligible, key=lambda item: (item["winrate"], -item["count"], _key_as_int(item[key_name])))
    return {
        key_name: chosen[key_name],
        "count": chosen["count"],
        "winrate": chosen["winrate"],
    }


def _key_as_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value in WEEKDAY_NAMES:
        return WEEKDAY_NAMES.index(value)
    return 0
