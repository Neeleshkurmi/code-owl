from unittest import result

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def get_by_github_id(
            self,
            db : AsyncSession,
            repository_id : int,
    ) -> Repository | None : 

        result = await db.execute(
            select(Repository).where(
                Repository.id == repository_id
            )
        )

        return result.scalar_one_or_none()