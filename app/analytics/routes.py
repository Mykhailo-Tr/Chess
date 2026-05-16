from __future__ import annotations

from flask import current_app, flash, render_template
from flask_login import current_user, login_required
from sqlalchemy import case

from app.analytics.rating_history import parse_rating_history
from app.analytics import analytics_bp
from app.analytics.reports import latest_or_create_report
from app.lichess.client import LichessClient
from app.models import Game


def _build_report_payload() -> dict:
    games = (
        Game.query.filter_by(user_id=current_user.id)
        .order_by(
            case((Game.played_at.is_(None), 1), else_=0),
            Game.played_at.desc(),
            Game.created_at.desc(),
        )
        .all()
    )
    report = latest_or_create_report(current_user, games)
    return report.payload


@analytics_bp.route("/")
@login_required
def analytics_home():
    payload = _build_report_payload()
    return render_template("analytics/index.html", payload=payload)


@analytics_bp.route("/openings")
@login_required
def openings():
    payload = _build_report_payload()
    return render_template("analytics/openings.html", payload=payload)


@analytics_bp.route("/weaknesses")
@login_required
def weaknesses():
    payload = _build_report_payload()
    return render_template("analytics/weaknesses.html", payload=payload)


@analytics_bp.route("/rating-history")
@login_required
def rating_history():
    history: dict = {}

    try:
        client = LichessClient.from_app(current_app)
        raw_history = client.get_rating_history(
            username=current_user.username,
            access_token=current_user.access_token,
        )
        history = parse_rating_history(raw_history)
    except Exception as exc:  # noqa: BLE001 - page should remain available if API is unavailable
        flash(f"Could not load rating history: {exc}", "warning")

    return render_template("analytics/rating_history.html", history=history)
