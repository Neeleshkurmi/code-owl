from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.repository import Repository


class RepositoryRepository:

    async def create(
            self,
            db : AsyncSession, 
            repository : Repository,
    ) -> Repository : 
        db.add(repository)

        await db.commit()
        await db.refresh(repository)

        return repository

    async def get_all(
            self, 
            db : AsyncSession,
    ) -> list[Repository] : 
        result = await db.execute(
            select(Repository)
        )

        return list(result.scalars().all())


    async def get_by_id(self, db, repository_id):
        result = await db.execute(
            select(Repository).where(
                Repository.id == repository_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_github_repo_id(self, db, repository_id):
            result = await db.execute(
                select(Repository).where(
                    Repository.github_repo_id == repository_id
                )
            )
            return result.scalar_one_or_none()

    async def get_or_create(
    self,
    db: AsyncSession,
    github_repo_id: int,
    name: str,
    full_name: str,
    owner: str,
    url: str,
) -> Repository:

        existing = await self.get_by_github_repo_id(
            db,
            github_repo_id,
        )

        if existing is not None:
            return existing

        repository = Repository(
            github_repo_id=github_repo_id,
            name=name,
            full_name=full_name,
            owner=owner,
            url=url,
        )

        try:
            async with db.begin_nested():
                db.add(repository)
                await db.flush()

        except IntegrityError:
            existing = await self.get_by_github_repo_id(
                db,
                github_repo_id,
            )

            if existing is None:
                raise

            return existing

        await db.commit()
        await db.refresh(repository)

        return repository

    