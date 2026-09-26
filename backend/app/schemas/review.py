from pydantic import BaseModel


class ReviewFinding(BaseModel) :
    severity : str
    file : str
    line : int | None = None
    message : str
    suggestions : str | None = None


class ReviewResult(BaseModel) :
    findings : list[ReviewFinding]
    summary : str