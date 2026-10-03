import httpx

from app.core.config import settings
from app.core.github_app import GitHubAppAuth


class GitHubClient:
    def __init__(self, github_app_auth: GitHubAppAuth):
        self.base_url = settings.github_api_url
        self.github_app_auth = github_app_auth

    async def get_pull_request_diff(
        self,
        installation_id: int,
        owner: str,
        repo: str,
        pull_request_number: int,
    ) -> str:
        url = (
            f"{self.base_url}/repos/"
            f"{owner}/{repo}/pulls/{pull_request_number}"
        )

        headers = await self._get_headers(
            installation_id=installation_id,
            accept="application/vnd.github.v3.diff",
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
            )

        response.raise_for_status()

        return response.text

    async def create_pull_request_review(
        self,
        owner: str,
        repo: str,
        pull_request_number: int,
        commit_sha: str,
        body: str,
        comments: list[dict] | None,
        installation_id : int,
    ) -> dict:

        url = (
            f"{self.base_url}/repos/"
            f"{owner}/{repo}/pulls/{pull_request_number}/reviews"
        )

        payload = {
            "commit_id": commit_sha,
            "body": body,
            "event": "COMMENT",
        }

        if comments :
            payload["comments"] = comments

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers= await self._get_headers(
                    installation_id=installation_id
                ),
                json=payload,
            )

        if response.is_error:
            print("GitHub API error:")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            print(
                "Accepted GitHub permissions:",
                response.headers.get("X-Accepted-GitHub-Permissions"),
            )

        response.raise_for_status()

        return response.json()


    async def get_pull_request_review_comments(
        self,
        owner: str,
        repo: str,
        pull_request_number: int,
        installation_id : int,
    ) -> list[dict]:

        comments = []
        page = 1

        async with httpx.AsyncClient() as client:

            while True:

                url = (
                    f"{self.base_url}/repos/"
                    f"{owner}/{repo}/pulls/"
                    f"{pull_request_number}/comments"
                )

                response = await client.get(
                    url,
                    headers = await self._get_headers(
                        installation_id=installation_id
                    ),
                    params={
                        "per_page": 100,
                        "page": page,
                    },
                )

                response.raise_for_status()

                page_comments = response.json()

                if not page_comments:
                    break

                comments.extend(page_comments)

                if len(page_comments) < 100:
                    break

                page += 1

        return comments

    async def _get_headers(
        self,
        installation_id: int,
        accept: str = "application/vnd.github+json",
    ) -> dict:
        token = await self.github_app_auth.generate_installation_token(
            installation_id
        )

        return {
            "Authorization": f"Bearer {token}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
        }