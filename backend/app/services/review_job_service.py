import json

from app.core.redis import redis_client


class ReviewJobService:

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