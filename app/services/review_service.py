import os
import logging
import hashlib
from app.config import settings
from app.github.client import GitHubClient
from app.github.parser import PRDiffParser
from app.llm.reviewer import LLMReviewer
from app.services.comment_service import CommentService
from app.services.cache_service import ReviewCache

logger = logging.getLogger("review_service")

async def run_review(repo: str, pr_number: int, post_to_github: bool = True) -> dict:
    """
    Coordinates the end-to-end PR review pipeline:
    1. Fetches PR info and modified files from GitHub.
    2. Parses diff hunks to map code additions to new line numbers.
    3. Uses ReviewCache to skip already reviewed unchanged files.
    4. Triggers the LLM reviewer for non-cached files.
    5. Validates, formats, and caches inline feedback.
    6. Submits comments and summary review back to GitHub.
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
    cache = ReviewCache()

    # 2. Fetch PR metadata to find the head commit SHA
    pr_metadata = await gh_client.get_pull_request(repo, pr_number)
    commit_id = pr_metadata["head"]["sha"]

    # 3. Fetch file diff details and parse additions
    files_payload = await gh_client.get_pull_request_files(repo, pr_number)
    parsed_files = PRDiffParser.parse_files(files_payload)

    # 4. Check cache and partition files
    all_comments = []
    files_to_review = []
    file_hashes = {}

    for file in parsed_files:
        filename = file["filename"]
        patch = file.get("patch", "")
        # Compute SHA256 of filename + patch as unique diff cache key
        diff_content = f"{filename}:{patch}"
        diff_hash = hashlib.sha256(diff_content.encode("utf-8")).hexdigest()
        
        cached_comments = cache.get_comments(diff_hash)
        if cached_comments is not None:
            all_comments.extend(cached_comments)
        else:
            files_to_review.append(file)
            file_hashes[filename] = diff_hash

    # 5. Generate structured LLM feedback for non-cached files
    if not files_to_review:
        summary = "All changed files in this pull request have been previously reviewed and remain unchanged. Re-using cached review comments."
    else:
        review_result = await reviewer.review_diff(files_to_review)
        summary = review_result.get("summary", "")
        raw_comments = review_result.get("comments", [])

        # 6. Formulate and validate inline review comments
        new_formatted_comments = CommentService.filter_and_format_comments(raw_comments, files_to_review)
        all_comments.extend(new_formatted_comments)

        # Group new comments by file path to cache them individually
        comments_by_file = {filename: [] for filename in file_hashes}
        for comment in new_formatted_comments:
            path = comment.get("path")
            if path in comments_by_file:
                comments_by_file[path].append(comment)

        # Store results in cache
        for filename, diff_hash in file_hashes.items():
            cache.set_comments(diff_hash, comments_by_file[filename])

        # Append cache note if some files were cached
        if len(parsed_files) > len(files_to_review):
            summary += "\n\n*(Note: Re-used cached review comments for unchanged files in this PR.)*"

    # 7. Post comments back to GitHub as a single Pull Request Review
    comments_posted = 0
    if post_to_github:
        review_body = f"### 🤖 AI Code Review Summary\n\n{summary}"
        if not all_comments:
            review_body += "\n\nNo specific inline issues found. Code quality looks great! 👍"
            
        await gh_client.post_review(
            repo=repo,
            pr_number=pr_number,
            commit_id=commit_id,
            body=review_body,
            comments=all_comments,
            event="COMMENT"
        )
        comments_posted = len(all_comments)

    return {
        "status": "success",
        "pr": pr_number,
        "comments_posted": comments_posted,
        "summary": summary,
        "comments": all_comments
    }

