from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode

import requests
from flask import Flask


class LichessClient:
    def __init__(self, client_id: str, client_secret: str, api_base: str, oauth_url: str, token_url: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_base = api_base.rstrip("/")
        self.oauth_url = oauth_url
        self.token_url = token_url

    @classmethod
    def from_app(cls, app: Flask) -> "LichessClient":
        return cls(
            client_id=app.config["LICHESS_CLIENT_ID"],
            client_secret=app.config["LICHESS_CLIENT_SECRET"],
            api_base=app.config["LICHESS_API_BASE"],
            oauth_url=app.config["LICHESS_OAUTH_AUTHORIZE_URL"],
            token_url=app.config["LICHESS_OAUTH_TOKEN_URL"],
        )

    def build_authorize_url(self, redirect_uri: str, state: str, scope: str = "preference:read") -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
        }
        return f"{self.oauth_url}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict[str, Any]:
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def get_profile(self, access_token: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.api_base}/account",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def export_games(self, username: str, max_games: int = 50, access_token: str | None = None) -> list[dict[str, Any]]:
        headers = {"Accept": "application/x-ndjson"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        params = {
            "max": max_games,
            "opening": "true",
            "clocks": "true",
            "pgnInJson": "true",
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
