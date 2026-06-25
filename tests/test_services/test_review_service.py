import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.review_service import run_review

@pytest.mark.asyncio
@patch("app.services.review_service.settings")
async def test_run_review_missing_github_token(mock_settings):
    # Setup settings to have no github_token
    mock_settings.github_token = ""
    
    with pytest.raises(ValueError, match="GITHUB_TOKEN config setting is missing."):
        await run_review("owner/repo", 42)

@pytest.mark.asyncio
@patch("app.services.review_service.settings")
@patch("app.services.review_service.GitHubClient")
@patch("app.services.review_service.LLMReviewer")
@patch("app.services.review_service.CommentService")
async def test_run_review_success_with_comments(
    mock_comment_service,
    mock_llm_reviewer_cls,
    mock_github_client_cls,
    mock_settings
):
    # 1. Setup mocks
    mock_settings.github_token = "fake-github-token"
    mock_settings.llm_provider = "mock"
    
    # Mock GitHubClient
    mock_gh_client = MagicMock()
    mock_gh_client.get_pull_request = AsyncMock(return_value={"head": {"sha": "abcdef12345"}})
    mock_gh_client.get_pull_request_files = AsyncMock(return_value=[{"filename": "a.py"}])
    mock_gh_client.post_review = AsyncMock()
    mock_github_client_cls.return_value = mock_gh_client
    
    # Mock LLMReviewer
    mock_reviewer = MagicMock()
    mock_reviewer.review_diff = AsyncMock(return_value={
        "summary": "This is a summary.",
        "comments": [{"path": "a.py", "line": 5, "comment": "use double quotes"}]
    })
    mock_llm_reviewer_cls.return_value = mock_reviewer
    
    # Mock CommentService
    formatted_comments = [{"path": "a.py", "line": 5, "side": "RIGHT", "body": "use double quotes"}]
    mock_comment_service.filter_and_format_comments.return_value = formatted_comments
    
    # 2. Run service function
    result = await run_review("owner/repo", 42, post_to_github=True)
    
    # 3. Assertions
    assert result["status"] == "success"
    assert result["pr"] == 42
    assert result["comments_posted"] == 1
    assert result["summary"] == "This is a summary."
    assert result["comments"] == formatted_comments
    
    mock_gh_client.get_pull_request.assert_called_once_with("owner/repo", 42)
    mock_gh_client.get_pull_request_files.assert_called_once_with("owner/repo", 42)
    mock_gh_client.post_review.assert_called_once_with(
        repo="owner/repo",
        pr_number=42,
        commit_id="abcdef12345",
        body="### 🤖 AI Code Review Summary\n\nThis is a summary.",
        comments=formatted_comments,
        event="COMMENT"
    )

@pytest.mark.asyncio
@patch("app.services.review_service.settings")
@patch("app.services.review_service.GitHubClient")
@patch("app.services.review_service.LLMReviewer")
@patch("app.services.review_service.CommentService")
async def test_run_review_success_no_comments(
    mock_comment_service,
    mock_llm_reviewer_cls,
    mock_github_client_cls,
    mock_settings
):
    # 1. Setup mocks
    mock_settings.github_token = "fake-github-token"
    mock_settings.llm_provider = "openai"
    mock_settings.openai_api_key = "fake-openai-key"
    
    # Mock GitHubClient
    mock_gh_client = MagicMock()
    mock_gh_client.get_pull_request = AsyncMock(return_value={"head": {"sha": "abcdef12345"}})
    mock_gh_client.get_pull_request_files = AsyncMock(return_value=[{"filename": "a.py"}])
    mock_gh_client.post_review = AsyncMock()
    mock_github_client_cls.return_value = mock_gh_client
    
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
    result = await run_review("owner/repo", 42, post_to_github=True)
    
    # 3. Assertions
    assert result["status"] == "success"
    assert result["comments_posted"] == 0
    
    expected_body = "### 🤖 AI Code Review Summary\n\nNo major issues found.\n\nNo specific inline issues found. Code quality looks great! 👍"
    mock_gh_client.post_review.assert_called_once_with(
        repo="owner/repo",
        pr_number=42,
        commit_id="abcdef12345",
        body=expected_body,
        comments=[],
        event="COMMENT"
    )

@pytest.mark.asyncio
@patch("app.services.review_service.settings")
@patch("app.services.review_service.GitHubClient")
@patch("app.services.review_service.LLMReviewer")
@patch("app.services.review_service.CommentService")
async def test_run_review_no_post_to_github(
    mock_comment_service,
    mock_llm_reviewer_cls,
    mock_github_client_cls,
    mock_settings
):
    # 1. Setup mocks
    mock_settings.github_token = "fake-github-token"
    mock_settings.llm_provider = "anthropic"
    mock_settings.anthropic_api_key = "fake-anthropic-key"
    
    # Mock GitHubClient
    mock_gh_client = MagicMock()
    mock_gh_client.get_pull_request = AsyncMock(return_value={"head": {"sha": "abcdef12345"}})
    mock_gh_client.get_pull_request_files = AsyncMock(return_value=[{"filename": "a.py"}])
    mock_gh_client.post_review = AsyncMock()
    mock_github_client_cls.return_value = mock_gh_client
    
    # Mock LLMReviewer
    mock_reviewer = MagicMock()
    mock_reviewer.review_diff = AsyncMock(return_value={
        "summary": "This is a summary.",
        "comments": [{"path": "a.py", "line": 5, "comment": "use double quotes"}]
    })
    mock_llm_reviewer_cls.return_value = mock_reviewer
    
    # Mock CommentService
    formatted_comments = [{"path": "a.py", "line": 5, "side": "RIGHT", "body": "use double quotes"}]
    mock_comment_service.filter_and_format_comments.return_value = formatted_comments
    
    # 2. Run service function with post_to_github=False
    result = await run_review("owner/repo", 42, post_to_github=False)
    
    # 3. Assertions
    assert result["status"] == "success"
    assert result["comments_posted"] == 0  # since post_to_github is False, it shouldn't post review
    assert result["comments"] == formatted_comments
    
    # Verify post_review was NOT called
    mock_gh_client.post_review.assert_not_called()
