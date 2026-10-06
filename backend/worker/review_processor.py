from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.pull_request_repository import PullRequestRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.review_run_repository import ReviewRunRepository
from app.repositories.repository_repository import RepositoryRepository

from app.services.code_review_service import CodeReviewService
from app.services.github_review_service import GitHubReviewService
from app.services.review_run_service import ReviewRunService
from app.services.review_service import ReviewService

from app.core.github_app import GitHubAppAuth
from app.core.github_client import GitHubClient


review_run_repository = ReviewRunRepository()
pull_request_repository = PullRequestRepository()
repository_repository = RepositoryRepository()

review_run_service = ReviewRunService(
    repository=review_run_repository,
)

review_service = ReviewService(
    review_repository=ReviewRepository(),
)

code_review_service = CodeReviewService()

github_auth_app = GitHubAppAuth()

github_client = GitHubClient(
    github_app_auth=github_auth_app,
)

github_review_service = GitHubReviewService(
    github_client=github_client,
)


async def process_review_run(
    db: AsyncSession,
    review_run_id: int,
) -> None:

    print(
        f"Processing ReviewRun {review_run_id}",
        flush=True,
    )

    review_run = await review_run_repository.get_by_id(
        db,
        review_run_id,
    )

    if review_run is None:
        print(
            f"ReviewRun {review_run_id} not found",
            flush=True,
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

        print(
            "Running AI code review...",
            flush=True,
        )

        review_result = await code_review_service.review_diff(
            pull_request.diff
        )

        print(
            "Saving review result...",
            flush=True,
        )

        await review_service.save_review(
            db=db,
            pull_request_id=pull_request.id,
            review_run_id=review_run.id,
            review_result=review_result,
        )

        repository = await repository_repository.get_by_id(
            db,
            pull_request.repository_id,
        )

        if repository is None:
            raise ValueError(
                "Repository not found"
            )

        print(
            "Publishing review to GitHub...",
            flush=True,
        )

        github_response = await github_review_service.publish_review(
            db=db,
            repository=repository,
            pull_request=pull_request,
            review_result=review_result,
            commit_sha=review_run.commit_sha,
        )

        if github_response is None:
            print(
                "No new findings. No GitHub review published.",
                flush=True,
            )
        else:
            print(
                f"GitHub review published: "
                f"{github_response.get('id')}",
                flush=True,
            )

        await review_run_service.mark_completed(
            db,
            review_run,
        )

        print(
            f"ReviewRun {review_run_id} completed",
            flush=True,
        )

    except Exception as error:

        await db.rollback()

        # Reload the ReviewRun after rollback.
        review_run = await review_run_repository.get_by_id(
            db,
            review_run_id,
        )

        if review_run is not None:
            await review_run_service.mark_failed(
                db,
                review_run,
                str(error),
            )

        print(
            f"ReviewRun {review_run_id} failed: {error}",
            flush=True,
        )

        raise