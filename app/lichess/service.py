from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from flask import current_app

from app.extensions import db
from app.lichess.client import LichessClient
from app.models import Game, User


def sync_recent_games(user: User, max_games: int = 50) -> int:
    client = LichessClient.from_app(current_app)

    profile = client.get_profile(user.access_token or "")
    user.ratings_snapshot = _extract_ratings(profile)
    user.last_synced_at = datetime.now(UTC)

    raw_games = client.export_games(
        username=user.username,
        max_games=max_games,
        access_token=user.access_token,
    )

    imported = 0
    for raw_game in raw_games:
        game_id = raw_game.get("id")
        if not game_id:
            continue

        existing = Game.query.filter_by(user_id=user.id, lichess_game_id=game_id).first()
        if existing:
            continue

        game_obj = Game(
            user_id=user.id,
            lichess_game_id=game_id,
            pgn=raw_game.get("pgn", ""),
            result=_resolve_result(raw_game, user.username),
            opening=_resolve_opening(raw_game),
            played_at=_resolve_played_at(raw_game),
            opponent=_resolve_opponent(raw_game, user.username),
            user_color=_resolve_color(raw_game, user.username),
            time_control=_resolve_time_control(raw_game),
            speed=raw_game.get("speed"),
            termination=raw_game.get("status"),
            rating=_resolve_rating(raw_game, user.username),
            moves_count=raw_game.get("turns"),
            clock_data=raw_game.get("clocks") or raw_game.get("clock"),
            metadata_json={
                "rated": raw_game.get("rated"),
                "variant": raw_game.get("variant"),
                "winner": raw_game.get("winner"),
            },
        )
        db.session.add(game_obj)
        imported += 1

    db.session.commit()
    return imported


def _resolve_opening(raw_game: dict[str, Any]) -> str:
    opening = raw_game.get("opening")
    if isinstance(opening, dict):
        return opening.get("name") or "Unknown Opening"
    return "Unknown Opening"


def _resolve_color(raw_game: dict[str, Any], username: str) -> str:
    players = raw_game.get("players") or {}
    white_name = _extract_name(players.get("white"))
    if white_name.lower() == username.lower():
        return "white"
    return "black"


def _resolve_opponent(raw_game: dict[str, Any], username: str) -> str:
    players = raw_game.get("players") or {}
    white_name = _extract_name(players.get("white"))
    black_name = _extract_name(players.get("black"))
    if white_name.lower() == username.lower():
        return black_name
    return white_name


def _resolve_rating(raw_game: dict[str, Any], username: str) -> int | None:
    players = raw_game.get("players") or {}
    white_name = _extract_name(players.get("white"))
    color_data = players.get("white") if white_name.lower() == username.lower() else players.get("black")
    if isinstance(color_data, dict) and color_data.get("rating"):
        return int(color_data["rating"])
    return None


def _resolve_result(raw_game: dict[str, Any], username: str) -> str:
    winner = raw_game.get("winner")
    if not winner:
        return "DRAW"

    color = _resolve_color(raw_game, username)
    if winner == color:
        return "WIN"
    return "LOSS"


def _resolve_time_control(raw_game: dict[str, Any]) -> str:
    clock = raw_game.get("clock")
    if isinstance(clock, dict):
        initial = clock.get("initial")
        increment = clock.get("increment")
        if initial is not None and increment is not None:
            return f"{initial}+{increment}"
    return raw_game.get("speed", "")


def _resolve_played_at(raw_game: dict[str, Any]) -> datetime | None:
    created_at = raw_game.get("createdAt")
    if isinstance(created_at, int):
        return datetime.fromtimestamp(created_at / 1000, tz=UTC)
    return None


def _extract_name(color_data: Any) -> str:
    if not isinstance(color_data, dict):
        return "Unknown"
    user_blob = color_data.get("user")
    if isinstance(user_blob, dict):
        return user_blob.get("name", "Unknown")
    return "Unknown"


def _extract_ratings(profile: dict[str, Any]) -> dict[str, int]:
    perfs = profile.get("perfs") or {}
    ratings: dict[str, int] = {}
    for perf_key in ("bullet", "blitz", "rapid", "classical"):
        perf_data = perfs.get(perf_key)
        if isinstance(perf_data, dict) and perf_data.get("rating"):
            ratings[perf_key] = int(perf_data["rating"])
    return ratings
