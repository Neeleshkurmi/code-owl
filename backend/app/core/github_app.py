from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import jwt

from app.core.config import settings


class GitHubAppAuth:
    def __init__(self):
        self.app_id = settings.github_app_id
        self.base_url = settings.github_api_url

        private_key_path = Path(
            settings.github_app_private_key_path
        )

        if not private_key_path.exists():
            raise FileNotFoundError(
                f"GitHub App private key not found: {private_key_path}"
            )

        self.private_key = private_key_path.read_bytes()

    def generate_jwt(self) -> str:
        now = datetime.now(timezone.utc)

        payload = {
            "iat": int((now - timedelta(seconds=60)).timestamp()),
            "exp": int((now + timedelta(minutes=9)).timestamp()),
            "iss": str(self.app_id),
        }

        return jwt.encode(
            payload,
            self.private_key,
            algorithm="RS256",
        )

    async def generate_installation_token(
        self,
        installation_id: int,
    ) -> str:
        app_jwt = self.generate_jwt()

        url = (
            f"{self.base_url}/app/installations/"
            f"{installation_id}/access_tokens"
        )

        headers = {
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
            )

        response.raise_for_status()

        data = response.json()

        return data["token"]

    async def get_installation(
        self,
        installation_id: int,
    ) -> dict:
        app_jwt = self.generate_jwt()

        url = (
            f"{self.base_url}/app/installations/"
            f"{installation_id}"
        )

        headers = {
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
            )

        response.raise_for_status()

        return response.json()