import re

from app.core.github_client import GitHubClient
from app.models.pull_request import PullRequest
from app.models.repository import Repository
from app.schemas.review import ReviewResult
from app.services.diff_parser import DiffParser
from app.repositories.github_installation_repository import GitHubInstallationRepository


AI_REVIEW_MARKER = "<!-- ai-pr-review -->"

github_installation_repository = GitHubInstallationRepository()


class GitHubReviewService:

    def __init__(
        self,
        github_client: GitHubClient,
    ):
        self.github_client = github_client

    @staticmethod
    def normalize_text(text: str) -> str:

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @classmethod
    def is_same_finding(
        cls,
        finding,
        existing_comment: dict,
    ) -> bool:

        existing_path = existing_comment.get("path")

        if existing_path != finding.file:
            return False

        existing_body = existing_comment.get("body", "")

        existing_body = existing_body.replace(
            AI_REVIEW_MARKER,
            "",
        )

        existing_body = cls.normalize_text(
            existing_body
        )

        finding_text = cls.normalize_text(
            finding.message
        )

        if not finding_text:
            return False

        # Exact normalized message match
        if finding_text in existing_body:
            return True

        # Compare the important words in the finding.
        finding_words = set(
            finding_text.split()
        )

        existing_words = set(
            existing_body.split()
        )

        if not finding_words:
            return False

        overlap = (
            len(finding_words & existing_words)
            / len(finding_words)
        )

        return overlap >= 0.80

    async def publish_review(
        self,
        db,
        repository: Repository,
        pull_request: PullRequest,
        review_result: ReviewResult,
        commit_sha: str,
    ) -> dict | None:

        changed_lines = DiffParser.get_changed_lines(
            pull_request.diff or ""
        )

        installation = await github_installation_repository.get_by_id(
            db=db,
            installation_id=repository.installation_id,
        )

        if installation is None:
            raise RuntimeError(
                f"GitHub installation not found for repository "
                f"{repository.id}: {repository.installation_id}"
            )

        existing_comments = (
            await self.github_client
            .get_pull_request_review_comments(
                owner=repository.owner,
                repo=repository.name,
                pull_request_number=pull_request.number,
                installation_id=installation.github_installation_id,
            )
        )

        existing_ai_comments = [
            comment
            for comment in existing_comments
            if AI_REVIEW_MARKER
            in comment.get("body", "")
        ]

        print(
            f"Existing AI comments: "
            f"{len(existing_ai_comments)}"
        )

        comments = []

        for finding in review_result.findings:

            if finding.line is None:
                continue

            file_lines = changed_lines.get(
                finding.file
            )

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

            already_reported = any(
                self.is_same_finding(
                    finding,
                    existing_comment,
                )
                for existing_comment
                in existing_ai_comments
            )

            if already_reported:
                print(
                    f"Skipping duplicate finding -> "
                    f"{finding.file}:{finding.line}"
                )
                continue

            body = (
                f"{AI_REVIEW_MARKER}\n\n"
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

        # Critical:
        # Do not create an empty GitHub review.
        if not comments:
            print(
                "No new AI findings to publish."
            )
            return None

        summary = (
            f"AI Code Review\n\n"
            f"{review_result.summary}\n\n"
            f"New findings: {len(comments)}"
        )

        return await self.github_client.create_pull_request_review(
            owner=repository.owner,
            repo=repository.name,
            pull_request_number=pull_request.number,
            commit_sha=commit_sha,
            body=summary,
            comments=comments,
            installation_id=installation.github_installation_id,
        )