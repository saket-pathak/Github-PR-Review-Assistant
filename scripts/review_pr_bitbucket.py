import argparse
import asyncio
import re
import sys
from dotenv import load_dotenv

# Pre-load environment configurations
load_dotenv()

from app.config import settings
from app.services.bitbucket_review_service import run_bitbucket_review

def parse_bitbucket_url(url: str) -> tuple[str, int]:
    """
    Parses a Bitbucket Cloud pull request URL to extract repo and PR ID.
    Example: https://bitbucket.org/workspace/repo/pull-requests/42 -> ('workspace/repo', 42)
    """
    pattern = r"https://bitbucket\.org/([^/]+)/([^/]+)/pull-requests/(\d+)"
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid Bitbucket PR URL. Must be format: https://bitbucket.org/workspace/repo/pull-requests/42")
    workspace, repo, pr_id = match.groups()
    return f"{workspace}/{repo}", int(pr_id)

async def main():
    parser = argparse.ArgumentParser(description="Review a Bitbucket PR from terminal.")
    parser.add_argument("pr_url", help="Bitbucket PR URL (e.g. https://bitbucket.org/workspace/repo/pull-requests/42)")
    parser.add_argument("--post", action="store_true", help="Post reviews as comments on Bitbucket")
    args = parser.parse_args()

    try:
        repo, pr_id = parse_bitbucket_url(args.pr_url)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Starting AI Bitbucket PR review for {repo} PR #{pr_id}...")
    print(f"LLM Provider: {settings.llm_provider}")
    print(f"Post to Bitbucket: {args.post}")
    print("=" * 60)

    try:
        result = await run_bitbucket_review(repo, pr_id, post_to_bitbucket=args.post)
        
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
