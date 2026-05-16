from __future__ import annotations

from typing import Any


def parse_puzzle_dashboard(raw: dict[str, Any]) -> dict[str, Any]:
    themes_blob = raw.get("themes")
    themes: list[dict[str, Any]] = []

    if isinstance(themes_blob, dict):
        for theme_key, theme_value in themes_blob.items():
            if not isinstance(theme_value, dict):
                continue

            results = theme_value.get("results")
            if not isinstance(results, dict):
                results = {}

            nb = int(results.get("nb") or 0)
            wins = int(results.get("wins") or 0)
            winrate = round((wins / max(nb, 1)) * 100, 2)

            themes.append(
                {
                    "theme_name": str(theme_value.get("theme") or theme_key),
                    "nb": nb,
                    "wins": wins,
                    "winrate": winrate,
                }
            )

    themes.sort(key=lambda item: item["nb"], reverse=True)

    weakest = [
        item
        for item in themes
        if item["nb"] >= 3 and item["winrate"] < 50
    ]
    weakest = sorted(weakest, key=lambda item: (item["winrate"], -item["nb"]))[:5]

    strongest = [
        item
        for item in themes
        if item["nb"] >= 3 and item["winrate"] >= 60
    ]
    strongest = sorted(strongest, key=lambda item: (item["winrate"], item["nb"]), reverse=True)[:5]

    global_blob = raw.get("global")
    global_results = raw.get("results")
    if not isinstance(global_blob, dict):
        global_blob = {}
    if not isinstance(global_results, dict):
        global_results = {}

    days = int(raw.get("days") or global_blob.get("days") or 0)
    nb_total = int(raw.get("nb") or global_blob.get("nb") or global_results.get("nb") or 0)
    wins_total = int(raw.get("wins") or global_blob.get("wins") or global_results.get("wins") or 0)
    winrate_total = round((wins_total / max(nb_total, 1)) * 100, 2)

    return {
        "days": days,
        "nb": nb_total,
        "wins": wins_total,
        "winrate": winrate_total,
        "themes": themes,
        "weakest": weakest,
        "strongest": strongest,
    }
