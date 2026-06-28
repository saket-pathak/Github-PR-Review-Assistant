import hashlib
import logging
from app.config import settings
from app.gitlab.client import GitLabClient
from app.gitlab.parser import MRDiffParser
from app.llm.reviewer import LLMReviewer
from app.services.comment_service import CommentService
from app.services.cache_service import ReviewCache

logger = logging.getLogger("gitlab_review_service")

async def run_gitlab_review(project_id: str, mr_iid: int, post_to_gitlab: bool = True) -> dict:
    """
    Coordinates the end-to-end GitLab MR review pipeline:
    1. Fetches MR details and modified files/changes from GitLab.
    2. Parses diff to map code additions.
    3. Uses ReviewCache to skip already reviewed unchanged files.
    4. Triggers the LLM reviewer for non-cached files.
    5. Validates, formats, and caches inline feedback.
    6. Submits discussions (inline comments) and general note (summary) back to GitLab.
    """
    # 1. Load configurations
    gl_token = settings.gitlab_token
    if not gl_token:
        raise ValueError("GITLAB_TOKEN config setting is missing.")
        
    gl_client = GitLabClient(token=gl_token, base_url=settings.gitlab_api_url)
    
    provider = settings.llm_provider
    if provider == "openai":
        api_key = settings.openai_api_key
    elif provider == "anthropic":
        api_key = settings.anthropic_api_key
    else:  # mock or other providers
        api_key = "mock-key"
        
    reviewer = LLMReviewer(provider=provider, api_key=api_key)
    cache = ReviewCache()

    # 2. Fetch MR metadata to find diff refs
    mr_metadata = await gl_client.get_merge_request(project_id, mr_iid)
    diff_refs = mr_metadata.get("diff_refs", {})
    base_sha = diff_refs.get("base_sha")
    start_sha = diff_refs.get("start_sha")
    head_sha = diff_refs.get("head_sha")

    if not (base_sha and start_sha and head_sha):
        raise ValueError("Could not extract diff_refs (base_sha, start_sha, head_sha) from GitLab MR.")

    # 3. Fetch file changes
    changes_payload = await gl_client.get_merge_request_changes(project_id, mr_iid)
    parsed_files = MRDiffParser.parse_changes(changes_payload)

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
        summary = "All changed files in this merge request have been previously reviewed and remain unchanged. Re-using cached review comments."
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
            summary += "\n\n*(Note: Re-used cached review comments for unchanged files in this MR.)*"

    # 7. Post review back to GitLab
    comments_posted = 0
    if post_to_gitlab:
        review_body = f"### 🤖 AI Code Review Summary\n\n{summary}"
        if not all_comments:
            review_body += "\n\nNo specific inline issues found. Code quality looks great! 👍"
            
        # Post general summary comment
        await gl_client.post_comment(project_id, mr_iid, review_body)
        
        # Post inline discussion threads
        for comment in all_comments:
            try:
                await gl_client.post_discussion(
                    project_id=project_id,
                    mr_iid=mr_iid,
                    base_sha=base_sha,
                    start_sha=start_sha,
                    head_sha=head_sha,
                    path=comment["path"],
                    line=comment["line"],
                    body=comment["body"]
                )
            except Exception as e:
                logger.error(f"Failed to post GitLab discussion on {comment['path']}:{comment['line']}: {e}")
                
        comments_posted = len(all_comments)

    return {
        "status": "success",
        "mr": mr_iid,
        "comments_posted": comments_posted,
        "summary": summary,
        "comments": all_comments
    }
