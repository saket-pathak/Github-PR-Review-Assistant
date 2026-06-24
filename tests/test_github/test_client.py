import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.github.client import GitHubClient

@pytest.mark.asyncio
async def test_github_client_init_requires_token():
    with pytest.raises(ValueError, match="GITHUB_TOKEN is required"):
        GitHubClient(token="")

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_get_pull_request_success(mock_async_client_cls):
    mock_client = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 123, "state": "open", "title": "Test PR"}
    mock_client.get.return_value = mock_response

    client = GitHubClient(token="fake-token")
    pr_data = await client.get_pull_request("owner/repo", 42)

    assert pr_data["id"] == 123
    assert pr_data["title"] == "Test PR"
    mock_client.get.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/pulls/42",
        headers={
            "Authorization": "token fake-token",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_get_pull_request_failure(mock_async_client_cls):
    mock_client = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_client.get.return_value = mock_response

    client = GitHubClient(token="fake-token")
    with pytest.raises(HTTPException) as exc_info:
        await client.get_pull_request("owner/repo", 42)

    assert exc_info.value.status_code == 404
    assert "Failed to fetch PR 42" in exc_info.value.detail

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_get_pull_request_files_success(mock_async_client_cls):
    mock_client = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"filename": "app/main.py", "status": "modified"}]
    mock_client.get.return_value = mock_response

    client = GitHubClient(token="fake-token")
    files = await client.get_pull_request_files("owner/repo", 42)

    assert len(files) == 1
    assert files[0]["filename"] == "app/main.py"
    mock_client.get.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/pulls/42/files",
        headers={
            "Authorization": "token fake-token",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        params={"per_page": 100}
    )

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_post_review_success(mock_async_client_cls):
    mock_client = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 999, "state": "COMMENTED"}
    mock_client.post.return_value = mock_response

    client = GitHubClient(token="fake-token")
    comments = [{"path": "main.py", "line": 10, "side": "RIGHT", "body": "Fix this"}]
    response = await client.post_review(
        repo="owner/repo",
        pr_number=42,
        commit_id="sha123",
        body="LGTM",
        comments=comments
    )

    assert response["id"] == 999
    mock_client.post.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/pulls/42/reviews",
        headers={
            "Authorization": "token fake-token",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={
            "commit_id": "sha123",
            "body": "LGTM",
            "event": "COMMENT",
            "comments": comments
        }
    )
