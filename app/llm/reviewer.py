import json
from typing import List, Dict, Any
from app.llm.client import LLMClient
from app.llm.prompts import get_system_instruction, format_review_prompt

class LLMReviewer:
    def __init__(self, provider: str, api_key: str):
        self.client = LLMClient(provider=provider, api_key=api_key)

    async def review_diff(self, parsed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Formats parsed files, calls the LLM, and sanitizes/parses the JSON response.
        """
        # Filter files to review (exclude binaries, metadata, lockfiles, etc.)
        reviewable_files = []
        for f in parsed_files:
            filename = f.get("filename", "")
            # Skip common lock/dependency and asset file formats
            if any(filename.endswith(ext) for ext in [
                ".lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
                ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf"
            ]):
                continue
            reviewable_files.append(f)

        if not reviewable_files:
            return {
                "summary": "No reviewable code changes found in this PR.",
                "comments": []
            }

        prompt = format_review_prompt(reviewable_files)
        filenames = [f.get("filename", "") for f in reviewable_files]
        system_instruction = get_system_instruction(filenames)
        raw_response = await self.client.get_review(
            prompt=prompt,
            system_instruction=system_instruction
        )
        
        # Sanitize LLM response (in case of markdown code block encapsulation)
        cleaned_json = raw_response.strip()
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json[7:]
        if cleaned_json.startswith("```"):
            cleaned_json = cleaned_json[3:]
        if cleaned_json.endswith("```"):
            cleaned_json = cleaned_json[:-3]
        cleaned_json = cleaned_json.strip()

        try:
            review_data = json.loads(cleaned_json)
            return {
                "summary": review_data.get("summary", ""),
                "comments": review_data.get("comments", [])
            }
        except json.JSONDecodeError as e:
            return {
                "summary": f"Failed to parse LLM review output as JSON: {str(e)}",
                "comments": [],
                "raw_response": raw_response
            }

