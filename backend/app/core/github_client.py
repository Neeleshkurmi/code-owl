import httpx

from app.core.config import settings


class GitHubClient :
    
    def __init__(self):
        self.base_url = settings.github_api_url
        self.headers = {
            "Authorization": f"Bearer {settings.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_pull_request_diff(
            self,
            owner: str,
            repo : str,
            pull_request_number : int
    ) -> str : 

        url = (
            f"{self.base_url}/repos/"
            f"{owner}/{repo}/pulls/{pull_request_number}"
        )

        print(f"DEBUG: Attempting to connect to URL: {url}")

        headers = {
            **self.headers,
            "Accept" : "application/vnd.github.v3.diff",
        }

        async with httpx.AsyncClient() as client : 
            response = await client.get(
                url,
                headers=headers,
            )

        response.raise_for_status()

        return response.text