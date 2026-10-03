from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_installation import GitHubInstallation
from app.repositories.github_installation_repository import (
    GitHubInstallationRepository,
)
from app.core.github_app import GitHubAppAuth


class GitHubInstallationService:

    def __init__(
        self,
        repository: GitHubInstallationRepository,
        github_app_auth : GitHubAppAuth
    ):
        self.repository = repository
        self.github_app_auth = github_app_auth

    async def get_or_create_installation(
        self,
        db: AsyncSession,
        github_installation_id: int,
    ) -> GitHubInstallation:

        existing = await self.repository.get_by_github_installation_id(
            db,
            github_installation_id,
        )

        if existing is not None:
            return existing

        installation_data = await self.github_app_auth.get_installation(
            installation_id=github_installation_id,
        )

        account = installation_data["account"]

        installation = GitHubInstallation(
            github_installation_id=installation_data["id"],
            account_id=account["id"],
            account_login=account["login"],
            account_type=account["type"],
            is_active=True,
        )

        return await self.repository.create(
            db=db,
            installation=installation,
        )