import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.gitlab.client import GitLabClient

@pytest.mark.asyncio
async def test_gitlab_client_init_requires_token():
    with pytest.raises(ValueError, match="GITLAB_TOKEN is required"):
        GitLabClient(token="")

def test_gitlab_client_project_id_encoding():
    client = GitLabClient(token="fake-token")
    assert client._encode_project_id("123") == "123"
    assert client._encode_project_id("gitlab-org/gitlab") == "gitlab-org%2Fgitlab"

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_get_merge_request_success(mock_async_client_cls):
    mock_client = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 123, "state": "opened", "title": "Test MR"}
    mock_client.get.return_value = mock_response

    client = GitLabClient(token="fake-token")
    mr_data = await client.get_merge_request("gitlab-org/gitlab", 42)

    assert mr_data["id"] == 123
    assert mr_data["title"] == "Test MR"
    mock_client.get.assert_called_once_with(
        "https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab/merge_requests/42",
        headers={
            "PRIVATE-TOKEN": "fake-token",
            "Accept": "application/json",
        }
    )

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_get_merge_request_failure(mock_async_client_cls):
    mock_client = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_client.get.return_value = mock_response

    client = GitLabClient(token="fake-token")
    with pytest.raises(HTTPException) as exc_info:
        await client.get_merge_request("gitlab-org/gitlab", 42)

    assert exc_info.value.status_code == 404
    assert "Failed to fetch GitLab MR 42" in exc_info.value.detail

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_get_merge_request_changes_success(mock_async_client_cls):
    mock_client = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"changes": [{"new_path": "main.py", "diff": "@@ -1 +1 @@"}]}
    mock_client.get.return_value = mock_response

    client = GitLabClient(token="fake-token")
    changes = await client.get_merge_request_changes("gitlab-org/gitlab", 42)

    assert "changes" in changes
    assert len(changes["changes"]) == 1
    mock_client.get.assert_called_once_with(
        "https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab/merge_requests/42/changes",
        headers={
            "PRIVATE-TOKEN": "fake-token",
            "Accept": "application/json",
        }
    )

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_post_comment_success(mock_async_client_cls):
    mock_client = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 555, "body": "LGTM"}
    mock_client.post.return_value = mock_response

    client = GitLabClient(token="fake-token")
    response = await client.post_comment("gitlab-org/gitlab", 42, "LGTM")

    assert response["id"] == 555
    mock_client.post.assert_called_once_with(
        "https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab/merge_requests/42/notes",
        headers={
            "PRIVATE-TOKEN": "fake-token",
            "Accept": "application/json",
        },
        json={"body": "LGTM"}
    )

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_post_discussion_success(mock_async_client_cls):
    mock_client = AsyncMock()
    mock_async_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 777}
    mock_client.post.return_value = mock_response

    client = GitLabClient(token="fake-token")
    response = await client.post_discussion(
        project_id="gitlab-org/gitlab",
        mr_iid=42,
        base_sha="base123",
        start_sha="start123",
        head_sha="head123",
        path="main.py",
        line=10,
        body="Fix this styling"
    )

    assert response["id"] == 777
    mock_client.post.assert_called_once_with(
        "https://gitlab.com/api/v4/projects/gitlab-org%2Fgitlab/merge_requests/42/discussions",
        headers={
            "PRIVATE-TOKEN": "fake-token",
            "Accept": "application/json",
        },
        json={
            "body": "Fix this styling",
            "position": {
                "base_sha": "base123",
                "start_sha": "start123",
                "head_sha": "head123",
                "position_type": "text",
                "new_path": "main.py",
                "new_line": 10
            }
        }
    )
