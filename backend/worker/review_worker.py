import json
from backend.app.services import review_job_service
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
from app.services.review_job_service import ReviewJobService


review_job_service = ReviewJobService()

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

    pull_request = await pull_request_repository.get_by_id(
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


    try:
        await review_run_service.mark_running(
            db,
            review_run,
        )

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
            review_run_id=review_run.id,
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

            raw_job = await review_job_service.claim()

            if raw_job is None:
                continue

            job = json.loads(raw_job)

            review_run_id = job["review_run_id"]

            print(
                f"Processing ReviewRun {review_run_id}"
            )

            async with AsyncSessionLocal() as db:

                await process_review_run(
                    db,
                    review_run_id,
                )

            await review_job_service.acknowledge(
                raw_job,
            )

            print(
                f"ReviewRun {review_run_id} acknowledged"
            )

        except redis.exceptions.RedisError as error:

            print(
                f"Redis error: {error}"
            )

            await asyncio.sleep(2)

        except Exception as error:

            print(
                f"Unexpected worker error: {error}"
            )

            await asyncio.sleep(2)
if __name__ == "__main__":
    asyncio.run(worker())