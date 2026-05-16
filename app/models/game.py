from __future__ import annotations

from datetime import datetime, UTC

from app.extensions import db


class Game(db.Model):
    __tablename__ = "games"
    __table_args__ = (db.UniqueConstraint("user_id", "lichess_game_id", name="uq_user_lichess_game"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    lichess_game_id = db.Column(db.String(64), nullable=False, index=True)
    pgn = db.Column(db.Text, nullable=False)
    result = db.Column(db.String(12), nullable=False)  # WIN | LOSS | DRAW
    opening = db.Column(db.String(255), nullable=True)
    eco = db.Column(db.String(8), nullable=True)  # ECO code e.g. "B20"
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    played_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)

    opponent = db.Column(db.String(120), nullable=True)
    user_color = db.Column(db.String(5), nullable=True)  # white | black
    time_control = db.Column(db.String(32), nullable=True)
    speed = db.Column(db.String(32), nullable=True)
    termination = db.Column(db.String(64), nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    moves_count = db.Column(db.Integer, nullable=True)
    clock_data = db.Column(db.JSON, nullable=True)
    division_json = db.Column(db.JSON, nullable=True)  # {"middle": ply, "end": ply}
    metadata_json = db.Column(db.JSON, nullable=True)

    user = db.relationship("User", back_populates="games")
