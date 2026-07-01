import hashlib
import logging
from app.config import settings
from app.bitbucket.client import BitbucketClient
from app.bitbucket.parser import BitbucketDiffParser
from app.llm.reviewer import LLMReviewer
from app.services.comment_service import CommentService
from app.services.cache_service import ReviewCache

logger = logging.getLogger("bitbucket_review_service")

async def run_bitbucket_review(repo: str, pr_id: int, post_to_bitbucket: bool = True) -> dict:
    """
    Coordinates the end-to-end Bitbucket PR review pipeline:
    1. Fetches PR raw diff from Bitbucket.
    2. Parses diff to map code additions.
    3. Uses ReviewCache to skip already reviewed unchanged files.
    4. Triggers the LLM reviewer for non-cached files.
    5. Validates, formats, and caches inline feedback.
    6. Submits inline comments and general summary comment back to Bitbucket.
    """
    # 1. Load configurations
    bb_token = settings.bitbucket_token
    bb_username = settings.bitbucket_username
    if not bb_token:
        raise ValueError("BITBUCKET_TOKEN config setting is missing.")
        
    bb_client = BitbucketClient(
        token=bb_token,
        username=bb_username,
        base_url=settings.bitbucket_api_url
    )
    
    provider = settings.llm_provider
    if provider == "openai":
        api_key = settings.openai_api_key
    elif provider == "anthropic":
        api_key = settings.anthropic_api_key
    else:  # mock or other providers
        api_key = "mock-key"
        
    reviewer = LLMReviewer(provider=provider, api_key=api_key)
    cache = ReviewCache()

    # 2. Fetch PR raw diff
    diff_text = await bb_client.get_pull_request_diff(repo, pr_id)
    
    # 3. Parse diff
    parsed_files = BitbucketDiffParser.parse_pr_diff(diff_text)

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

    # 7. Post review back to Bitbucket
    comments_posted = 0
    if post_to_bitbucket:
        review_body = f"### 🤖 AI Code Review Summary\n\n{summary}"
        if not all_comments:
            review_body += "\n\nNo specific inline issues found. Code quality looks great! 👍"
            
        # Post general summary comment
        await bb_client.post_comment(repo, pr_id, review_body)
        
        # Post inline comments
        for comment in all_comments:
            try:
                await bb_client.post_inline_comment(
                    repo=repo,
                    pr_id=pr_id,
                    filename=comment["path"],
                    line=comment["line"],
                    body=comment["body"]
                )
            except Exception as e:
                logger.error(f"Failed to post Bitbucket comment on {comment['path']}:{comment['line']}: {e}")
                
        comments_posted = len(all_comments)

    return {
        "status": "success",
        "pr": pr_id,
        "comments_posted": comments_posted,
        "summary": summary,
        "comments": all_comments
    }
