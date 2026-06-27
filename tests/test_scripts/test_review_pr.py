import pytest
import sys
from unittest.mock import AsyncMock, patch
from scripts.review_pr import parse_pr_url, main

def test_parse_pr_url_valid():
    repo, pr_number = parse_pr_url("https://github.com/owner/repo/pull/42")
    assert repo == "owner/repo"
    assert pr_number == 42

def test_parse_pr_url_invalid():
    with pytest.raises(ValueError, match="Invalid GitHub PR URL"):
        parse_pr_url("https://github.com/owner/repo")
    
    with pytest.raises(ValueError, match="Invalid GitHub PR URL"):
        parse_pr_url("https://gitlab.com/owner/repo/pull/42")

@pytest.mark.asyncio
@patch("scripts.review_pr.run_review", new_callable=AsyncMock)
async def test_main_success_no_comments(mock_run_review, capsys):
    mock_run_review.return_value = {
        "status": "success",
        "comments_posted": 0,
        "summary": "No changes needed",
        "comments": []
    }
    
    test_args = ["review_pr.py", "https://github.com/owner/repo/pull/42"]
    with patch.object(sys, "argv", test_args):
        await main()
        
    captured = capsys.readouterr()
    assert "Starting AI PR review for owner/repo PR #42..." in captured.out
    assert "Status: success" in captured.out
    assert "Comments Posted: 0" in captured.out
    assert "No specific inline concerns raised." in captured.out

@pytest.mark.asyncio
@patch("scripts.review_pr.run_review", new_callable=AsyncMock)
async def test_main_success_with_comments(mock_run_review, capsys):
    mock_run_review.return_value = {
        "status": "success",
        "comments_posted": 1,
        "summary": "Summary check",
        "comments": [
            {
                "path": "app/main.py",
                "line": 10,
                "body": "Fix variable name"
            }
        ]
    }
    
    test_args = ["review_pr.py", "https://github.com/owner/repo/pull/42", "--post"]
    with patch.object(sys, "argv", test_args):
        await main()
        
    captured = capsys.readouterr()
    assert "Starting AI PR review for owner/repo PR #42..." in captured.out
    assert "Post to GitHub: True" in captured.out
    assert "Status: success" in captured.out
    assert "Comments Posted: 1" in captured.out
    assert "1. File: app/main.py | Line: 10" in captured.out
    assert "Suggestion: Fix variable name" in captured.out

@pytest.mark.asyncio
async def test_main_url_parsing_error(capsys):
    test_args = ["review_pr.py", "https://github.com/invalid-url"]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            await main()
            
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Invalid GitHub PR URL" in captured.err

@pytest.mark.asyncio
@patch("scripts.review_pr.run_review", new_callable=AsyncMock)
async def test_main_execution_error(mock_run_review, capsys):
    mock_run_review.side_effect = Exception("API rate limit exceeded")
    
    test_args = ["review_pr.py", "https://github.com/owner/repo/pull/42"]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            await main()
            
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Review Execution Failed: API rate limit exceeded" in captured.err
