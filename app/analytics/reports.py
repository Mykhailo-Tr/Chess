from __future__ import annotations

from typing import Any

from app.analytics.openings import analyze_openings
from app.analytics.tilt import analyze_tilt
from app.analytics.time_management import analyze_time_management
from app.analytics.weaknesses import analyze_weaknesses
from app.extensions import db
from app.models import AnalysisReport, Game, User


def build_behavior_report(games: list[Game]) -> dict[str, Any]:
    openings = analyze_openings(games)
    tilt = analyze_tilt(games)
    time_management = analyze_time_management(games)
    weaknesses = analyze_weaknesses(games)

    wins = sum(1 for g in games if g.result == "WIN")
    draws = sum(1 for g in games if g.result == "DRAW")
    total = len(games)
    winrate = (wins / max(total, 1)) * 100

    # Placeholder accuracy score from outcome balance.
    avg_accuracy = round(((wins + (draws * 0.5)) / max(total, 1)) * 100, 2)

    return {
        "games_analyzed": total,
        "winrate": round(winrate, 2),
        "avg_accuracy": avg_accuracy,
        "tilt": tilt,
        "openings": openings,
        "time_management": time_management,
        "weaknesses": weaknesses,
    }


def create_analysis_report(user: User, games: list[Game]) -> AnalysisReport:
    payload = build_behavior_report(games)

    report = AnalysisReport(
        user_id=user.id,
        games_analyzed=payload["games_analyzed"],
        winrate=payload["winrate"],
        avg_accuracy=payload["avg_accuracy"],
        tilt_level=payload["tilt"]["level"],
        tilt_score=payload["tilt"]["score"],
        time_pressure_score=payload["time_management"]["time_pressure_score"],
        payload=payload,
    )
    db.session.add(report)
    db.session.commit()
    return report


def latest_or_create_report(user: User, games: list[Game]) -> AnalysisReport:
    latest = AnalysisReport.query.filter_by(user_id=user.id).order_by(AnalysisReport.generated_at.desc()).first()
    if latest and latest.games_analyzed == len(games):
        return latest
    return create_analysis_report(user, games)
