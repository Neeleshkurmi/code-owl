from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.review_run import ReviewRun
from app.repositories.review_run_repository import ReviewRunRepository
from tkinter.tix import STATUS


class ReviewRunService : 

    def __init__(
            self,
            repository : ReviewRunRepository
    ):
        self.repository=repository

    async def create_run (
            self,
            db : AsyncSession, 
            pull_request_id : int, 
            commit_sha : str,
    ) -> tuple[ReviewRun, bool] :

        existing_run = await self.repository.get_by_pull_request_and_commit(
            db,
            pull_request_id,
            commit_sha,
        )

        if existing_run is not None :
            return existing_run, False

        review_run = ReviewRun(
            pull_request_id = pull_request_id,
            commit_sha = commit_sha,
            status="PENDING",
        )

        try :
            created_run = await self.repository.create(
                db,
                review_run,
            )

            return created_run, True
        except IntegrityError :
            await db.rollback()

            existing_run = await self.repository.get_by_pull_request_and_commit(
                db,
                pull_request_id,
                commit_sha,
            )

            if existing_run is None :
                raise

            return existing_run, False
        

    async def mark_running(
            self,
            db : AsyncSession,
            review_run : ReviewRun,
    ) -> ReviewRun : 
        review_run.status = "RUNNING"
        review_run.started_at = datetime.utcnow()

        await db.commit()
        await db.refresh(review_run)

        return review_run

    async def mark_completed(
            self,
            db : AsyncSession,
            review_run : ReviewRun
    ) -> ReviewRun : 

        review_run.status = "COMPLETED"
        review_run.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(review_run)

        return review_run

    async def mark_failed(
            self,
            db : AsyncSession,
            review_run : ReviewRun,
            error_message : str
    ) -> ReviewRun : 

        review_run.status = "FAILED"
        review_run.error_message = error_message
        review_run.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(review_run)

        return review_run