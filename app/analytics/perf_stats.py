from __future__ import annotations

from typing import Any


def parse_perf_stats(raw: dict[str, Any], perf: str) -> dict[str, Any]:
    stat = raw.get("stat")
    if not isinstance(stat, dict):
        stat = {}

    current_streak = _to_int(stat.get("currentStreak"))
    max_streak = _to_int(stat.get("maxStreak"))

    best_wins_raw = stat.get("bestWins")
    if not isinstance(best_wins_raw, list):
        best_wins_raw = []
    best_wins = [_normalize_result_item(item) for item in best_wins_raw if isinstance(item, dict)]

    worst_losses_raw = stat.get("worstLosses")
    if not isinstance(worst_losses_raw, list):
        worst_losses_raw = []
    worst_losses = [_normalize_result_item(item) for item in worst_losses_raw if isinstance(item, dict)]

    glicko = raw.get("glicko")
    if not isinstance(glicko, dict):
        glicko = {}

    rating = _to_int(glicko.get("rating"))
    if rating == 0:
        rating = _to_int(raw.get("rating"))
    if rating == 0:
        rating = _to_int(raw.get("perf") or raw.get("int"))

    rd = _to_float(glicko.get("deviation"))
    if rd == 0.0:
        rd = _to_float(raw.get("rd"))
    if rd == 0.0:
        rd = _to_float(raw.get("deviation"))

    prog = _to_int(raw.get("prog"))
    nb = _to_int(raw.get("nb"))
    percentile = _to_float(raw.get("percentile"))

    peak_rating = None
    highest = raw.get("highest")
    if isinstance(highest, dict):
        peak_rating = _to_int(highest.get("int"))
        if peak_rating == 0:
            peak_rating = _to_int(highest.get("rating"))

    return {
        "perf": perf,
        "rating": rating,
        "rd": rd,
        "prog": prog,
        "nb": nb,
        "percentile": percentile,
        "peak_rating": peak_rating or rating,
        "streak": {
            "current": current_streak,
            "max": max_streak,
        },
        "best_wins": best_wins,
        "worst_losses": worst_losses,
    }


def _normalize_result_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "opId": str(item.get("opId") or "Unknown"),
        "opRating": _to_int(item.get("opRating")),
        "at": str(item.get("at") or ""),
    }


def _to_int(value: Any) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _to_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0
