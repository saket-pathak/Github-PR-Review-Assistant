import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.services.bitbucket_review_service import run_bitbucket_review

@pytest.mark.asyncio
@patch("app.services.bitbucket_review_service.settings")
async def test_run_bitbucket_review_missing_token(mock_settings):
    mock_settings.bitbucket_token = ""
    with pytest.raises(ValueError, match="BITBUCKET_TOKEN config setting is missing."):
        await run_bitbucket_review("workspace/repo", 1)

@pytest.mark.asyncio
@patch("app.services.bitbucket_review_service.settings")
@patch("app.services.bitbucket_review_service.BitbucketClient")
@patch("app.services.bitbucket_review_service.LLMReviewer")
@patch("app.services.bitbucket_review_service.CommentService")
@patch("app.services.bitbucket_review_service.ReviewCache")
async def test_run_bitbucket_review_success_with_comments(
    mock_cache_cls,
    mock_comment_service,
    mock_llm_reviewer_cls,
    mock_bitbucket_client_cls,
    mock_settings
):
    mock_settings.bitbucket_token = "fake-token"
    mock_settings.bitbucket_username = "user"
    mock_settings.bitbucket_api_url = "https://api.bitbucket.org/2.0"
    mock_settings.llm_provider = "mock"
    
    mock_cache = MagicMock()
    mock_cache.get_comments.return_value = None
    mock_cache_cls.return_value = mock_cache

    mock_client = MagicMock()
    mock_client.get_pull_request_diff = AsyncMock(return_value="diff --git a/a.py b/a.py\n@@ -1 +1,2 @@\n+x = 1\n")
    mock_client.post_comment = AsyncMock()
    mock_client.post_inline_comment = AsyncMock()
    mock_bitbucket_client_cls.return_value = mock_client
    
    mock_reviewer = MagicMock()
    mock_reviewer.review_diff = AsyncMock(return_value={
        "summary": "This is a summary.",
        "comments": [{"path": "a.py", "line": 5, "comment": "use double quotes"}]
    })
    mock_llm_reviewer_cls.return_value = mock_reviewer
    
    formatted_comments = [{"path": "a.py", "line": 5, "body": "use double quotes"}]
    mock_comment_service.filter_and_format_comments.return_value = formatted_comments
    
    result = await run_bitbucket_review("workspace/repo", 1, post_to_bitbucket=True)
    
    assert result["status"] == "success"
    assert result["pr"] == 1
    assert result["comments_posted"] == 1
    assert result["summary"] == "This is a summary."
    assert result["comments"] == formatted_comments
    
    mock_client.get_pull_request_diff.assert_called_once_with("workspace/repo", 1)
    mock_client.post_comment.assert_called_once_with(
        "workspace/repo",
        1,
        "### 🤖 AI Code Review Summary\n\nThis is a summary."
    )
    mock_client.post_inline_comment.assert_called_once_with(
        repo="workspace/repo",
        pr_id=1,
        filename="a.py",
        line=5,
        body="use double quotes"
    )

@pytest.mark.asyncio
@patch("app.services.bitbucket_review_service.settings")
@patch("app.services.bitbucket_review_service.BitbucketClient")
@patch("app.services.bitbucket_review_service.LLMReviewer")
@patch("app.services.bitbucket_review_service.CommentService")
@patch("app.services.bitbucket_review_service.ReviewCache")
async def test_run_bitbucket_review_success_no_comments(
    mock_cache_cls,
    mock_comment_service,
    mock_llm_reviewer_cls,
    mock_bitbucket_client_cls,
    mock_settings
):
    mock_settings.bitbucket_token = "fake-token"
    mock_settings.bitbucket_username = "user"
    mock_settings.bitbucket_api_url = "https://api.bitbucket.org/2.0"
    mock_settings.llm_provider = "openai"
    mock_settings.openai_api_key = "fake-openai-key"
    
    mock_cache = MagicMock()
    mock_cache.get_comments.return_value = None
    mock_cache_cls.return_value = mock_cache

    mock_client = MagicMock()
    mock_client.get_pull_request_diff = AsyncMock(return_value="diff --git a/a.py b/a.py\n@@ -1 +1,2 @@\n+x = 1\n")
    mock_client.post_comment = AsyncMock()
    mock_bitbucket_client_cls.return_value = mock_client
    
    mock_reviewer = MagicMock()
    mock_reviewer.review_diff = AsyncMock(return_value={
        "summary": "No major issues found.",
        "comments": []
    })
    mock_llm_reviewer_cls.return_value = mock_reviewer
    
    mock_comment_service.filter_and_format_comments.return_value = []
    
    result = await run_bitbucket_review("workspace/repo", 1, post_to_bitbucket=True)
    
    assert result["status"] == "success"
    assert result["comments_posted"] == 0
    
    expected_body = "### 🤖 AI Code Review Summary\n\nNo major issues found.\n\nNo specific inline issues found. Code quality looks great! 👍"
    mock_client.post_comment.assert_called_once_with("workspace/repo", 1, expected_body)

