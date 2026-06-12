import re
from typing import List, Dict, Any

def parse_patch(patch: str) -> List[Dict[str, Any]]:
    """
    Parses a unified diff patch string.
    Returns a list of dicts for added/modified lines:
    [
        {
            "line_number": int,   # Line number in the new file
            "content": str        # Line content
        }
    ]
    """
    if not patch:
        return []
        
    added_lines = []
    lines = patch.split('\n')
    new_line_no = 0
    
    for line in lines:
        # Check for hunk header
        hunk_match = re.match(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', line)
        if hunk_match:
            new_line_no = int(hunk_match.group(1))
            continue
            
        if line.startswith('+') and not line.startswith('+++'):
            # This is an added line
            added_lines.append({
                "line_number": new_line_no,
                "content": line[1:]
            })
            new_line_no += 1
        elif line.startswith('-') and not line.startswith('---'):
            # This is a deleted line, doesn't increment the new line count in new file
            pass
        elif line.startswith(' '):
            # This is a context line, increment both
            new_line_no += 1
        # We ignore other metadata lines (like \ No newline at end of file)
        
    return added_lines


class PRDiffParser:
    @staticmethod
    def parse_files(files_payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parses the list of files returned by GitHub client.get_pull_request_files().
        Each file has 'filename', 'status', 'patch'.
        Returns a list of parsed file diff structures.
        """
        parsed_files = []
        for f in files_payload:
            filename = f.get("filename")
            status = f.get("status")
            patch = f.get("patch", "")
            
            # Skip if there's no patch content (e.g. binary or empty file)
            if not patch:
                continue
                
            added_lines = parse_patch(patch)
            parsed_files.append({
                "filename": filename,
                "status": status,
                "added_lines": added_lines,
                "patch": patch
            })
        return parsed_files
