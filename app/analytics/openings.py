from __future__ import annotations

from typing import Any

import pandas as pd

from app.models import Game


def analyze_openings(games: list[Game]) -> dict[str, Any]:
    if not games:
        return {"favorite": [], "best": [], "worst": []}

    rows = [{"opening": g.opening or "Unknown Opening", "result": g.result} for g in games]
    df = pd.DataFrame(rows)

    grouped = df.groupby("opening").agg(games=("opening", "count"))
    grouped["wins"] = df[df["result"] == "WIN"].groupby("opening").size()
    grouped["losses"] = df[df["result"] == "LOSS"].groupby("opening").size()
    grouped["draws"] = df[df["result"] == "DRAW"].groupby("opening").size()
    grouped = grouped.fillna(0)
    grouped["winrate"] = (grouped["wins"] / grouped["games"] * 100).round(2)

    favorite = (
        grouped.sort_values(by="games", ascending=False)
        .head(5)
        .reset_index()[["opening", "games", "winrate"]]
        .to_dict(orient="records")
    )
    eligible = grouped[grouped["games"] >= 3]
    if eligible.empty:
        eligible = grouped

    best = (
        eligible.sort_values(by=["winrate", "games"], ascending=[False, False])
        .head(3)
        .reset_index()[["opening", "games", "winrate"]]
        .to_dict(orient="records")
    )
    worst = (
        eligible.sort_values(by=["winrate", "games"], ascending=[True, False])
        .head(3)
        .reset_index()[["opening", "games", "winrate"]]
        .to_dict(orient="records")
    )

    return {"favorite": favorite, "best": best, "worst": worst}
