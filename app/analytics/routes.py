from __future__ import annotations

from flask import render_template
from flask_login import current_user, login_required
from sqlalchemy import case

from app.analytics import analytics_bp
from app.analytics.reports import latest_or_create_report
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
