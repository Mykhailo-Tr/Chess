from __future__ import annotations

from datetime import UTC, datetime

from flask import current_app, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import case

from app.analytics.color_analysis import analyze_by_color
from app.analytics.eco_heatmap import build_eco_heatmap
from app.analytics.opponent_analysis import analyze_opponent_strength
from app.analytics.perf_stats import parse_perf_stats
from app.analytics.pdf_export import render_report_pdf
from app.analytics.puzzle_stats import parse_puzzle_dashboard
from app.analytics.rating_history import parse_rating_history
from app.analytics.session_stats import build_calendar_heatmap, build_session_stats
from app.analytics.tips import generate_daily_tips
from app.analytics import analytics_bp
from app.analytics.reports import build_behavior_report, latest_or_create_report
from app.lichess.client import LichessClient
from app.models import Game

VALID_SPEEDS = {"bullet", "blitz", "rapid", "classical"}
VALID_PUZZLE_DAYS = {7, 30, 60, 90}
VALID_PERFS = {"bullet", "blitz", "rapid", "classical"}


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


@analytics_bp.route("/export-pdf")
@login_required
def export_pdf():
    try:
        payload = _build_report_payload()
        pdf_bytes = render_report_pdf(current_user, payload)
        response = make_response(pdf_bytes)
        response.mimetype = "application/pdf"
        response.headers["Content-Disposition"] = (
            f'attachment; filename="chess_report_{current_user.username}.pdf"'
        )
        return response
    except Exception as exc:  # noqa: BLE001 - user-facing fallback route
        flash(f"PDF export failed: {exc}", "danger")
        return redirect(url_for("analytics.analytics_home"))


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


@analytics_bp.route("/tips")
@login_required
def daily_tips():
    payload = _build_report_payload()
    tips = generate_daily_tips(payload)
    today_label = datetime.now(UTC).strftime("%B %d, %Y")
    return render_template(
        "analytics/tips.html",
        tips=tips,
        today_label=today_label,
    )


@analytics_bp.route("/opponents")
@login_required
def opponent_strength():
    active_speed = _normalize_speed(request.args.get("speed"))
    games = _get_user_games(speed=active_speed)
    opponent_stats = analyze_opponent_strength(games)
    return render_template(
        "analytics/opponents.html",
        opponent_stats=opponent_stats,
        active_speed=active_speed,
    )


@analytics_bp.route("/eco")
@login_required
def eco_map():
    active_speed = _normalize_speed(request.args.get("speed"))
    games = _get_user_games(speed=active_speed)
    eco_stats = build_eco_heatmap(games)
    return render_template(
        "analytics/eco.html",
        eco_stats=eco_stats,
        active_speed=active_speed,
    )


@analytics_bp.route("/perf/<perf>")
@login_required
def perf_stats(perf: str):
    normalized_perf = (perf or "").strip().lower()
    if normalized_perf not in VALID_PERFS:
        normalized_perf = "blitz"

    stats = {
        "perf": normalized_perf,
        "rating": 0,
        "rd": 0.0,
        "prog": 0,
        "nb": 0,
        "percentile": 0.0,
        "peak_rating": 0,
        "streak": {"current": 0, "max": 0},
        "best_wins": [],
        "worst_losses": [],
    }
    rating_series: list[dict] = []

    try:
        if not current_user.access_token:
            raise ValueError("Missing Lichess access token")

        client = LichessClient.from_app(current_app)
        raw_stats = client.get_perf_stats(
            username=current_user.username,
            perf=normalized_perf,
            access_token=current_user.access_token,
        )
        stats = parse_perf_stats(raw_stats, normalized_perf)

        raw_history = client.get_rating_history(current_user.username, current_user.access_token)
        parsed_history = parse_rating_history(raw_history)
        rating_series = parsed_history.get(normalized_perf, [])
    except Exception:  # noqa: BLE001 - keep page available for missing/empty stats
        pass

    return render_template(
        "analytics/perf_stats.html",
        stats=stats,
        active_perf=normalized_perf,
        rating_series=rating_series,
    )


