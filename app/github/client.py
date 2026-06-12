import httpx
from typing import Dict, List, Any, Optional
from fastapi import HTTPException

class GitHubClient:
    def __init__(self, token: str):
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable or parameter is required.")
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_pull_request(self, repo: str, pr_number: int) -> Dict[str, Any]:
        """
        Fetch details of a specific pull request.
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Failed to fetch PR {pr_number} from GitHub: {response.text}"
                )
            return response.json()

    async def get_pull_request_files(self, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """
        Fetch the list of files in a pull request.
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/files"
        params = {"per_page": 100}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Failed to fetch files for PR {pr_number} from GitHub: {response.text}"
                )
            return response.json()

    async def post_review(
        self, 
        repo: str, 
        pr_number: int, 
        commit_id: str, 
        body: str, 
        comments: List[Dict[str, Any]], 
        event: str = "COMMENT"
    ) -> Dict[str, Any]:
        """
        Post a review on a pull request.
        comments should be a list of dictionaries with:
        {
            "path": "file_path",
            "line": line_number,
            "side": "RIGHT",
            "body": "comment_text"
        }
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/reviews"
        payload = {
            "commit_id": commit_id,
            "body": body,
            "event": event,
        }
        if comments:
            payload["comments"] = comments

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload)
            if response.status_code not in (200, 201):
                # If there's an error, try to print/return helpful info
                raise ValueError(f"Failed to post review: {response.text}")
            return response.json()
