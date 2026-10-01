from app.core.github_client import GitHubClient
from app.models.pull_request import PullRequest
from app.models.repository import Repository
from app.schemas.review import ReviewResult
from app.services.diff_parser import DiffParser


class GitHubReviewService:

    def __init__(
        self,
        github_client: GitHubClient,
    ):
        self.github_client = github_client

    async def publish_review(
        self,
        repository: Repository,
        pull_request: PullRequest,
        review_result: ReviewResult,
        commit_sha: str,
    ) -> dict:

        comments = []

        changed_lines = DiffParser.get_changed_lines(
            pull_request.diff or ""
        )

        for finding in review_result.findings:

            if finding.line is None:
                continue

            file_lines = changed_lines.get(finding.file)

            if file_lines is None:
                print(
                    f"Skipping finding: file not in diff -> "
                    f"{finding.file}"
                )
                continue

            if finding.line not in file_lines:
                print(
                    f"Skipping finding: line not changed -> "
                    f"{finding.file}:{finding.line}"
                )
                continue

            body = (
                f"**{finding.severity.upper()}**\n\n"
                f"{finding.message}"
            )

            if finding.suggestions:
                body += (
                    f"\n\n**Suggestion:** "
                    f"{finding.suggestions}"
                )

            comments.append(
                {
                    "path": finding.file,
                    "body": body,
                    "line": finding.line,
                    "side": "RIGHT",
                }
            )

        summary = review_result.summary

        if not comments:
            summary = (
                summary
                + "\n\n"
                + "No inline findings could be mapped to changed lines."
            )

        return await self.github_client.create_pull_request_review(
            owner=repository.owner,
            repo=repository.name,
            pull_request_number=pull_request.number,
            commit_sha=commit_sha,
            body=summary,
            comments=comments if comments else None,
        )