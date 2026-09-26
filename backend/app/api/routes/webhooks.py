from email import header
from json import JSONDecodeError
from urllib import request
from webbrowser import get
from fastapi import APIRouter, Request as FastAPIRequest, HTTPException, status

from app.schemas.github import GitHubPullRequestEvent
from app.core.github import verify_github_signature


router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["webhooks"],
)

@router.post("/github")
async def github_webhook(request : FastAPIRequest) :
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

    data = await request.json()

    event = GitHubPullRequestEvent.model_validate(data)

    return {
        "received": True,
        "event": request.headers.get("X-GitHub-Event"),
        "action": event.action,
        "repository": event.repository.full_name,
        "pull_request_number": event.pull_request.number,
        "pull_request_title": event.pull_request.title,
    }