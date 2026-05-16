from __future__ import annotations

from collections import Counter
from typing import Any

from app.models import Game


def analyze_by_color(games: list[Game]) -> dict[str, dict[str, Any]]:
    white_games = [game for game in games if (game.user_color or "").lower() == "white"]
    black_games = [game for game in games if (game.user_color or "").lower() == "black"]

    return {
        "white": _build_color_stats(white_games),
        "black": _build_color_stats(black_games),
    }


def _build_color_stats(color_games: list[Game]) -> dict[str, Any]:
    total = len(color_games)
    wins = sum(1 for game in color_games if game.result == "WIN")
    draws = sum(1 for game in color_games if game.result == "DRAW")
    losses = sum(1 for game in color_games if game.result == "LOSS")
    winrate = round((wins / max(total, 1)) * 100, 2)

    move_counts = [game.moves_count for game in color_games if isinstance(game.moves_count, int)]
    avg_moves = round(sum(move_counts) / len(move_counts), 2) if move_counts else 0.0

    opening_counts = Counter((game.opening or "Unknown Opening") for game in color_games)
    opening_rows: list[dict[str, Any]] = []
    for opening_name, games_count in opening_counts.most_common(3):
        opening_games = [game for game in color_games if (game.opening or "Unknown Opening") == opening_name]
        opening_wins = sum(1 for game in opening_games if game.result == "WIN")
        opening_winrate = round((opening_wins / max(games_count, 1)) * 100, 2)
        opening_rows.append(
            {
                "opening": opening_name,
                "games": games_count,
                "winrate": opening_winrate,
            }
        )

    return {
        "total": total,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "winrate": winrate,
        "avg_moves": avg_moves,
        "openings": opening_rows,
    }
