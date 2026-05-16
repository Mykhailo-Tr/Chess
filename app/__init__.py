from __future__ import annotations

import os
from typing import Any

from flask import Flask

from app.config import config_by_name
from app.extensions import db, login_manager
from app.lichess.client import LichessClient


def create_app(config_name: str | None = None, test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    if test_config is not None:
        app.config.from_mapping(test_config)
    else:
        selected_config = config_name or os.getenv("FLASK_ENV", "development")
        app.config.from_object(config_by_name.get(selected_config, config_by_name["development"]))

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.auth import auth_bp
    from app.dashboard import dashboard_bp
    from app.analytics import analytics_bp
    from app.lichess import lichess_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(lichess_bp, url_prefix="/lichess")

    @app.context_processor
    def inject_live_game():
        from flask_login import current_user

        live = None
        # This performs an HTTP request on every page load and should be replaced
        # with caching/background polling in production.
        if current_user.is_authenticated and current_user.access_token:
            try:
                client = LichessClient.from_app(app)
                live = client.get_playing(current_user.access_token)
            except Exception:  # noqa: BLE001 - non-critical sidebar indicator
                pass
        return {"live_game": live}

    with app.app_context():
        db.create_all()

    return app
