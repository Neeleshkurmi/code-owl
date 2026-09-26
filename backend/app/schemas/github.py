from pydantic import BaseModel

class GitHubRepositoryPayload(BaseModel) :
    id : int
    name : str
    full_name : str
    html_url : str

class GitHubPullRequestPayload(BaseModel) :
    number : int
    title : str
    body : str | None = None
    html_url : str
    base : str
    head : dict



class GitHubPullRequestEvent(BaseModel) :
    action : str
    repository : GitHubRepositoryPayload
    pull_request : GitHubPullRequestPayload

class GitHubOwnerPayload(BaseModel) :
    login : str

class GitHubBranchPayload(BaseModel) :
    ref : str

