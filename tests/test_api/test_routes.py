import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app import create_app
from app.config import settings

client = TestClient(create_app())

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("app.services.review_service.run_review", new_callable=AsyncMock)
def test_review_pr_success(mock_run_review):
    mock_run_review.return_value = {
        "status": "success",
        "comments_posted": 3,
        "summary": "This is a great PR!"
    }

    payload = {"repo": "owner/repo", "pr_number": 42}
    response = client.post("/review", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "pr": 42,
        "comments_posted": 3,
        "summary": "This is a great PR!"
    }
    mock_run_review.assert_called_once_with("owner/repo", 42, post_to_github=True)

@patch("app.github.webhook.verify_signature")
@patch("app.github.webhook.parse_webhook_payload")
@patch("app.services.review_service.run_review", new_callable=AsyncMock)
def test_webhook_ignored_event(mock_run_review, mock_parse_payload, mock_verify_signature):
    mock_verify_signature.return_value = True
    mock_parse_payload.return_value = None  # not pull_request or not eligible action

    headers = {
        "X-GitHub-Event": "push",
        "X-Hub-Signature-256": "sha256=fakesig"
    }
    response = client.post("/webhook", json={}, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    mock_run_review.assert_not_called()

@patch("app.github.webhook.verify_signature")
@patch("app.github.webhook.parse_webhook_payload")
@patch("app.services.review_service.run_review", new_callable=AsyncMock)
def test_webhook_triggered_success(mock_run_review, mock_parse_payload, mock_verify_signature):
    # Enable webhook secret for testing signature validation
    settings.github_webhook_secret = "testsecret"
    mock_verify_signature.return_value = True
    mock_parse_payload.return_value = ("owner/repo", 101)

    headers = {
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": "sha256=validsig"
    }
    payload = {"action": "opened", "pull_request": {"number": 101}}
    response = client.post("/webhook", json=payload, headers=headers)
    
    assert response.status_code == 200
    assert response.json() == {
        "status": "triggered",
        "repo": "owner/repo",
        "pr": 101
    }
    mock_verify_signature.assert_called_once_with(b'{"action":"opened","pull_request":{"number":101}}', "sha256=validsig", "testsecret")
    mock_parse_payload.assert_called_once_with(payload, "pull_request")
