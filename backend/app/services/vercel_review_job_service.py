from vercel.queue import send


class VercelReviewJobService:

    QUEUE_NAME = "code-owl-review-jobs"

    async def enqueue(
        self,
        review_run_id: int,
    ) -> str | None:

        return await send(
            self.QUEUE_NAME,
            {
                "review_run_id": review_run_id,
            },
        )