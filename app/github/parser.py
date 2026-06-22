import re
from typing import List, Dict, Any

def parse_patch(patch: str) -> List[Dict[str, Any]]:
    """
    Parses a unified diff patch string.
    Returns a list of dicts representing added/modified lines in the new file version:
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
        hunk_match = re.match(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', line)
        if hunk_match:
            new_line_no = int(hunk_match.group(1))
            continue
            
        if line.startswith('+') and not line.startswith('+++'):
            added_lines.append({
                "line_number": new_line_no,
                "content": line[1:]
            })
            new_line_no += 1
        elif line.startswith('-') and not line.startswith('---'):
            pass
        elif line.startswith(' '):
            new_line_no += 1
            
    return added_lines


class PRDiffParser:
    @staticmethod
    def parse_files(files_payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parses list of files from GitHub REST response.
        Extracts filename, status, and added lines from the patch.
        """
        parsed_files = []
        for f in files_payload:
            filename = f.get("filename")
            status = f.get("status")
            patch = f.get("patch", "")
            
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
