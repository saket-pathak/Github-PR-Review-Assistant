import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.bitbucket.client import BitbucketClient

@pytest.mark.asyncio
async def test_bitbucket_client_init_requires_token():
    with pytest.raises(ValueError, match="Bitbucket token or app password is required"):
        BitbucketClient(token="")

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_get_pull_request_success(mock_async_client_cls):
    mock_client = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 1, "title": "Test PR", "state": "OPEN"}
    mock_client.get.return_value = mock_response

    client = BitbucketClient(token="fake-token", username="user")
    pr_data = await client.get_pull_request("workspace/repo", 1)

    assert pr_data["id"] == 1
    assert pr_data["title"] == "Test PR"
    mock_client.get.assert_called_once_with(
        "https://api.bitbucket.org/2.0/repositories/workspace/repo/pullrequests/1",
        headers={"Accept": "application/json"},
        auth=("user", "fake-token")
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

    client = BitbucketClient(token="fake-token", username="user")
    with pytest.raises(HTTPException) as exc_info:
        await client.get_pull_request("workspace/repo", 1)

    assert exc_info.value.status_code == 404
    assert "Failed to fetch Bitbucket PR 1" in exc_info.value.detail

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_get_pull_request_diff_success(mock_async_client_cls):
    mock_client = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "diff --git a/file.py b/file.py\n+new_line"
    mock_client.get.return_value = mock_response

    client = BitbucketClient(token="fake-token", username="user")
    diff_text = await client.get_pull_request_diff("workspace/repo", 1)

    assert "new_line" in diff_text
    mock_client.get.assert_called_once_with(
        "https://api.bitbucket.org/2.0/repositories/workspace/repo/pullrequests/1/diff",
        headers={"Accept": "application/json"},
        auth=("user", "fake-token")
    )

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_post_comment_success(mock_async_client_cls):
    mock_client = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 100, "content": {"raw": "LGTM"}}
    mock_client.post.return_value = mock_response

    client = BitbucketClient(token="fake-token", username="user")
    response = await client.post_comment("workspace/repo", 1, "LGTM")

    assert response["id"] == 100
    mock_client.post.assert_called_once_with(
        "https://api.bitbucket.org/2.0/repositories/workspace/repo/pullrequests/1/comments",
        headers={"Accept": "application/json"},
        auth=("user", "fake-token"),
        json={"content": {"raw": "LGTM"}}
    )

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_post_inline_comment_success(mock_async_client_cls):
    mock_client = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 101}
    mock_client.post.return_value = mock_response

    client = BitbucketClient(token="fake-token", username="user")
    response = await client.post_inline_comment("workspace/repo", 1, "file.py", 12, "Use clean code")

    assert response["id"] == 101
    mock_client.post.assert_called_once_with(
        "https://api.bitbucket.org/2.0/repositories/workspace/repo/pullrequests/1/comments",
        headers={"Accept": "application/json"},
        auth=("user", "fake-token"),
        json={
            "content": {"raw": "Use clean code"},
            "inline": {"path": "file.py", "to": 12}
        }
    )
