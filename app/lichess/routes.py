from __future__ import annotations

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import case

from app.analytics.reports import create_analysis_report
from app.lichess import lichess_bp
from app.lichess.service import sync_recent_games
from app.models import Game


@lichess_bp.route("/import-recent", methods=["POST"])
@login_required
def import_recent_games():
    max_games = request.form.get("max_games", type=int) or 50
    max_games = min(max(max_games, 1), 500)

    try:
        imported_count = sync_recent_games(current_user, max_games=max_games)
        total_games = Game.query.filter_by(user_id=current_user.id).count()
        games = (
            Game.query.filter_by(user_id=current_user.id)
            .order_by(
                case((Game.played_at.is_(None), 1), else_=0),
                Game.played_at.desc(),
                Game.created_at.desc(),
            )
            .all()
        )
        create_analysis_report(current_user, games)
        if imported_count == 0:
            flash(
                f"No new games found since last import. Total: {total_games} games in database.",
                "success",
            )
        else:
            flash(
                f"Imported {imported_count} new games. Total: {total_games} games in database.",
                "success",
            )
    except Exception as exc:  # noqa: BLE001 - MVP fallback messaging
        flash(f"Import failed: {exc}", "danger")

    return redirect(url_for("dashboard.dashboard_home"))
