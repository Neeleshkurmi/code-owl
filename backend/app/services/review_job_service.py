import json
from datetime import datetime

from app.core.redis import redis_client
from app.models.review_run import ReviewRun

from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.review_run_repository import ReviewRunRepository



class ReviewJobService:

    def __init__(self):
        self.repository = ReviewRunRepository()

    QUEUE_NAME = "review_jobs"
    PROCESSING_QUEUE_NAME = "review_jobs_processing"

    async def enqueue(
        self,
        review_run_id: int,
    ) -> None:

        job = {
            "review_run_id": review_run_id,
            "claimed_at" : None,
        }

        await redis_client.rpush(
            self.QUEUE_NAME,
            json.dumps(job),
        )

    async def claim(
        self,
    ) -> str | None:

        return await redis_client.brpoplpush(
            self.QUEUE_NAME,
            self.PROCESSING_QUEUE_NAME,
            timeout=5,
        )

    async def acknowledge(
        self,
        raw_job: str,
    ) -> None:

        await redis_client.lrem(
            self.PROCESSING_QUEUE_NAME,
            1,
            raw_job,
        )

    async def get_processing_jobs(
            self,
    ) -> list[str] :

        return await redis_client.lrange(
            self.PROCESSING_QUEUE_NAME,
            0,
            -1,
        )

    async def get_stale_runs(
        self,
        db: AsyncSession,
        stale_before: datetime,
    ) -> list[ReviewRun]:

        return await self.repository.get_stale_running_runs(
            db,
            stale_before,
        )

    async def requeue(
        self,
        review_run_id: int,
    ) -> None:

        job = {
            "review_run_id": review_run_id,
            "claimed_at": None,
        }

        await redis_client.rpush(
            self.QUEUE_NAME,
            json.dumps(job),
        )