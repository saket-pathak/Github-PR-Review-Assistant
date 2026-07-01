import re
from typing import List, Dict, Any
from app.github.parser import parse_patch

class BitbucketDiffParser:
    @staticmethod
    def parse_pr_diff(diff_text: str) -> List[Dict[str, Any]]:
        """
        Parses a complete multi-file unified diff text into structured file changes.
        """
        if not diff_text:
            return []
            
        # Split diff by "diff --git "
        file_diffs = diff_text.split("diff --git ")
        parsed_files = []
        
        for file_diff in file_diffs:
            if not file_diff.strip():
                continue
                
            lines = file_diff.split("\n")
            header_line = lines[0]
            
            # Extract filenames. E.g. "a/app/config.py b/app/config.py"
            match = re.match(r"^a/(.*?) b/(.*?)$", header_line.strip())
            if not match:
                continue
                
            old_path, new_path = match.groups()
            
            # Determine status
            status = "modified"
            is_deleted = False
            for line in lines[1:10]:
                if line.startswith("new file mode"):
                    status = "added"
                elif line.startswith("deleted file mode"):
                    is_deleted = True
                    status = "deleted"
                    
            if is_deleted:
                continue
                
            # Reconstruct the patch/diff content for this file
            patch_content = "\n".join(lines[1:])
            
            added_lines = parse_patch(patch_content)
            parsed_files.append({
                "filename": new_path,
                "status": status,
                "added_lines": added_lines,
                "patch": patch_content
            })
            
        return parsed_files
