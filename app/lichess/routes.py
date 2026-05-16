from __future__ import annotations

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.analytics.reports import create_analysis_report
from app.lichess import lichess_bp
from app.lichess.service import sync_recent_games
from app.models import Game


@lichess_bp.route("/import-recent", methods=["POST"])
@login_required
def import_recent_games():
    max_games = request.form.get("max_games", type=int) or 50
    max_games = min(max(max_games, 1), 200)

    try:
        imported_count = sync_recent_games(current_user, max_games=max_games)
        games = (
            Game.query.filter_by(user_id=current_user.id)
            .order_by(Game.played_at.desc().nullslast(), Game.created_at.desc())
            .all()
        )
        create_analysis_report(current_user, games)
        flash(f"Imported {imported_count} new games and refreshed analytics.", "success")
    except Exception as exc:  # noqa: BLE001 - MVP fallback messaging
        flash(f"Import failed: {exc}", "danger")

    return redirect(url_for("dashboard.dashboard_home"))
