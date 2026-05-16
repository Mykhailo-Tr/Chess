from __future__ import annotations

import json
from typing import Any

import requests
from flask import Flask


class LichessClient:
    def __init__(self, client_id: str, api_base: str) -> None:
        self.client_id = client_id
        self.api_base = api_base.rstrip("/")

    @classmethod
    def from_app(cls, app: Flask) -> "LichessClient":
        return cls(
            client_id=app.config.get("LICHESS_CLIENT_ID", "chess-app"),
            api_base=app.config["LICHESS_API_BASE"],
        )

    def get_profile(self, access_token: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.api_base}/account",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def export_games(
        self,
        username: str,
        max_games: int = 50,
        access_token: str | None = None,
    ) -> list[dict[str, Any]]:
        headers = {"Accept": "application/x-ndjson"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        params = {
            "max": max_games,
            "opening": "true",
            "clocks": "true",
            "accuracy": "true",
            "division": "true",
            "pgnInJson": "true",
            "moves": "true",
        }
        response = requests.get(
            f"{self.api_base}/games/user/{username}",
            params=params,
            headers=headers,
            timeout=45,
        )
        response.raise_for_status()

        games: list[dict[str, Any]] = []
        for line in response.text.splitlines():
            line = line.strip()
            if not line:
                continue
            games.append(json.loads(line))
        return games
