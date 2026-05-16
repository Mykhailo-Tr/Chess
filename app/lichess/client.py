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

    def get_rating_history(self, username: str, access_token: str | None = None) -> list[dict[str, Any]]:
        headers = {"Accept": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        response = requests.get(
            f"{self.api_base}/user/{username}/rating-history",
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def get_puzzle_dashboard(self, access_token: str, days: int = 30) -> dict[str, Any]:
        response = requests.get(
            f"{self.api_base}/puzzle/dashboard/{days}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def get_perf_stats(self, username: str, perf: str, access_token: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.api_base}/user/{username}/perf/{perf}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def get_user(self, username: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.api_base}/user/{username}",
            headers={"Accept": "application/json"},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def get_crosstable(self, user1: str, user2: str, access_token: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.api_base}/crosstable/{user1}/{user2}",
            params={"matchup": "true"},
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def get_playing(self, access_token: str) -> dict[str, Any] | None:
        try:
            response = requests.get(
                f"{self.api_base}/account/playing",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {access_token}",
                },
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                return None
            now_playing = payload.get("nowPlaying")
            if isinstance(now_playing, list) and now_playing:
                first_game = now_playing[0]
                if isinstance(first_game, dict):
                    return first_game
            return None
        except Exception:  # noqa: BLE001 - non-critical sidebar status
            return None
