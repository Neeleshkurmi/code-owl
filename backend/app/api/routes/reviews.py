from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.review import ReviewResult
from app.services.code_review_service import CodeReviewService
from app.db.database import get_db
from app.repositories.review_repository import ReviewRepository
from app.services.review_service import ReviewService

router = APIRouter(
    prefix="/api/v1/reviews",
    tags=["reviews"],
)

code_review_service = CodeReviewService()

review_service = ReviewService(
    review_repository=ReviewRepository()
)


@router.post("/test", response_model=ReviewResult) 
async def test_review(
    diff : str,
    db : AsyncSession = Depends(get_db)
) : 

    result = await code_review_service.review_diff(
        diff
    )

    pull_request_id = 1
    review_run_id = 1

    await review_service.save_review(
        db=db,
        pull_request_id=pull_request_id,
        review_run_id=review_run_id,
        review_result=result,
    )

    return result