@analytics_bp.route("/compare")
@login_required
def compare_player():
    opponent = (request.args.get("opponent") or "").strip()

    comparison = None
    if opponent:
        client = LichessClient.from_app(current_app)
        opponent_key = opponent.lower()
        local_games = (
            Game.query.filter_by(user_id=current_user.id)
            .filter(Game.opponent.ilike(opponent))
            .all()
        )
        local_wins = sum(1 for game in local_games if game.result == "WIN")
        local_draws = sum(1 for game in local_games if game.result == "DRAW")
        local_losses = sum(1 for game in local_games if game.result == "LOSS")
        local_total = len(local_games)
        local_winrate = round((local_wins / max(local_total, 1)) * 100, 2)

        try:
            me_profile = client.get_user(current_user.username)
            opponent_profile = client.get_user(opponent)
            crosstable = client.get_crosstable(current_user.username, opponent, current_user.access_token or "")
        except Exception:  # noqa: BLE001 - render with local stats only when remote fails
            me_profile = {}
            opponent_profile = {}
            crosstable = {}

        comparison = {
            "opponent_query": opponent,
            "me": _build_profile_summary(me_profile, fallback_name=current_user.username),
            "opponent": _build_profile_summary(opponent_profile, fallback_name=opponent),
            "crosstable": crosstable if isinstance(crosstable, dict) else {},
            "crosstable_summary": _extract_crosstable_summary(
                crosstable if isinstance(crosstable, dict) else {},
                user1=current_user.username,
                user2=opponent,
            ),
            "local": {
                "wins": local_wins,
                "draws": local_draws,
                "losses": local_losses,
                "total": local_total,
                "winrate": local_winrate,
            },
            "opponent_key": opponent_key,
        }

    return render_template(
        "analytics/compare.html",
        comparison=comparison,
    )


def _build_profile_summary(profile: dict, *, fallback_name: str) -> dict:
    if not isinstance(profile, dict):
        profile = {}

    perfs = profile.get("perfs")
    if not isinstance(perfs, dict):
        perfs = {}

    count = profile.get("count")
    if not isinstance(count, dict):
        count = {}

    created_at_ms = profile.get("createdAt")
    join_date = "N/A"
    if isinstance(created_at_ms, int):
        join_date = datetime.fromtimestamp(created_at_ms / 1000, tz=UTC).strftime("%Y-%m-%d")

    return {
        "username": profile.get("username") or fallback_name,
        "ratings": {
            "bullet": _extract_perf_rating(perfs.get("bullet")),
            "blitz": _extract_perf_rating(perfs.get("blitz")),
            "rapid": _extract_perf_rating(perfs.get("rapid")),
        },
        "games_all": int(count.get("all") or 0),
        "join_date": join_date,
    }


def _extract_perf_rating(perf_blob: object) -> int:
    if isinstance(perf_blob, dict):
        value = perf_blob.get("rating")
        if isinstance(value, int):
            return value
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
    return 0


def _extract_crosstable_summary(crosstable: dict, *, user1: str, user2: str) -> dict:
    if not isinstance(crosstable, dict):
        crosstable = {}

    matchup = crosstable.get("matchup")
    if not isinstance(matchup, dict):
        matchup = crosstable

    users = matchup.get("users")
    if not isinstance(users, dict):
        users = {}

    score_user1 = users.get(user1) or users.get(user1.lower()) or users.get(user1.capitalize()) or 0
    score_user2 = users.get(user2) or users.get(user2.lower()) or users.get(user2.capitalize()) or 0

    try:
        score_user1 = float(score_user1)
    except (TypeError, ValueError):
        score_user1 = 0.0
    try:
        score_user2 = float(score_user2)
    except (TypeError, ValueError):
        score_user2 = 0.0

    total_games = matchup.get("nbGames") or crosstable.get("nbGames") or 0
    try:
        total_games = int(total_games)
    except (TypeError, ValueError):
        total_games = 0

    return {
        "score_user1": score_user1,
        "score_user2": score_user2,
        "total_games": total_games,
    }
