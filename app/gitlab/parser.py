from typing import List, Dict, Any
from app.github.parser import parse_patch

class MRDiffParser:
    @staticmethod
    def parse_changes(changes_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses changes from GitLab Merge Request changes API response.
        Extracts filename, status, and added lines from the diff.
        """
        parsed_files = []
        changes = changes_payload.get("changes", [])
        
        for change in changes:
            # Skip deleted files as we don't review deleted content
            if change.get("deleted_file"):
                continue
                
            filename = change.get("new_path") or change.get("old_path")
            if not filename:
                continue
                
            # Determine status equivalent to GitHub's file statuses
            if change.get("new_file"):
                status = "added"
            elif change.get("renamed_file"):
                status = "renamed"
            else:
                status = "modified"
                
            diff = change.get("diff", "")
            if not diff:
                continue
                
            added_lines = parse_patch(diff)
            parsed_files.append({
                "filename": filename,
                "status": status,
                "added_lines": added_lines,
                "patch": diff
            })
            
        return parsed_files
