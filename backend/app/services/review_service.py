from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.models.review_findings import ReviewFinding
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewResult


class ReviewService:

    def __init__(
        self,
        review_repository: ReviewRepository,
    ):
        self.review_repository = review_repository

    async def save_review(
        self,
        db: AsyncSession,
        pull_request_id: int,
        review_result: ReviewResult,
    ) -> Review:

        review = Review(
            pull_request_id=pull_request_id,
            summary=review_result.summary,
        )

        for finding_data in review_result.findings:

            finding = ReviewFinding(
                severity=finding_data.severity,
                file=finding_data.file,
                line=finding_data.line,
                message=finding_data.message,
                suggestion=finding_data.suggestions,
            )

            review.findings.append(finding)

        return await self.review_repository.create(
            db,
            review,
        )