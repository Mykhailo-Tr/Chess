from __future__ import annotations

from flask import redirect, render_template, url_for
from flask_login import current_user, login_required

from app.analytics.reports import latest_or_create_report
from app.dashboard import dashboard_bp
from app.models import Game


@dashboard_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_home"))
    return redirect(url_for("auth.login"))


@dashboard_bp.route("/dashboard")
@login_required
def dashboard_home():
    games = (
        Game.query.filter_by(user_id=current_user.id)
        .order_by(Game.played_at.desc().nullslast(), Game.created_at.desc())
        .all()
    )
    report = latest_or_create_report(current_user, games)
    payload = report.payload
    ratings = current_user.ratings_snapshot or {}

    openings_chart = payload["openings"]["favorite"]
    results_chart = [
        sum(1 for g in games if g.result == "WIN"),
        sum(1 for g in games if g.result == "DRAW"),
        sum(1 for g in games if g.result == "LOSS"),
    ]

    return render_template(
        "dashboard/index.html",
        payload=payload,
        ratings=ratings,
        openings_chart=openings_chart,
        results_chart=results_chart,
    )
