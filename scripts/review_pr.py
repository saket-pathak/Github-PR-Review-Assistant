import argparse
import asyncio
import re
import sys
from dotenv import load_dotenv

# Pre-load environment configurations
load_dotenv()

from app.config import settings
from app.services.review_service import run_review

def parse_pr_url(url: str) -> tuple[str, int]:
    """
    Parses a GitHub pull request URL to extract repo identifier and PR number.
    Example: https://github.com/owner/repo/pull/42 -> ('owner/repo', 42)
    """
    pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid GitHub PR URL. Must be format: https://github.com/owner/repo/pull/42")
    owner, repo, pr_number = match.groups()
    return f"{owner}/{repo}", int(pr_number)

async def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR from terminal.")
    parser.add_argument("pr_url", help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/42)")
    parser.add_argument("--post", action="store_true", help="Post reviews as comments on GitHub")
    args = parser.parse_args()

    try:
        repo, pr_number = parse_pr_url(args.pr_url)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Starting AI PR review for {repo} PR #{pr_number}...")
    print(f"LLM Provider: {settings.llm_provider}")
    print(f"Post to GitHub: {args.post}")
    print("=" * 60)

    try:
        result = await run_review(repo, pr_number, post_to_github=args.post)
        
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
