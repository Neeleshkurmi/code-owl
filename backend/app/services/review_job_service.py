import json

from app.core.redis import redis_client


class ReviewJobService:

    QUEUE_NAME = "review_jobs"

    async def enqueue(
        self,
        review_run_id: int,
    ) -> None:

        job = {
            "review_run_id": review_run_id,
        }

        await redis_client.rpush(
            self.QUEUE_NAME,
            json.dumps(job),
        )