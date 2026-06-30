import pytest
from pydantic import ValidationError
from app.api.schemas import ReviewRequest, ReviewResponse

def test_review_request_validation_success():
    # Valid payload
    payload = {
        "repo": "owner/repo",
        "pr_number": 123
    }
    request = ReviewRequest(**payload)
    assert request.repo == "owner/repo"
    assert request.pr_number == 123
    assert request.platform == "github"

def test_review_request_validation_custom_platform():
    payload = {
        "repo": "gitlab-org/gitlab",
        "pr_number": 42,
        "platform": "gitlab"
    }
    request = ReviewRequest(**payload)
    assert request.repo == "gitlab-org/gitlab"
    assert request.pr_number == 42
    assert request.platform == "gitlab"

def test_review_request_validation_missing_fields():
    # Missing pr_number
    with pytest.raises(ValidationError):
        ReviewRequest(repo="owner/repo")
        
    # Missing repo
    with pytest.raises(ValidationError):
        ReviewRequest(pr_number=123)

def test_review_request_validation_invalid_types():
    # pr_number must be parseable as an integer
    with pytest.raises(ValidationError):
        ReviewRequest(repo="owner/repo", pr_number="not-a-number")

def test_review_response_validation_success():
    payload = {
        "status": "success",
        "pr": 42,
        "comments_posted": 2,
        "summary": "This is a brief summary of the changes."
    }
    response = ReviewResponse(**payload)
    assert response.status == "success"
    assert response.pr == 42
    assert response.comments_posted == 2
    assert response.summary == "This is a brief summary of the changes."

def test_review_response_validation_missing_fields():
    # Missing summary
    with pytest.raises(ValidationError):
        ReviewResponse(status="success", pr=42, comments_posted=2)
