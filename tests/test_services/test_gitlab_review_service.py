import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.services.gitlab_review_service import run_gitlab_review

@pytest.mark.asyncio
@patch("app.services.gitlab_review_service.settings")
async def test_run_gitlab_review_missing_token(mock_settings):
    mock_settings.gitlab_token = ""
    with pytest.raises(ValueError, match="GITLAB_TOKEN config setting is missing."):
        await run_gitlab_review("gitlab-org/gitlab", 42)

@pytest.mark.asyncio
@patch("app.services.gitlab_review_service.settings")
@patch("app.services.gitlab_review_service.GitLabClient")
async def test_run_gitlab_review_missing_diff_refs(mock_gitlab_client_cls, mock_settings):
    mock_settings.gitlab_token = "fake-token"
    mock_settings.gitlab_api_url = "https://gitlab.com/api/v4"
    mock_settings.llm_provider = "mock"

    mock_client = MagicMock()
    mock_client.get_merge_request = AsyncMock(return_value={"id": 123, "diff_refs": {}})
    mock_gitlab_client_cls.return_value = mock_client

    with pytest.raises(ValueError, match="Could not extract diff_refs"):
        await run_gitlab_review("gitlab-org/gitlab", 42)

@pytest.mark.asyncio
@patch("app.services.gitlab_review_service.settings")
@patch("app.services.gitlab_review_service.GitLabClient")
@patch("app.services.gitlab_review_service.LLMReviewer")
@patch("app.services.gitlab_review_service.CommentService")
@patch("app.services.gitlab_review_service.ReviewCache")
async def test_run_gitlab_review_success_with_comments(
    mock_cache_cls,
    mock_comment_service,
    mock_llm_reviewer_cls,
    mock_gitlab_client_cls,
    mock_settings
):
    # 1. Setup mocks
    mock_settings.gitlab_token = "fake-token"
    mock_settings.gitlab_api_url = "https://gitlab.com/api/v4"
    mock_settings.llm_provider = "mock"
    
    # Mock ReviewCache
    mock_cache = MagicMock()
    mock_cache.get_comments.return_value = None
    mock_cache_cls.return_value = mock_cache

    # Mock GitLabClient
    mock_client = MagicMock()
    mock_client.get_merge_request = AsyncMock(return_value={
        "id": 123,
        "diff_refs": {
            "base_sha": "base123",
            "start_sha": "start123",
            "head_sha": "head123"
        }
    })
    mock_client.get_merge_request_changes = AsyncMock(return_value={
        "changes": [{"new_path": "a.py", "diff": "@@ -1 +1,2 @@\n+x = 1\n"}]
    })
    mock_client.post_comment = AsyncMock()
    mock_client.post_discussion = AsyncMock()
    mock_gitlab_client_cls.return_value = mock_client
    
    # Mock LLMReviewer
    mock_reviewer = MagicMock()
    mock_reviewer.review_diff = AsyncMock(return_value={
        "summary": "This is a summary.",
        "comments": [{"path": "a.py", "line": 5, "comment": "use double quotes"}]
    })
    mock_llm_reviewer_cls.return_value = mock_reviewer
    
    # Mock CommentService
    formatted_comments = [{"path": "a.py", "line": 5, "body": "use double quotes"}]
    mock_comment_service.filter_and_format_comments.return_value = formatted_comments
    
    # 2. Run service function
    result = await run_gitlab_review("gitlab-org/gitlab", 42, post_to_gitlab=True)
    
    # 3. Assertions
    assert result["status"] == "success"
    assert result["mr"] == 42
    assert result["comments_posted"] == 1
    assert result["summary"] == "This is a summary."
    assert result["comments"] == formatted_comments
    
    mock_client.get_merge_request.assert_called_once_with("gitlab-org/gitlab", 42)
    mock_client.get_merge_request_changes.assert_called_once_with("gitlab-org/gitlab", 42)
    mock_client.post_comment.assert_called_once_with(
        "gitlab-org/gitlab",
        42,
        "### 🤖 AI Code Review Summary\n\nThis is a summary."
    )
    mock_client.post_discussion.assert_called_once_with(
        project_id="gitlab-org/gitlab",
        mr_iid=42,
        base_sha="base123",
        start_sha="start123",
        head_sha="head123",
        path="a.py",
        line=5,
        body="use double quotes"
    )

@pytest.mark.asyncio
@patch("app.services.gitlab_review_service.settings")
@patch("app.services.gitlab_review_service.GitLabClient")
@patch("app.services.gitlab_review_service.LLMReviewer")
@patch("app.services.gitlab_review_service.CommentService")
@patch("app.services.gitlab_review_service.ReviewCache")
async def test_run_gitlab_review_success_no_comments(
    mock_cache_cls,
    mock_comment_service,
    mock_llm_reviewer_cls,
    mock_gitlab_client_cls,
    mock_settings
):
    # 1. Setup mocks
    mock_settings.gitlab_token = "fake-token"
    mock_settings.gitlab_api_url = "https://gitlab.com/api/v4"
    mock_settings.llm_provider = "openai"
    mock_settings.openai_api_key = "fake-openai-key"
    
    # Mock ReviewCache
    mock_cache = MagicMock()
    mock_cache.get_comments.return_value = None
    mock_cache_cls.return_value = mock_cache

    # Mock GitLabClient
    mock_client = MagicMock()
    mock_client.get_merge_request = AsyncMock(return_value={
        "id": 123,
        "diff_refs": {
            "base_sha": "base123",
            "start_sha": "start123",
            "head_sha": "head123"
        }
    })
    mock_client.get_merge_request_changes = AsyncMock(return_value={
        "changes": [{"new_path": "a.py", "diff": "@@ -1 +1,2 @@\n+x = 1\n"}]
    })
    mock_client.post_comment = AsyncMock()
    mock_gitlab_client_cls.return_value = mock_client
    
    # Mock LLMReviewer
    mock_reviewer = MagicMock()
    mock_reviewer.review_diff = AsyncMock(return_value={
        "summary": "No major issues found.",
        "comments": []
    })
    mock_llm_reviewer_cls.return_value = mock_reviewer
    
    # Mock CommentService
    mock_comment_service.filter_and_format_comments.return_value = []
    
    # 2. Run service function
    result = await run_gitlab_review("gitlab-org/gitlab", 42, post_to_gitlab=True)
    
    # 3. Assertions
    assert result["status"] == "success"
    assert result["comments_posted"] == 0
    
    expected_body = "### 🤖 AI Code Review Summary\n\nNo major issues found.\n\nNo specific inline issues found. Code quality looks great! 👍"
    mock_client.post_comment.assert_called_once_with("gitlab-org/gitlab", 42, expected_body)

