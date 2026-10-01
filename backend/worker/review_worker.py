import json

import redis.exceptions
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.db.database import AsyncSessionLocal
from app.repositories.pull_request_repository import PullRequestRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.review_run_repository import ReviewRunRepository
from app.services.code_review_service import CodeReviewService
from app.services.review_run_service import ReviewRunService
from app.services.review_service import ReviewService
from app.services.review_job_service import ReviewJobService
from app.core.github_client import GitHubClient
from app.repositories.repository_repository import RepositoryRepository
from app.services.github_review_service import GitHubReviewService

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

repository_repository = RepositoryRepository()

github_review_service = GitHubReviewService(
    github_client=GitHubClient(),
)


from datetime import datetime, timedelta


STALE_AFTER_MINUTES = 10


async def recover_stale_runs():

    while True:

        try:

            stale_before = (
                datetime.utcnow()
                - timedelta(minutes=STALE_AFTER_MINUTES)
            )

            async with AsyncSessionLocal() as db:

                stale_runs = await review_run_service.get_stale_runs(
                    db,
                    stale_before,
                )

                for review_run in stale_runs:

                    await review_run_service.reset_to_pending(
                        db,
                        review_run,
                    )

                    await review_job_service.requeue(
                        review_run.id,
                    )

                    print(
                        f"Requeued stale ReviewRun {review_run.id}"
                    )

            await asyncio.sleep(60)

        except Exception as error:

            print(
                f"Recovery error: {error}"
            )

            await asyncio.sleep(10)


async def process_review_run(
    db: AsyncSession,
    review_run_id: int,
):
    print("calling review_run repository to get review run")
    review_run = await review_run_repository.get_by_id(
        db,
        review_run_id,
    )

    if review_run is None:
        print(
            f"ReviewRun {review_run_id} not found"
        )
        return

    print("calling pull request get by id --> pull_request_id")
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
        print("marking the review as running - > ")
        await review_run_service.mark_running(
            db,
            review_run,
        )

        if not pull_request.diff:
            raise ValueError(
                "Pull request has no diff"
            )

        print("calling the code_review_service to get review_diff with the help of llm - > ")

        review_result = await code_review_service.review_diff(
            pull_request.diff
        )


        print("saving the review result in db -> ")
        await review_service.save_review(
            db=db,
            pull_request_id=pull_request.id,
            review_run_id=review_run.id,
            review_result=review_result,
        )

        # GitHub publishing comes here.

        print("AI review completed")
        print(f"Findings: {len(review_result.findings)}")

        print("Loading repository...")

        repository = await repository_repository.get_by_id(
            db,
            pull_request.repository_id,
        )

        if repository is None:
            raise ValueError("Repository not found")

        print("Publishing review to GitHub...")

        github_response = await github_review_service.publish_review(
            repository=repository,
            pull_request=pull_request,
            review_result=review_result,
            commit_sha=review_run.commit_sha,
        )

        print(
            f"GitHub review published: {github_response.get('id')}"
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

            print("Calling process run ->")
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

async def main():

    await asyncio.gather(
        worker(),
        # recover_stale_runs(),
    )


if __name__ == "__main__":
    asyncio.run(main())