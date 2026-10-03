from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pull_request import PullRequest
from app.repositories.pull_request_repository import PullRequestRepository
from app.repositories.repository_repository import RepositoryRepository
from app.schemas.github import GitHubPullRequestEvent
from app.core.github_client import GitHubClient


class PullRequestService:

    def __init__(
        self,
        pull_request_repository: PullRequestRepository,
        repository_repository: RepositoryRepository,
        github_client : GitHubClient
    ):
        self.pull_request_repository = pull_request_repository
        self.repository_repository = repository_repository
        self.github_client = github_client

    async def process_pull_request_event(
        self,
        db,
        event,
        installation_id : int,
    ):
        supported_actions = {
            "opened",
            "reopened",
            "synchronize",
        }

        if event.action not in supported_actions:
            return None

        github_repository = event.repository
        github_pr = event.pull_request

        repository = await self.repository_repository.get_or_create(
            db=db,
            installation_id=installation_id,
            github_repo_id=github_repository.id,
            name=github_repository.name,
            full_name=github_repository.full_name,
            owner=github_repository.owner.login,
            url=github_repository.html_url,
        )

        diff = await self.github_client.get_pull_request_diff(
            installation_id=event.installation.id,
            owner=github_repository.owner.login,
            repo=github_repository.name,
            pull_request_number=github_pr.number,
        )

        existing_pr = await self.pull_request_repository.get_by_github_pr_id(
            db,
            github_pr.id,
        )

        if existing_pr is None:
            pull_request = PullRequest(
                github_pr_id=github_pr.id,
                repository_id=repository.id,
                number=github_pr.number,
                title=github_pr.title,
                body=github_pr.body,
                html_url=github_pr.html_url,
                base_branch=github_pr.base.ref,
                head_branch=github_pr.head.ref,
                diff=diff,
            )

            return await self.pull_request_repository.create(
                db,
                pull_request,
            )

        existing_pr.title = github_pr.title
        existing_pr.body = github_pr.body
        existing_pr.html_url = github_pr.html_url
        existing_pr.base_branch = github_pr.base.ref
        existing_pr.head_branch = github_pr.head.ref
        existing_pr.diff = diff

        await db.commit()
        await db.refresh(existing_pr)

        return existing_pr