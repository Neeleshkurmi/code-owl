from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.models.review_finding import ReviewFinding


class ReviewRepository:

    async def create(
        self,
        db: AsyncSession,
        review: Review,
    ) -> Review:

        db.add(review)

        await db.commit()
        await db.refresh(review)

        return review

    async def create_finding(
        self,
        db: AsyncSession,
        finding: ReviewFinding,
    ) -> ReviewFinding:

        db.add(finding)

        await db.commit()
        await db.refresh(finding)

        return finding