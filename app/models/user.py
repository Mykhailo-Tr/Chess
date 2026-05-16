from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from flask_login import UserMixin

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    lichess_id = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(120), unique=True, nullable=False, index=True)
    access_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    ratings_snapshot = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    last_synced_at = db.Column(db.DateTime(timezone=True), nullable=True)

    games = db.relationship("Game", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    reports = db.relationship("AnalysisReport", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

    def is_token_valid(self) -> bool:
        if not self.access_token:
            return False
        if self.token_expires_at is None:
            return True
        return datetime.now(UTC) < self.token_expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "lichess_id": self.lichess_id,
            "ratings_snapshot": self.ratings_snapshot or {},
        }


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))
