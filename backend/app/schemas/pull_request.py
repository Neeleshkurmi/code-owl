from pydantic import BaseModel

class PullRequestResponse(BaseModel):
    id: int
    github_pr_id: int
    repository_id: int
    number: int
    title: str
    body: str | None
    html_url: str
    base_branch: str
    head_branch: str

    model_config = {
        "from_attributes": True,
    }