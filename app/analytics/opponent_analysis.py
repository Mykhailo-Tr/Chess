from __future__ import annotations

from typing import Any

from app.models import Game

BRACKETS = [
    {"label": "<1200", "min": None, "max": 1199},
    {"label": "1200-1500", "min": 1200, "max": 1499},
    {"label": "1500-1800", "min": 1500, "max": 1799},
    {"label": "1800-2100", "min": 1800, "max": 2099},
    {"label": "2100+", "min": 2100, "max": None},
]


def analyze_opponent_strength(games: list[Game]) -> dict[str, Any]:
    brackets = []
    for bracket in BRACKETS:
        scoped_games = [game for game in games if _in_bracket(game.rating, bracket["min"], bracket["max"])]
        wins = sum(1 for game in scoped_games if game.result == "WIN")
        count = len(scoped_games)
        winrate = round((wins / max(count, 1)) * 100, 2)
        brackets.append(
            {
                "label": bracket["label"],
                "games": count,
                "wins": wins,
                "winrate": winrate,
            }
        )

    toughest_loss = _best_rated_game([game for game in games if game.result == "LOSS"])
    best_win = _best_rated_game([game for game in games if game.result == "WIN"])

    return {
        "brackets": brackets,
        "toughest_loss": toughest_loss,
        "best_win": best_win,
    }


def _in_bracket(rating: int | None, min_value: int | None, max_value: int | None) -> bool:
    if not isinstance(rating, int):
        return False
    if min_value is not None and rating < min_value:
        return False
    if max_value is not None and rating > max_value:
        return False
    return True


def _best_rated_game(games: list[Game]) -> dict[str, Any] | None:
    rated_games = [game for game in games if isinstance(game.rating, int)]
    if not rated_games:
        return None
    target = max(rated_games, key=lambda game: game.rating or 0)
    return {
        "opponent": target.opponent or "Unknown",
        "rating": int(target.rating or 0),
    }
