from pydantic import BaseModel


class GitHubOwnerPayload(BaseModel):
    login: str


class GitHubRepositoryPayload(BaseModel):
    id: int
    name: str
    full_name: str
    html_url: str
    owner: GitHubOwnerPayload


class GitHubBranchPayload(BaseModel):
    ref: str
    sha : str


class GitHubPullRequestPayload(BaseModel):
    id: int
    number: int
    title: str
    body: str | None = None
    html_url: str
    base: GitHubBranchPayload
    head: GitHubBranchPayload


class GitHubPullRequestEvent(BaseModel):
    action: str
    installation: GitHubInstallationPayload
    repository: GitHubRepositoryPayload
    pull_request: GitHubPullRequestPayload



class GitHubInstallationPayload(BaseModel):
    id: int


class GitHubInstallationAccountPayload(BaseModel):
    id: int
    login: str
    type: str


class GitHubInstallationResponse(BaseModel):
    id: int
    account: GitHubInstallationAccount


class GitHubInstallationAccount(BaseModel):
    id: int
    login: str
    type: str