from __future__ import annotations

from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import case

from app.analytics.reports import build_behavior_report, latest_or_create_report
from app.analytics.tilt import tilt_guard_message
from app.dashboard import dashboard_bp
from app.models import Game

VALID_SPEEDS = {"bullet", "blitz", "rapid", "classical"}


def _normalize_speed(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized in VALID_SPEEDS:
        return normalized
    return None


@dashboard_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_home"))
    return redirect(url_for("auth.login"))


@dashboard_bp.route("/dashboard")
@login_required
def dashboard_home():
    active_speed = _normalize_speed(request.args.get("speed"))

    games = (
        Game.query.filter_by(user_id=current_user.id)
        .order_by(
            case((Game.played_at.is_(None), 1), else_=0),
            Game.played_at.desc(),
            Game.created_at.desc(),
        )
        .all()
    )
    if active_speed:
        games = [game for game in games if (game.speed or "").lower() == active_speed]

    if active_speed:
        payload = build_behavior_report(games)
    else:
        report = latest_or_create_report(current_user, games)
        payload = report.payload
    ratings = current_user.ratings_snapshot or {}

    openings_chart = payload["openings"]["favorite"]
    results_chart = [
        sum(1 for g in games if g.result == "WIN"),
        sum(1 for g in games if g.result == "DRAW"),
        sum(1 for g in games if g.result == "LOSS"),
    ]
    dismiss_tilt_guard = request.args.get("dismiss_tilt_guard") == "1"
    tilt_guard = None if dismiss_tilt_guard else tilt_guard_message(payload.get("tilt") or {})

    return render_template(
        "dashboard/index.html",
        payload=payload,
        ratings=ratings,
        openings_chart=openings_chart,
        results_chart=results_chart,
        active_speed=active_speed,
        tilt_guard=tilt_guard,
    )