@pytest.mark.asyncio
@patch("app.services.gitlab_review_service.settings")
@patch("app.services.gitlab_review_service.GitLabClient")
@patch("app.services.gitlab_review_service.LLMReviewer")
@patch("app.services.gitlab_review_service.CommentService")
@patch("app.services.gitlab_review_service.ReviewCache")
async def test_run_gitlab_review_no_post(
    mock_cache_cls,
    mock_comment_service,
    mock_llm_reviewer_cls,
    mock_gitlab_client_cls,
    mock_settings
):
    # 1. Setup mocks
    mock_settings.gitlab_token = "fake-token"
    mock_settings.gitlab_api_url = "https://gitlab.com/api/v4"
    mock_settings.llm_provider = "anthropic"
    mock_settings.anthropic_api_key = "fake-anthropic-key"
    
    # Mock ReviewCache
    mock_cache = MagicMock()
    mock_cache.get_comments.return_value = None
    mock_cache_cls.return_value = mock_cache

    # Mock GitLabClient
    mock_client = MagicMock()
    mock_client.get_merge_request = AsyncMock(return_value={
        "id": 123,
        "diff_refs": {
            "base_sha": "base123",
            "start_sha": "start123",
            "head_sha": "head123"
        }
    })
    mock_client.get_merge_request_changes = AsyncMock(return_value={
        "changes": [{"new_path": "a.py", "diff": "@@ -1 +1,2 @@\n+x = 1\n"}]
    })
    mock_client.post_comment = AsyncMock()
    mock_client.post_discussion = AsyncMock()
    mock_gitlab_client_cls.return_value = mock_client
    
    # Mock LLMReviewer
    mock_reviewer = MagicMock()
    mock_reviewer.review_diff = AsyncMock(return_value={
        "summary": "This is a summary.",
        "comments": [{"path": "a.py", "line": 5, "comment": "use double quotes"}]
    })
    mock_llm_reviewer_cls.return_value = mock_reviewer
    
    # Mock CommentService
    formatted_comments = [{"path": "a.py", "line": 5, "body": "use double quotes"}]
    mock_comment_service.filter_and_format_comments.return_value = formatted_comments
    
    # 2. Run service function with post_to_gitlab=False
    result = await run_gitlab_review("gitlab-org/gitlab", 42, post_to_gitlab=False)
    
    # 3. Assertions
    assert result["status"] == "success"
    assert result["comments_posted"] == 0
    assert result["comments"] == formatted_comments
    
    mock_client.post_comment.assert_not_called()
    mock_client.post_discussion.assert_not_called()

@pytest.mark.asyncio
@patch("app.services.gitlab_review_service.settings")
@patch("app.services.gitlab_review_service.GitLabClient")
@patch("app.services.gitlab_review_service.LLMReviewer")
@patch("app.services.gitlab_review_service.ReviewCache")
async def test_run_gitlab_review_cache_hit(
    mock_cache_cls,
    mock_llm_reviewer_cls,
    mock_gitlab_client_cls,
    mock_settings
):
    mock_settings.gitlab_token = "fake-token"
    mock_settings.gitlab_api_url = "https://gitlab.com/api/v4"
    
    # Mock GitLabClient
    mock_client = MagicMock()
    mock_client.get_merge_request = AsyncMock(return_value={
        "id": 123,
        "diff_refs": {
            "base_sha": "base123",
            "start_sha": "start123",
            "head_sha": "head123"
        }
    })
    mock_client.get_merge_request_changes = AsyncMock(return_value={
        "changes": [{"new_path": "a.py", "diff": "@@ -1 +1 @@\n-x\n+y\n"}]
    })
    mock_client.post_comment = AsyncMock()
    mock_gitlab_client_cls.return_value = mock_client
    
    # Mock ReviewCache to return cached comments
    mock_cache = MagicMock()
    cached_comments = [{"path": "a.py", "line": 1, "body": "fix styling"}]
    mock_cache.get_comments.return_value = cached_comments
    mock_cache_cls.return_value = mock_cache
    
    # Mock LLMReviewer (should NOT be called since file is cached)
    mock_reviewer = MagicMock()
    mock_reviewer.review_diff = AsyncMock()
    mock_llm_reviewer_cls.return_value = mock_reviewer
    
    result = await run_gitlab_review("gitlab-org/gitlab", 42, post_to_gitlab=True)
    
    assert result["status"] == "success"
    assert result["comments"] == cached_comments
    assert "previously reviewed" in result["summary"]
    
    mock_reviewer.review_diff.assert_not_called()
    mock_client.post_comment.assert_called_once()
