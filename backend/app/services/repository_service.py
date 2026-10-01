from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.repository import Repository
from app.repositories.repository_repository import RepositoryRepository
from app.schemas.repository import RepositoryCreate


class RepositoryService : 

    def __init__(
            self,
            repository_repository : RepositoryRepository
    ) : 
        self.repository_repository = repository_repository

    async def create_repository(
            self,
            db : AsyncSession,
            repository_data : RepositoryCreate
    ) -> Repository : 

        existing_repository = (
            await self.repository_repository.get_by_id(
                db,
                repository_data.github_repo_id,
            )
        )

        if existing_repository is not None:
            raise HTTPException(
                status_code=409,
                detail="Repository already exists",
            )

        repository = Repository(
            github_repo_id=repository_data.github_repo_id,
            name=repository_data.name,
            full_name=repository_data.full_name,
            owner=repository_data.owner,
            url=repository_data.url
        )

        return await self.repository_repository.create(
            db,
            repository,
        )

    async def get_repositories(
              self, 
              db : AsyncSession,
    ) -> list[Repository] :
        return await self.repository_repository.get_all(db)

    async def get_repository(
            self,
            db : AsyncSession,
            repository_id : int,
    ) -> Repository | None : 

        return await self.repository_repository.get_by_id(
            db,
            repository_id
        )