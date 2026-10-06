from pydantic import BaseModel
from vercel.queue import subscribe

from app.db.database import AsyncSessionLocal
from worker.review_processor import process_review_run


class ReviewJobPayload(BaseModel):
    review_run_id: int


@subscribe(
    topic="code-owl-review-jobs",
    consumer_group="code-owl-review-worker",
    retry_after=60,
    max_attempts=3,
)
async def process_review_job(message: ReviewJobPayload) -> None:

    review_run_id = message.review_run_id

    print(
        f"Processing ReviewRun {review_run_id}",
        flush=True,
    )

    async with AsyncSessionLocal() as db:

        await process_review_run(
            db=db,
            review_run_id=review_run_id,
        )