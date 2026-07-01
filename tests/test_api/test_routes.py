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
        "platform": "github",
        "repo": "owner/repo",
        "pr": 101
    }
    mock_verify_signature.assert_called_once_with(b'{"action":"opened","pull_request":{"number":101}}', "sha256=validsig", "testsecret")
    mock_parse_payload.assert_called_once_with(payload, "pull_request")


@patch("app.services.gitlab_review_service.run_gitlab_review", new_callable=AsyncMock)
def test_review_mr_success(mock_run_gitlab_review):
    mock_run_gitlab_review.return_value = {
        "status": "success",
        "comments_posted": 2,
        "summary": "This is a great MR!"
    }

    payload = {"repo": "gitlab-org/gitlab", "pr_number": 42, "platform": "gitlab"}
    response = client.post("/review", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "pr": 42,
        "comments_posted": 2,
        "summary": "This is a great MR!"
    }
    mock_run_gitlab_review.assert_called_once_with("gitlab-org/gitlab", 42, post_to_gitlab=True)


@patch("app.gitlab.webhook.verify_gitlab_token")
@patch("app.gitlab.webhook.parse_gitlab_webhook")
@patch("app.services.gitlab_review_service.run_gitlab_review", new_callable=AsyncMock)
def test_gitlab_webhook_triggered_success(mock_run_gitlab_review, mock_parse_gitlab_webhook, mock_verify_gitlab_token):
    settings.gitlab_webhook_secret = "gitlabsecret"
    mock_verify_gitlab_token.return_value = True
    mock_parse_gitlab_webhook.return_value = ("gitlab-org/gitlab", 42)

    headers = {
        "X-Gitlab-Event": "Merge Request Hook",
        "X-Gitlab-Token": "gitlabsecret"
    }
    payload = {"object_attributes": {"action": "open", "iid": 42}}
    response = client.post("/webhook", json=payload, headers=headers)
    
    assert response.status_code == 200
    assert response.json() == {
        "status": "triggered",
        "platform": "gitlab",
        "repo": "gitlab-org/gitlab",
        "pr": 42
    }
    mock_verify_gitlab_token.assert_called_once_with("gitlabsecret", "gitlabsecret")
    mock_parse_gitlab_webhook.assert_called_once_with(payload, "Merge Request Hook")


@patch("app.gitlab.webhook.verify_gitlab_token")
def test_gitlab_webhook_signature_failure(mock_verify_gitlab_token):
    settings.gitlab_webhook_secret = "gitlabsecret"
    mock_verify_gitlab_token.return_value = False

    headers = {
        "X-Gitlab-Event": "Merge Request Hook",
        "X-Gitlab-Token": "wrongsecret"
    }
    response = client.post("/webhook", json={}, headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid GitLab webhook token"


@patch("app.gitlab.webhook.verify_gitlab_token")
@patch("app.gitlab.webhook.parse_gitlab_webhook")
def test_gitlab_webhook_ignored_event(mock_parse_gitlab_webhook, mock_verify_gitlab_token):
    settings.gitlab_webhook_secret = ""
    mock_verify_gitlab_token.return_value = True
    mock_parse_gitlab_webhook.return_value = None

    headers = {
        "X-Gitlab-Event": "Push Hook"
    }
    response = client.post("/webhook", json={}, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


@patch("app.services.bitbucket_review_service.run_bitbucket_review", new_callable=AsyncMock)
def test_review_bitbucket_pr_success(mock_run_bitbucket_review):
    mock_run_bitbucket_review.return_value = {
        "status": "success",
        "comments_posted": 4,
        "summary": "Nice Bitbucket PR!"
    }

    payload = {"repo": "workspace/repo", "pr_number": 1, "platform": "bitbucket"}
    response = client.post("/review", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "pr": 1,
        "comments_posted": 4,
        "summary": "Nice Bitbucket PR!"
    }
    mock_run_bitbucket_review.assert_called_once_with("workspace/repo", 1, post_to_bitbucket=True)


@patch("app.bitbucket.webhook.verify_bitbucket_signature")
@patch("app.bitbucket.webhook.parse_bitbucket_webhook")
@patch("app.services.bitbucket_review_service.run_bitbucket_review", new_callable=AsyncMock)
def test_bitbucket_webhook_triggered_success(mock_run_bitbucket_review, mock_parse_bitbucket_webhook, mock_verify_signature):
    settings.bitbucket_webhook_secret = "bbsecret"
    mock_verify_signature.return_value = True
    mock_parse_bitbucket_webhook.return_value = ("workspace/repo", 1)

    headers = {
        "X-Event-Key": "pullrequest:created",
        "X-Hub-Signature": "sha256=bbsig"
    }
    payload = {"pullrequest": {"id": 1}}
    response = client.post("/webhook", json=payload, headers=headers)
    
    assert response.status_code == 200
    assert response.json() == {
        "status": "triggered",
        "platform": "bitbucket",
        "repo": "workspace/repo",
        "pr": 1
    }
    mock_verify_signature.assert_called_once_with(b'{"pullrequest":{"id":1}}', "sha256=bbsig", "bbsecret")
    mock_parse_bitbucket_webhook.assert_called_once_with(payload, "pullrequest:created")


@patch("app.bitbucket.webhook.verify_bitbucket_signature")
def test_bitbucket_webhook_signature_failure(mock_verify_signature):
    settings.bitbucket_webhook_secret = "bbsecret"
    mock_verify_signature.return_value = False

    headers = {
        "X-Event-Key": "pullrequest:created",
        "X-Hub-Signature": "sha256=wrongsig"
    }
    response = client.post("/webhook", json={}, headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Bitbucket webhook signature"


@patch("app.bitbucket.webhook.verify_bitbucket_signature")
@patch("app.bitbucket.webhook.parse_bitbucket_webhook")
def test_bitbucket_webhook_ignored_event(mock_parse_bitbucket_webhook, mock_verify_signature):
    settings.bitbucket_webhook_secret = ""
    mock_verify_signature.return_value = True
    mock_parse_bitbucket_webhook.return_value = None

    headers = {
        "X-Event-Key": "repo:push"
    }
    response = client.post("/webhook", json={}, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
