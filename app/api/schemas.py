from pydantic import BaseModel

class ReviewRequest(BaseModel):
    repo: str
    pr_number: int

class ReviewResponse(BaseModel):
    status: str
    pr: int
    comments_posted: int
    summary: str
