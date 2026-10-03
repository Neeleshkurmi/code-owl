from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_installation import GitHubInstallation


class GitHubInstallationRepository:

    async def get_by_github_installation_id(
        self,
        db: AsyncSession,
        github_installation_id: int,
    ) -> GitHubInstallation | None:
        result = await db.execute(
            select(GitHubInstallation).where(
                GitHubInstallation.github_installation_id
                == github_installation_id
            )
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        installation: GitHubInstallation,
    ) -> GitHubInstallation:
        db.add(installation)

        await db.commit()
        await db.refresh(installation)

        return installation

    async def get_by_id(
        self,
        db: AsyncSession,
        installation_id: int,
    ) -> GitHubInstallation | None:
        result = await db.execute(
            select(GitHubInstallation).where(
                GitHubInstallation.id == installation_id
            )
        )

        return result.scalar_one_or_none()