from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pull_request import PullRequest


class PullRequestRepository:

    async def get_by_id(
        self,
        db: AsyncSession,
        pull_request_id: int,
    ) -> PullRequest | None:

        print("Fetching PullRequest by internal ID")
        result = await db.execute(
            select(PullRequest).where(
                PullRequest.id == pull_request_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_github_pr_id(
            self,
            db: AsyncSession,
            github_pr_id : int,
        ) -> PullRequest | None:

            print("Fetching PullRequest by GitHub PR ID")
    
            result = await db.execute(
                select(PullRequest).where(
                    PullRequest.github_pr_id == github_pr_id
                )
            )
    
            return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        pull_request: PullRequest,
    ) -> PullRequest:

        db.add(pull_request)

        await db.commit()
        await db.refresh(pull_request)

        return pull_request