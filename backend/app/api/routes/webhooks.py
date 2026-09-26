from fastapi import APIRouter, Request as FastAPIRequest, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.github import verify_github_signature
from app.db.database import get_db
from app.repositories.pull_request_repository import PullRequestRepository
from app.repositories.repository_repository import RepositoryRepository
from app.schemas.github import GitHubPullRequestEvent
from app.services.pull_request_service import PullRequestService
from app.core.github_client import GitHubClient



router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["webhooks"],
)

pull_request_service = PullRequestService(
    pull_request_repository=PullRequestRepository(),
    repository_repository=RepositoryRepository(),
    github_client=GitHubClient(),
)

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

    return {
        "received": True,
        "processed": True,
        "action": event.action,
        "pull_request_id": pull_request.id,
        "github_pr_id": pull_request.github_pr_id,
    }