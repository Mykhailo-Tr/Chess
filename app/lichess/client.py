from __future__ import annotations

import base64
import hashlib
import json
import os
from typing import Any
from urllib.parse import urlencode

import requests
from flask import Flask


def generate_pkce_pair() -> tuple[str, str]:
    """Returns (code_verifier, code_challenge)."""
    code_verifier = base64.urlsafe_b64encode(os.urandom(48)).rstrip(b"=").decode()
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


class LichessClient:
    def __init__(self, client_id: str, api_base: str, oauth_url: str, token_url: str) -> None:
        self.client_id = client_id
        self.api_base = api_base.rstrip("/")
        self.oauth_url = oauth_url
        self.token_url = token_url

    @classmethod
    def from_app(cls, app: Flask) -> "LichessClient":
        return cls(
            client_id=app.config["LICHESS_CLIENT_ID"],
            api_base=app.config["LICHESS_API_BASE"],
            oauth_url=app.config["LICHESS_OAUTH_AUTHORIZE_URL"],
            token_url=app.config["LICHESS_OAUTH_TOKEN_URL"],
        )

    def build_authorize_url(
        self,
        redirect_uri: str,
        state: str,
        code_challenge: str,
        scope: str = "preference:read",
    ) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{self.oauth_url}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str, redirect_uri: str, code_verifier: str) -> dict[str, Any]:
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.client_id,
                "code_verifier": code_verifier,
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