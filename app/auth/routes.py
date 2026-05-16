from __future__ import annotations

from datetime import datetime, UTC

from flask import current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth import auth_bp
from app.extensions import db
from app.lichess.client import LichessClient
from app.models import User


@auth_bp.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_home"))
    return render_template("auth/login.html")


@auth_bp.route("/token-login", methods=["POST"])
def token_login():
    token = current_app.config.get("LICHESS_PERSONAL_TOKEN", "")
    if not token:
        flash("LICHESS_PERSONAL_TOKEN is not set in environment.", "danger")
        return redirect(url_for("auth.login"))

    try:
        client = LichessClient.from_app(current_app)
        profile = client.get_profile(token)
    except Exception as exc:
        flash(f"Could not reach Lichess API: {exc}", "danger")
        return redirect(url_for("auth.login"))

    lichess_id = profile.get("id")
    username = profile.get("username")
    if not lichess_id or not username:
        flash("Could not read Lichess profile.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(lichess_id=lichess_id).first()
    if user is None:
        user = User(lichess_id=lichess_id, username=username)
        db.session.add(user)

    user.username = username
    user.access_token = token
    user.ratings_snapshot = _extract_ratings(profile)
    user.last_synced_at = datetime.now(UTC)
    db.session.commit()

    login_user(user)
    flash(f"Logged in as {username}.", "success")
    return redirect(url_for("dashboard.dashboard_home"))


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))


def _extract_ratings(profile: dict) -> dict[str, int]:
    perfs = profile.get("perfs") or {}
    ratings: dict[str, int] = {}
    for perf_key in ("bullet", "blitz", "rapid", "classical"):
        perf_data = perfs.get(perf_key)
        if isinstance(perf_data, dict) and perf_data.get("rating"):
            ratings[perf_key] = int(perf_data["rating"])
    return ratings