@pytest.mark.asyncio
@patch("app.services.bitbucket_review_service.settings")
@patch("app.services.bitbucket_review_service.BitbucketClient")
@patch("app.services.bitbucket_review_service.LLMReviewer")
@patch("app.services.bitbucket_review_service.CommentService")
@patch("app.services.bitbucket_review_service.ReviewCache")
async def test_run_bitbucket_review_no_post(
    mock_cache_cls,
    mock_comment_service,
    mock_llm_reviewer_cls,
    mock_bitbucket_client_cls,
    mock_settings
):
    mock_settings.bitbucket_token = "fake-token"
    mock_settings.bitbucket_username = "user"
    mock_settings.bitbucket_api_url = "https://api.bitbucket.org/2.0"
    mock_settings.llm_provider = "anthropic"
    mock_settings.anthropic_api_key = "fake-anthropic-key"
    
    mock_cache = MagicMock()
    mock_cache.get_comments.return_value = None
    mock_cache_cls.return_value = mock_cache

    mock_client = MagicMock()
    mock_client.get_pull_request_diff = AsyncMock(return_value="diff --git a/a.py b/a.py\n@@ -1 +1,2 @@\n+x = 1\n")
    mock_client.post_comment = AsyncMock()
    mock_client.post_inline_comment = AsyncMock()
    mock_bitbucket_client_cls.return_value = mock_client
    
    mock_reviewer = MagicMock()
    mock_reviewer.review_diff = AsyncMock(return_value={
        "summary": "This is a summary.",
        "comments": [{"path": "a.py", "line": 5, "comment": "use double quotes"}]
    })
    mock_llm_reviewer_cls.return_value = mock_reviewer
    
    formatted_comments = [{"path": "a.py", "line": 5, "body": "use double quotes"}]
    mock_comment_service.filter_and_format_comments.return_value = formatted_comments
    
    result = await run_bitbucket_review("workspace/repo", 1, post_to_bitbucket=False)
    
    assert result["status"] == "success"
    assert result["comments_posted"] == 0
    assert result["comments"] == formatted_comments
    
    mock_client.post_comment.assert_not_called()
    mock_client.post_inline_comment.assert_not_called()

@pytest.mark.asyncio
@patch("app.services.bitbucket_review_service.settings")
@patch("app.services.bitbucket_review_service.BitbucketClient")
@patch("app.services.bitbucket_review_service.LLMReviewer")
@patch("app.services.bitbucket_review_service.ReviewCache")
async def test_run_bitbucket_review_cache_hit(
    mock_cache_cls,
    mock_llm_reviewer_cls,
    mock_bitbucket_client_cls,
    mock_settings
):
    mock_settings.bitbucket_token = "fake-token"
    mock_settings.bitbucket_username = "user"
    mock_settings.bitbucket_api_url = "https://api.bitbucket.org/2.0"
    
    mock_client = MagicMock()
    mock_client.get_pull_request_diff = AsyncMock(return_value="diff --git a/a.py b/a.py\n@@ -1 +1 @@\n-x\n+y\n")
    mock_client.post_comment = AsyncMock()
    mock_bitbucket_client_cls.return_value = mock_client
    
    mock_cache = MagicMock()
    cached_comments = [{"path": "a.py", "line": 1, "body": "fix styling"}]
    mock_cache.get_comments.return_value = cached_comments
    mock_cache_cls.return_value = mock_cache
    
    mock_reviewer = MagicMock()
    mock_reviewer.review_diff = AsyncMock()
    mock_llm_reviewer_cls.return_value = mock_reviewer
    
    result = await run_bitbucket_review("workspace/repo", 1, post_to_bitbucket=True)
    
    assert result["status"] == "success"
    assert result["comments"] == cached_comments
    assert "previously reviewed" in result["summary"]
    
    mock_reviewer.review_diff.assert_not_called()
    mock_client.post_comment.assert_called_once()
