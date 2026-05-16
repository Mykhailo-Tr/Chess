from __future__ import annotations

from datetime import datetime, UTC

from app.extensions import db


class AnalysisReport(db.Model):
    __tablename__ = "analysis_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    generated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    games_analyzed = db.Column(db.Integer, nullable=False, default=0)
    winrate = db.Column(db.Float, nullable=False, default=0.0)
    avg_accuracy = db.Column(db.Float, nullable=True)
    tilt_level = db.Column(db.String(16), nullable=False, default="LOW")
    tilt_score = db.Column(db.Float, nullable=False, default=0.0)
    time_pressure_score = db.Column(db.Float, nullable=False, default=0.0)
    payload = db.Column(db.JSON, nullable=False, default=dict)

    user = db.relationship("User", back_populates="reports")
