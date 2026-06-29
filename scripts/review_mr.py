import argparse
import asyncio
import re
import sys
from dotenv import load_dotenv

# Pre-load environment configurations
load_dotenv()

from app.config import settings
from app.services.gitlab_review_service import run_gitlab_review

def parse_mr_url(url: str) -> tuple[str, int]:
    """
    Parses a GitLab merge request URL to extract project path and MR IID.
    Example: https://gitlab.com/owner/repo/-/merge_requests/42 -> ('owner/repo', 42)
    """
    pattern = r"https://[^/]+/(.+)/-/merge_requests/(\d+)"
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid GitLab MR URL. Must be format: https://gitlab.com/owner/repo/-/merge_requests/42")
    project_path, mr_iid = match.groups()
    return project_path, int(mr_iid)

async def main():
    parser = argparse.ArgumentParser(description="Review a GitLab MR from terminal.")
    parser.add_argument("mr_url", help="GitLab MR URL (e.g. https://gitlab.com/owner/repo/-/merge_requests/42)")
    parser.add_argument("--post", action="store_true", help="Post reviews as comments on GitLab")
    args = parser.parse_args()

    try:
        project_path, mr_iid = parse_mr_url(args.mr_url)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Starting AI MR review for {project_path} MR #{mr_iid}...")
    print(f"LLM Provider: {settings.llm_provider}")
    print(f"Post to GitLab: {args.post}")
    print("=" * 60)

    try:
        result = await run_gitlab_review(project_path, mr_iid, post_to_gitlab=args.post)
        
        print("\n=== AI CODE REVIEW RESULTS ===")
        print(f"Status: {result.get('status')}")
        print(f"Comments Posted: {result.get('comments_posted')}\n")
        print("Summary:")
        print(result.get("summary"))
        print("-" * 60)
        
        comments = result.get("comments", [])
        if comments:
            print("\nSuggested Inline Comments:")
            for idx, c in enumerate(comments, 1):
                print(f"{idx}. File: {c['path']} | Line: {c['line']}")
                print(f"   Suggestion: {c['body']}\n")
        else:
            print("\nNo specific inline concerns raised.")
            
    except Exception as e:
        print(f"\nReview Execution Failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
