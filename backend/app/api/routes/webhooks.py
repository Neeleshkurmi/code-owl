from fastapi import APIRouter, Request as FastAPIRequest, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.github import verify_github_signature
from app.db.database import get_db
from app.repositories.pull_request_repository import PullRequestRepository
from app.repositories.repository_repository import RepositoryRepository
from app.schemas.github import GitHubPullRequestEvent
from app.services.pull_request_service import PullRequestService
from app.core.github_client import GitHubClient
from app.repositories.review_repository import ReviewRepository
from app.services.code_review_service import CodeReviewService
from app.services.review_service import ReviewService
from app.repositories.review_run_repository import ReviewRunRepository
from app.services.review_run_service import ReviewRunService
from app.services.review_job_service import ReviewJobService



router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["webhooks"],
)

pull_request_service = PullRequestService(
    pull_request_repository=PullRequestRepository(),
    repository_repository=RepositoryRepository(),
    github_client=GitHubClient(),
)

code_review_service = CodeReviewService()

review_service = ReviewService(
    review_repository=ReviewRepository(),
)

review_run_service = ReviewRunService(
    repository=ReviewRunRepository(),
)

review_job_service = ReviewJobService()

@router.post("/github")
async def github_webhook(
    request : FastAPIRequest,
    db : AsyncSession = Depends(get_db)
) :

    print("🔥 WEBHOOK RECEIVED")
    
    payload = await request.body()

    signature = request.headers.get(
        "X-Hub-Signature-256"
    )

    if not verify_github_signature(
        payload,
        signature,
    ) : 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )
    
    event_name = request.headers.get(
        "X-GitHub-Event"
    )

    if event_name != "pull_request":
        return {
            "received": True,
            "processed": False,
            "reason": "Unsupported event",
        }

    data = await request.json()

    event = GitHubPullRequestEvent.model_validate(data)

    pull_request = await pull_request_service.process_pull_request_event(
        db,
        event,
    )

    if pull_request is None:
        return {
            "received": True,
            "processed": False,
            "action": event.action,
        }

    if not pull_request.diff : 
        return {
            "received" : True, 
            "processed" : False,
            "action" : event.action,
            "reason" : "Pull request has no diff",
        }

    review_run, created = await review_run_service.create_run(
        db=db,
        pull_request_id=pull_request.id,
        commit_sha=event.pull_request.head.sha,
    )

    if created :
        await review_job_service.enqueue(
            review_run_id=review_run.id,
        )

    response =  {
        "received": True,
        "processed": True,
        "action": event.action,
        "pull_request_id": pull_request.id,
        "review_run_id" : review_run.id,
        "review_run_created" : created,
    }

    print(response)

    return response