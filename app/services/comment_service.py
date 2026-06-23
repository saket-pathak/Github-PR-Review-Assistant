from typing import List, Dict, Any

class CommentService:
    @staticmethod
    def filter_and_format_comments(
        raw_comments: List[Dict[str, Any]], 
        parsed_files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filters and formats inline review comments.
        Ensures comments only target lines that were actually added/modified 
        in this pull request to avoid posting errors to GitHub.
        """
        valid_comments = []
        
        # Build map of filenames to sets of valid added line numbers
        file_added_lines = {}
        for file in parsed_files:
            filename = file["filename"]
            added_lines_set = {line["line_number"] for line in file["added_lines"]}
            file_added_lines[filename] = added_lines_set

        for comment in raw_comments:
            path = comment.get("path")
            line = comment.get("line")
            body = comment.get("comment")

            if not path or line is None or not body:
                continue

            # Check if file exists in diff and the line was added/modified (RIGHT side)
            if path in file_added_lines and int(line) in file_added_lines[path]:
                valid_comments.append({
                    "path": path,
                    "line": int(line),
                    "side": "RIGHT",
                    "body": body
                })
                
        return valid_comments
