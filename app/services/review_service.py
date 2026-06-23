import os
import logging
from app.config import settings
from app.github.client import GitHubClient
from app.github.parser import PRDiffParser
from app.llm.reviewer import LLMReviewer
from app.services.comment_service import CommentService

logger = logging.getLogger("review_service")

async def run_review(repo: str, pr_number: int, post_to_github: bool = True) -> dict:
    """
    Coordinates the end-to-end PR review pipeline:
    1. Fetches PR info and modified files from GitHub.
    2. Parses diff hunks to map code additions to new line numbers.
    3. Triggers the LLM reviewer.
    4. Validates and formats inline feedback.
    5. Submits comments and summary review back to GitHub.
    """
    # 1. Load configurations
    gh_token = settings.github_token
    if not gh_token:
        raise ValueError("GITHUB_TOKEN config setting is missing.")
        
    gh_client = GitHubClient(token=gh_token)
    
    provider = settings.llm_provider
    if provider == "openai":
        api_key = settings.openai_api_key
    elif provider == "anthropic":
        api_key = settings.anthropic_api_key
    else:  # mock or other providers
        api_key = "mock-key"
        
    reviewer = LLMReviewer(provider=provider, api_key=api_key)

    # 2. Fetch PR metadata to find the head commit SHA
    pr_metadata = await gh_client.get_pull_request(repo, pr_number)
    commit_id = pr_metadata["head"]["sha"]

    # 3. Fetch file diff details and parse additions
    files_payload = await gh_client.get_pull_request_files(repo, pr_number)
    parsed_files = PRDiffParser.parse_files(files_payload)

    # 4. Generate structured LLM feedback
    review_result = await reviewer.review_diff(parsed_files)
    summary = review_result.get("summary", "")
    raw_comments = review_result.get("comments", [])

    # 5. Formulate and validate inline review comments
    formatted_comments = CommentService.filter_and_format_comments(raw_comments, parsed_files)

    # 6. Post comments back to GitHub as a single Pull Request Review
    comments_posted = 0
    if post_to_github:
        review_body = f"### 🤖 AI Code Review Summary\n\n{summary}"
        if not formatted_comments:
            review_body += "\n\nNo specific inline issues found. Code quality looks great! 👍"
            
        await gh_client.post_review(
            repo=repo,
            pr_number=pr_number,
            commit_id=commit_id,
            body=review_body,
            comments=formatted_comments,
            event="COMMENT"
        )
        comments_posted = len(formatted_comments)

    return {
        "status": "success",
        "pr": pr_number,
        "comments_posted": comments_posted,
        "summary": summary,
        "comments": formatted_comments
    }
