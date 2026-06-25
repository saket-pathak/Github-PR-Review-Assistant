import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.llm.reviewer import LLMReviewer

@pytest.mark.asyncio
async def test_reviewer_no_reviewable_files():
    # If all files are lockfiles or binary/asset files, review_diff should return early
    reviewer = LLMReviewer(provider="mock", api_key="fake-key")
    parsed_files = [
        {
            "filename": "package-lock.json",
            "status": "modified",
            "added_lines": [{"line_number": 1, "content": "..."}]
        },
        {
            "filename": "image.png",
            "status": "added",
            "added_lines": []
        }
    ]
    
    result = await reviewer.review_diff(parsed_files)
    assert result["summary"] == "No reviewable code changes found in this PR."
    assert result["comments"] == []

@pytest.mark.asyncio
@patch("app.llm.reviewer.LLMClient")
async def test_reviewer_success_clean_json(mock_client_cls):
    mock_client = MagicMock()
    mock_client.get_review = AsyncMock(return_value='{"summary": "Code looks good.", "comments": []}')
    mock_client_cls.return_value = mock_client

    reviewer = LLMReviewer(provider="mock", api_key="fake-key")
    parsed_files = [
        {
            "filename": "app/main.py",
            "status": "modified",
            "added_lines": [{"line_number": 1, "content": "print('hello')"}]
        }
    ]

    result = await reviewer.review_diff(parsed_files)
    assert result["summary"] == "Code looks good."
    assert result["comments"] == []
    mock_client.get_review.assert_called_once()

@pytest.mark.asyncio
@patch("app.llm.reviewer.LLMClient")
async def test_reviewer_success_markdown_json(mock_client_cls):
    mock_client = MagicMock()
    mock_client.get_review = AsyncMock(return_value='```json\n{"summary": "Clean code", "comments": [{"path": "a.py", "line": 1, "comment": "fix"}]}\n```')
    mock_client_cls.return_value = mock_client

    reviewer = LLMReviewer(provider="mock", api_key="fake-key")
    parsed_files = [
        {
            "filename": "a.py",
            "status": "modified",
            "added_lines": [{"line_number": 1, "content": "x = 1"}]
        }
    ]

    result = await reviewer.review_diff(parsed_files)
    assert result["summary"] == "Clean code"
    assert len(result["comments"]) == 1
    assert result["comments"][0]["path"] == "a.py"

@pytest.mark.asyncio
@patch("app.llm.reviewer.LLMClient")
async def test_reviewer_invalid_json(mock_client_cls):
    mock_client = MagicMock()
    mock_client.get_review = AsyncMock(return_value='invalid raw response')
    mock_client_cls.return_value = mock_client

    reviewer = LLMReviewer(provider="mock", api_key="fake-key")
    parsed_files = [
        {
            "filename": "a.py",
            "status": "modified",
            "added_lines": [{"line_number": 1, "content": "x = 1"}]
        }
    ]

    result = await reviewer.review_diff(parsed_files)
    assert "Failed to parse LLM review output as JSON" in result["summary"]
    assert result["comments"] == []
    assert result["raw_response"] == "invalid raw response"
