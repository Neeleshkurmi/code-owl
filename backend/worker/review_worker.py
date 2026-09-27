import json
import redis.exceptions
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.redis import redis_client
from app.db.database import AsyncSessionLocal
from app.repositories.pull_request_repository import PullRequestRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.review_run_repository import ReviewRunRepository
from app.services.code_review_service import CodeReviewService
from app.services.review_run_service import ReviewRunService
from app.services.review_service import ReviewService


QUEUE_NAME = "review_jobs"


review_run_repository = ReviewRunRepository()
pull_request_repository = PullRequestRepository()

review_run_service = ReviewRunService(
    repository=review_run_repository,
)

review_service = ReviewService(
    review_repository=ReviewRepository(),
)

code_review_service = CodeReviewService()


async def process_review_run(
    db: AsyncSession,
    review_run_id: int,
):
    review_run = await review_run_repository.get_by_id(
        db,
        review_run_id,
    )

    if review_run is None:
        print(
            f"ReviewRun {review_run_id} not found"
        )
        return

    pull_request = await pull_request_repository.get_by_github_id(
        db,
        review_run.pull_request_id,
    )

    if pull_request is None:
        await review_run_service.mark_failed(
            db,
            review_run,
            "Pull request not found",
        )
        return

    await review_run_service.mark_running(
        db,
        review_run,
    )

    try:

        if not pull_request.diff:
            raise ValueError(
                "Pull request has no diff"
            )

        review_result = await code_review_service.review_diff(
            pull_request.diff
        )

        await review_service.save_review(
            db=db,
            pull_request_id=pull_request.id,
            review_result=review_result,
        )

        await review_run_service.mark_completed(
            db,
            review_run,
        )

        print(
            f"ReviewRun {review_run_id} completed"
        )

    except Exception as error:

        await db.rollback()

        await review_run_service.mark_failed(
            db,
            review_run,
            str(error),
        )

        print(
            f"ReviewRun {review_run_id} failed: {error}"
        )

async def worker():
    print("Review worker started")

    while True:
        try:
            # 1. Wait for a job up to 5 seconds
            result = await redis_client.blpop(
                QUEUE_NAME,
                timeout=5,
            )

            # 2. If result is None (timeout reached without data), loop again
            if not result:
                continue

            # 3. Process the job if data exists
            _, raw_job = result
            job = json.loads(raw_job)
            review_run_id = job["review_run_id"]

            print(f"Processing ReviewRun {review_run_id}")

            async with AsyncSessionLocal() as db:
                await process_review_run(
                    db,
                    review_run_id,
                )

        except redis.exceptions.TimeoutError:
            # Normal behavior: Redis timed out waiting for a message. Just keep listening.
            print("Queue empty, waiting for jobs...")
            continue
            
        except Exception as e:
            # Protects the loop: Prevents the entire worker from crashing on unexpected errors
            print(f"Unexpected error in worker loop: {e}")
            await asyncio.sleep(2)  # Avoid a tight CPU loop if the database or Redis goes down

if __name__ == "__main__":
    asyncio.run(worker())