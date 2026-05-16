from __future__ import annotations

from flask import current_app, flash, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import case

from app.analytics.color_analysis import analyze_by_color
from app.analytics.puzzle_stats import parse_puzzle_dashboard
from app.analytics.rating_history import parse_rating_history
from app.analytics.session_stats import build_calendar_heatmap, build_session_stats
from app.analytics import analytics_bp
from app.analytics.reports import build_behavior_report, latest_or_create_report
from app.lichess.client import LichessClient
from app.models import Game

VALID_SPEEDS = {"bullet", "blitz", "rapid", "classical"}
VALID_PUZZLE_DAYS = {7, 30, 60, 90}


def _normalize_speed(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized in VALID_SPEEDS:
        return normalized
    return None


def _get_user_games(speed: str | None = None) -> list[Game]:
    games = (
        Game.query.filter_by(user_id=current_user.id)
        .order_by(
            case((Game.played_at.is_(None), 1), else_=0),
            Game.played_at.desc(),
            Game.created_at.desc(),
        )
        .all()
    )
    if speed:
        return [game for game in games if (game.speed or "").lower() == speed]
    return games


def _build_report_payload(speed: str | None = None) -> dict:
    games = _get_user_games(speed=speed)
    if speed:
        return build_behavior_report(games)
    report = latest_or_create_report(current_user, games)
    return report.payload


@analytics_bp.route("/")
@login_required
def analytics_home():
    active_speed = _normalize_speed(request.args.get("speed"))
    payload = _build_report_payload(speed=active_speed)
    return render_template("analytics/index.html", payload=payload, active_speed=active_speed)


@analytics_bp.route("/openings")
@login_required
def openings():
    active_speed = _normalize_speed(request.args.get("speed"))
    payload = _build_report_payload(speed=active_speed)
    return render_template("analytics/openings.html", payload=payload, active_speed=active_speed)


@analytics_bp.route("/weaknesses")
@login_required
def weaknesses():
    active_speed = _normalize_speed(request.args.get("speed"))
    payload = _build_report_payload(speed=active_speed)
    return render_template("analytics/weaknesses.html", payload=payload, active_speed=active_speed)


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


@analytics_bp.route("/colors")
@login_required
def color_analysis():
    active_speed = _normalize_speed(request.args.get("speed"))
    games = _get_user_games(speed=active_speed)
    color_stats = analyze_by_color(games)
    return render_template("analytics/colors.html", color_stats=color_stats, active_speed=active_speed)


@analytics_bp.route("/calendar")
@login_required
def play_calendar():
    active_speed = _normalize_speed(request.args.get("speed"))
    games = _get_user_games(speed=active_speed)
    calendar = build_calendar_heatmap(games)
    session_stats = build_session_stats(games)
    return render_template(
        "analytics/calendar.html",
        calendar=calendar,
        session_stats=session_stats,
        active_speed=active_speed,
    )


@analytics_bp.route("/puzzles")
@login_required
def puzzle_training():
    days = request.args.get("days", type=int) or 30
    if days not in VALID_PUZZLE_DAYS:
        days = 30

    puzzle_stats = {
        "days": days,
        "nb": 0,
        "wins": 0,
        "winrate": 0.0,
        "themes": [],
        "weakest": [],
        "strongest": [],
    }

    try:
        if not current_user.access_token:
            raise ValueError("Missing Lichess access token")

        client = LichessClient.from_app(current_app)
        raw_dashboard = client.get_puzzle_dashboard(current_user.access_token, days=days)
        puzzle_stats = parse_puzzle_dashboard(raw_dashboard)
        if not puzzle_stats.get("days"):
            puzzle_stats["days"] = days
    except Exception:  # noqa: BLE001 - keep page available with empty state
        pass

    return render_template(
        "analytics/puzzles.html",
        puzzle_stats=puzzle_stats,
        active_days=days,
    )
