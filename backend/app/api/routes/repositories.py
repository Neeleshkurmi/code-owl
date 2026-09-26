from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories.repository_repository import RepositoryRepository
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.services.repository_service import RepositoryService


router = APIRouter(
    prefix="/api/v1/repositories",
    tags=["repositories"]
)

repository_repository = RepositoryRepository()
repository_service = RepositoryService(
    repository_repository
)


@router.post(
    "",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_repository(
    repository_data: RepositoryCreate,
    db: AsyncSession = Depends(get_db),
):
    return await repository_service.create_repository(
        db,
        repository_data,
    )

@router.get(
    "",
    response_model=list[RepositoryResponse],
)
async def get_repositories(
    db : AsyncSession = Depends(get_db)
) : 
    return await repository_service.get_repositories(db)

@router.get(
    "/{repository_id}",
    response_model=RepositoryResponse,
)
async def get_repository(
    repository_id : int,
    db : AsyncSession = Depends(get_db)
) : 
    repository = await repository_service.get_repository(
        db,
        repository_id
    )

    if repository is None : 
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return repository