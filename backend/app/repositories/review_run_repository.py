from unittest import result

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review_run import ReviewRun


class ReviewRunRepository:

    async def create(
        self,
        db: AsyncSession,
        review_run: ReviewRun,
    ) -> ReviewRun:

        db.add(review_run)

        await db.commit()
        await db.refresh(review_run)

        return review_run

    async def get_by_id(
        self,
        db: AsyncSession,
        review_run_id: int,
    ) -> ReviewRun | None:

        result = await db.execute(
            select(ReviewRun).where(
                ReviewRun.id == review_run_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_pull_request_and_commit(
            self,
            db : AsyncSession,
            pull_request_id : int,
            commit_sha : str,
    ) -> ReviewRun | None : 
        result = await db.execute(
            select(ReviewRun).where(
                ReviewRun.pull_request_id == pull_request_id,
                ReviewRun.commit_sha == commit_sha,
            )
        )

        return result.scalar_one_or_none()