from pydantic import BaseModel, ConfigDict


class RepositoryCreate(BaseModel) :
    github_repo_id : int
    name : str
    full_name : str
    owner : str
    url : str


class RepositoryResponse(BaseModel) :
    id : int
    github_repo_id : int
    name : str
    full_name : str
    owner : str
    url : str
    is_active : bool

    model_config = ConfigDict(from_attributes=True)