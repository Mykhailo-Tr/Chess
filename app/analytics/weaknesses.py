from __future__ import annotations

from typing import Any

from app.models import Game


def analyze_weaknesses(games: list[Game]) -> dict[str, Any]:
    if not games:
        return {"items": []}

    total_games = len(games)
    endgame_losses = 0
    equal_middlegame_losses = 0
    gambit_losses = 0

    for game in games:
        opening = (game.opening or "").lower()
        result = game.result
        move_count = game.moves_count or 0
        division = game.division_json or {}
        endgame_ply = division.get("end")
        middle_ply = division.get("middle")

        if result == "LOSS" and endgame_ply and move_count and (move_count * 2) > endgame_ply:
            endgame_losses += 1
        elif result == "LOSS" and not endgame_ply and move_count >= 60:
            endgame_losses += 1

        if result == "LOSS" and middle_ply:
            game_ply = (move_count or 0) * 2
            if middle_ply <= game_ply < (endgame_ply or game_ply + 1):
                equal_middlegame_losses += 1
        elif result == "LOSS" and not middle_ply and 25 <= (move_count or 0) <= 50:
            equal_middlegame_losses += 1

        if result == "LOSS" and "gambit" in opening:
            gambit_losses += 1

    items = [
        _to_item("Endgame Conversion", endgame_losses, total_games, "Losing many long games into endgame."),
        _to_item(
            "Middlegame Stability",
            equal_middlegame_losses,
            total_games,
            "Losses in the 25-50 move range suggest unstable middlegame plans.",
        ),
        _to_item("Anti-Gambit Readiness", gambit_losses, total_games, "Poor results against gambit structures."),
    ]
    return {"items": items}


def _to_item(label: str, losses: int, total: int, insight: str) -> dict[str, Any]:
    ratio = (losses / max(total, 1)) * 100
    if ratio >= 25:
        severity = "HIGH"
    elif ratio >= 12:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    return {
        "label": label,
        "severity": severity,
        "losses": losses,
        "ratio": round(ratio, 2),
        "insight": insight,
    }
