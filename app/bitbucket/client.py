import httpx
from typing import Dict, List, Any
from fastapi import HTTPException

class BitbucketClient:
    def __init__(self, token: str, username: str = "", base_url: str = "https://api.bitbucket.org/2.0"):
        if not token:
            raise ValueError("Bitbucket token or app password is required.")
        self.token = token
        self.username = username
        self.base_url = base_url.rstrip("/")
        
        # Configure authorization
        self.headers = {
            "Accept": "application/json",
        }
        self.auth = None
        
        if username:
            # Use HTTP Basic Auth for App Passwords
            self.auth = (username, token)
        else:
            # Use Bearer Token auth for OAuth2
            self.headers["Authorization"] = f"Bearer {token}"

    async def get_pull_request(self, repo: str, pr_id: int) -> Dict[str, Any]:
        """
        Fetch pull request metadata details.
        """
        url = f"{self.base_url}/repositories/{repo}/pullrequests/{pr_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, auth=self.auth)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch Bitbucket PR {pr_id}: {response.text}"
                )
            return response.json()

    async def get_pull_request_diff(self, repo: str, pr_id: int) -> str:
        """
        Fetch the raw unified diff for the pull request.
        """
        url = f"{self.base_url}/repositories/{repo}/pullrequests/{pr_id}/diff"
        async with httpx.AsyncClient() as client:
            # Note: Bitbucket diff returns plain text
            response = await client.get(url, headers=self.headers, auth=self.auth)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch Bitbucket PR {pr_id} diff: {response.text}"
                )
            return response.text

    async def post_comment(self, repo: str, pr_id: int, body: str) -> Dict[str, Any]:
        """
        Post a general comment to the pull request.
        """
        url = f"{self.base_url}/repositories/{repo}/pullrequests/{pr_id}/comments"
        payload = {
            "content": {
                "raw": body
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, auth=self.auth, json=payload)
            if response.status_code not in (200, 201):
                raise ValueError(f"Failed to post Bitbucket comment: {response.text}")
            return response.json()

    async def post_inline_comment(self, repo: str, pr_id: int, filename: str, line: int, body: str) -> Dict[str, Any]:
        """
        Post an inline comment on a specific line of a file in the pull request.
        """
        url = f"{self.base_url}/repositories/{repo}/pullrequests/{pr_id}/comments"
        payload = {
            "content": {
                "raw": body
            },
            "inline": {
                "path": filename,
                "to": line
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, auth=self.auth, json=payload)
            if response.status_code not in (200, 201):
                raise ValueError(f"Failed to post Bitbucket inline comment: {response.text}")
            return response.json()
