from fastapi import APIRouter

from app.schemas.review import ReviewResult
from app.services.code_review_service import CodeReviewService

router = APIRouter(
    prefix="/api/v1/reviews",
    tags=["reviews"],
)

review_service = CodeReviewService()


@router.post("/test", response_model=ReviewResult) 
async def test_review(diff : str) : 
    return await review_service.review_diff(diff)