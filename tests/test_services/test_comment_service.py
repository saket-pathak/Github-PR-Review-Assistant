from app.services.comment_service import CommentService

def test_filter_and_format_comments_valid():
    parsed_files = [
        {
            "filename": "app/main.py",
            "added_lines": [
                {"line_number": 10, "content": "print('hello')"},
                {"line_number": 11, "content": "print('world')"}
            ]
        }
    ]
    raw_comments = [
        {
            "path": "app/main.py",
            "line": 10,
            "comment": "Use double quotes instead of single quotes."
        }
    ]
    
    result = CommentService.filter_and_format_comments(raw_comments, parsed_files)
    
    assert len(result) == 1
    assert result[0] == {
        "path": "app/main.py",
        "line": 10,
        "side": "RIGHT",
        "body": "Use double quotes instead of single quotes."
    }

def test_filter_and_format_comments_filters_unmodified_line():
    parsed_files = [
        {
            "filename": "app/main.py",
            "added_lines": [
                {"line_number": 10, "content": "print('hello')"}
            ]
        }
    ]
    # Comment targets line 9 which was not added/modified
    raw_comments = [
        {
            "path": "app/main.py",
            "line": 9,
            "comment": "Line 9 issue"
        }
    ]
    
    result = CommentService.filter_and_format_comments(raw_comments, parsed_files)
    assert len(result) == 0

def test_filter_and_format_comments_filters_untracked_file():
    parsed_files = [
        {
            "filename": "app/main.py",
            "added_lines": [
                {"line_number": 10, "content": "print('hello')"}
            ]
        }
    ]
    # Comment targets a completely different file
    raw_comments = [
        {
            "path": "app/utils.py",
            "line": 10,
            "comment": "Untracked file issue"
        }
    ]
    
    result = CommentService.filter_and_format_comments(raw_comments, parsed_files)
    assert len(result) == 0

def test_filter_and_format_comments_invalid_structure():
    parsed_files = [
        {
            "filename": "app/main.py",
            "added_lines": [
                {"line_number": 10, "content": "print('hello')"}
            ]
        }
    ]
    # Comments missing required fields
    raw_comments = [
        {"line": 10, "comment": "Missing path"},
        {"path": "app/main.py", "comment": "Missing line"},
        {"path": "app/main.py", "line": 10}  # Missing comment text
    ]
    
    result = CommentService.filter_and_format_comments(raw_comments, parsed_files)
    assert len(result) == 0
