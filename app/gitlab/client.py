import httpx
import urllib.parse
from typing import Dict, List, Any
from fastapi import HTTPException

class GitLabClient:
    def __init__(self, token: str, base_url: str = "https://gitlab.com/api/v4"):
        if not token:
            raise ValueError("GITLAB_TOKEN is required.")
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "PRIVATE-TOKEN": token,
            "Accept": "application/json",
        }

    def _encode_project_id(self, project_id: str) -> str:
        """
        URL-encodes project path if it contains slashes, otherwise returns project ID.
        """
        # If it's an integer or string of integer, return as is
        if isinstance(project_id, int) or project_id.isdigit():
            return str(project_id)
        return urllib.parse.quote(project_id, safe="")

    async def get_merge_request(self, project_id: str, mr_iid: int) -> Dict[str, Any]:
        """
        Fetch merge request details (metadata, commits, SHAs).
        """
        encoded_project_id = self._encode_project_id(project_id)
        url = f"{self.base_url}/projects/{encoded_project_id}/merge_requests/{mr_iid}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch GitLab MR {mr_iid}: {response.text}"
                )
            return response.json()

    async def get_merge_request_changes(self, project_id: str, mr_iid: int) -> Dict[str, Any]:
        """
        Fetch files and diffs changed in a merge request.
        """
        encoded_project_id = self._encode_project_id(project_id)
        url = f"{self.base_url}/projects/{encoded_project_id}/merge_requests/{mr_iid}/changes"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch GitLab MR {mr_iid} changes: {response.text}"
                )
            return response.json()

    async def post_comment(self, project_id: str, mr_iid: int, body: str) -> Dict[str, Any]:
        """
        Post a general comment (note) to the merge request.
        """
        encoded_project_id = self._encode_project_id(project_id)
        url = f"{self.base_url}/projects/{encoded_project_id}/merge_requests/{mr_iid}/notes"
        payload = {"body": body}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload)
            if response.status_code not in (200, 201):
                raise ValueError(f"Failed to post GitLab comment: {response.text}")
            return response.json()

    async def post_discussion(
        self,
        project_id: str,
        mr_iid: int,
        base_sha: str,
        start_sha: str,
        head_sha: str,
        path: str,
        line: int,
        body: str
    ) -> Dict[str, Any]:
        """
        Post an inline review comment as a new discussion thread.
        """
        encoded_project_id = self._encode_project_id(project_id)
        url = f"{self.base_url}/projects/{encoded_project_id}/merge_requests/{mr_iid}/discussions"
        payload = {
            "body": body,
            "position": {
                "base_sha": base_sha,
                "start_sha": start_sha,
                "head_sha": head_sha,
                "position_type": "text",
                "new_path": path,
                "new_line": line
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload)
            if response.status_code not in (200, 201):
                raise ValueError(f"Failed to post GitLab inline discussion: {response.text}")
            return response.json()
