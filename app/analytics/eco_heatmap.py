from __future__ import annotations

from typing import Any

from app.models import Game

FAMILY_LABELS = {
    "A": "Flank openings",
    "B": "Semi-Open openings",
    "C": "Open openings",
    "D": "Closed/Semi-Closed openings",
    "E": "Indian openings",
}


def build_eco_heatmap(games: list[Game]) -> dict[str, Any]:
    families: dict[str, dict[str, Any]] = {}

    for family_code, family_label in FAMILY_LABELS.items():
        cells = [
            {
                "code": f"{family_code}{bucket}x",
                "bucket": bucket,
                "games": 0,
                "wins": 0,
                "winrate": None,
            }
            for bucket in range(10)
        ]
        families[family_code] = {"label": family_label, "cells": cells}

    for game in games:
        family_code, bucket = _parse_eco_bucket(game.eco)
        if family_code is None or bucket is None:
            continue

        cell = families[family_code]["cells"][bucket]
        cell["games"] += 1
        if game.result == "WIN":
            cell["wins"] += 1

    for family_data in families.values():
        for cell in family_data["cells"]:
            if cell["games"] > 0:
                cell["winrate"] = round((cell["wins"] / cell["games"]) * 100, 2)

    return {"families": families}


def _parse_eco_bucket(eco: str | None) -> tuple[str | None, int | None]:
    if not eco or len(eco) < 3:
        return None, None

    family_code = eco[0].upper()
    if family_code not in FAMILY_LABELS:
        return None, None

    digits = "".join(ch for ch in eco[1:] if ch.isdigit())
    if len(digits) < 2:
        return None, None

    bucket = int(digits[0])
    if bucket < 0 or bucket > 9:
        return None, None

    return family_code, bucket
