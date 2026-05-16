from __future__ import annotations

import secrets
from datetime import datetime, UTC, timedelta

from flask import current_app, flash, redirect, render_template, request, session, url_for
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


@auth_bp.route("/connect")
def connect_lichess():
    client = LichessClient.from_app(current_app)
    if not current_app.config["LICHESS_CLIENT_ID"]:
        flash("Lichess OAuth is not configured. Set LICHESS_CLIENT_ID and LICHESS_CLIENT_SECRET.", "danger")
        return redirect(url_for("auth.login"))

    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    redirect_uri = url_for("auth.oauth_callback", _external=True)
    authorize_url = client.build_authorize_url(
        redirect_uri=redirect_uri,
        state=state,
        scope="preference:read",
    )
    return redirect(authorize_url)


@auth_bp.route("/callback")
def oauth_callback():
    if request.args.get("error"):
        flash("Authorization denied by Lichess.", "danger")
        return redirect(url_for("auth.login"))

    code = request.args.get("code")
    state = request.args.get("state")
    expected_state = session.pop("oauth_state", None)

    if not code or not state or state != expected_state:
        flash("Invalid OAuth callback state.", "danger")
        return redirect(url_for("auth.login"))

    client = LichessClient.from_app(current_app)
    redirect_uri = url_for("auth.oauth_callback", _external=True)

    token_data = client.exchange_code_for_token(code=code, redirect_uri=redirect_uri)
    access_token = token_data.get("access_token")
    if not access_token:
        flash("Could not obtain Lichess token.", "danger")
        return redirect(url_for("auth.login"))

    profile = client.get_profile(access_token)
    lichess_id = profile.get("id")
    username = profile.get("username")

    if not lichess_id or not username:
        flash("Could not read your Lichess profile.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(lichess_id=lichess_id).first()
    if user is None:
        user = User(lichess_id=lichess_id, username=username)
        db.session.add(user)

    expires_in = token_data.get("expires_in")
    expires_at = datetime.now(UTC) + timedelta(seconds=int(expires_in)) if expires_in else None

    user.username = username
    user.access_token = access_token
    user.refresh_token = token_data.get("refresh_token")
    user.token_expires_at = expires_at
    user.ratings_snapshot = _extract_ratings(profile)
    user.last_synced_at = datetime.now(UTC)

    db.session.commit()
    login_user(user)
    flash("Lichess account connected.", "success")
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
