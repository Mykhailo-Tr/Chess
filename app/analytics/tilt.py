from __future__ import annotations

from datetime import timedelta
from typing import Any

import numpy as np

from app.models import Game


def analyze_tilt(games: list[Game]) -> dict[str, Any]:
    if not games:
        return {"level": "LOW", "score": 0.0, "signals": {}}

    ordered = sorted(games, key=lambda g: g.played_at or g.created_at)

    losing_streak = _max_losing_streak(ordered)
    rapid_requeue_events = _rapid_requeue_after_loss(ordered)
    recent_results = [g.result for g in ordered[-10:]]
    recent_loss_ratio = recent_results.count("LOSS") / max(len(recent_results), 1)

    score = min(
        100.0,
        (losing_streak * 15.0) + (rapid_requeue_events * 10.0) + (recent_loss_ratio * 40.0),
    )

    if score >= 65:
        level = "HIGH"
    elif score >= 35:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "level": level,
        "score": round(float(score), 2),
        "signals": {
            "losing_streak": losing_streak,
            "rapid_requeue_after_loss": rapid_requeue_events,
            "recent_loss_ratio": round(float(recent_loss_ratio * 100), 2),
            "accuracy_drop_placeholder": _accuracy_drop_placeholder(ordered),
        },
    }


def _max_losing_streak(games: list[Game]) -> int:
    max_streak = 0
    current = 0
    for game in games:
        if game.result == "LOSS":
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return max_streak


def _rapid_requeue_after_loss(games: list[Game]) -> int:
    rapid_events = 0
    for idx, game in enumerate(games[:-1]):
        if game.result != "LOSS":
            continue
        current_time = game.played_at or game.created_at
        next_time = games[idx + 1].played_at or games[idx + 1].created_at
        if current_time and next_time and next_time - current_time <= timedelta(minutes=3):
            rapid_events += 1
    return rapid_events


def _accuracy_drop_placeholder(games: list[Game]) -> float:
    # Placeholder signal so we can swap in real move-accuracy later.
    losses = np.array([1 if g.result == "LOSS" else 0 for g in games[-20:]])
    if losses.size == 0:
        return 0.0
    return round(float(losses.mean() * 100), 2)
