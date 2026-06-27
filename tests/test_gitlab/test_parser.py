from app.gitlab.parser import MRDiffParser

def test_mr_diff_parser_parse_changes_empty():
    assert MRDiffParser.parse_changes({"changes": []}) == []
    assert MRDiffParser.parse_changes({}) == []

def test_mr_diff_parser_parse_changes_valid():
    changes_payload = {
        "changes": [
            {
                "new_path": "app/main.py",
                "old_path": "app/main.py",
                "new_file": False,
                "renamed_file": False,
                "deleted_file": False,
                "diff": "@@ -1,2 +1,3 @@\n context\n+added line\n"
            },
            {
                "new_path": "app/new_file.py",
                "old_path": "app/new_file.py",
                "new_file": True,
                "renamed_file": False,
                "deleted_file": False,
                "diff": "@@ -0,0 +1 @@\n+print('hello')\n"
            },
            {
                "new_path": "app/old_file.py",
                "old_path": "app/old_file.py",
                "new_file": False,
                "renamed_file": False,
                "deleted_file": True,
                "diff": "@@ -1 +0,0 @@\n-print('bye')\n"
            },
            {
                "new_path": "app/renamed.py",
                "old_path": "app/original.py",
                "new_file": False,
                "renamed_file": True,
                "deleted_file": False,
                "diff": "@@ -1 +1 @@\n-x\n+y\n"
            }
        ]
    }
    
    parsed = MRDiffParser.parse_changes(changes_payload)
    
    # We should have 3 files parsed (deleted file is skipped)
    assert len(parsed) == 3
    
    # Assert main.py
    assert parsed[0]["filename"] == "app/main.py"
    assert parsed[0]["status"] == "modified"
    assert parsed[0]["added_lines"] == [{"line_number": 2, "content": "added line"}]
    
    # Assert new_file.py
    assert parsed[1]["filename"] == "app/new_file.py"
    assert parsed[1]["status"] == "added"
    assert parsed[1]["added_lines"] == [{"line_number": 1, "content": "print('hello')"}]
    
    # Assert renamed.py
    assert parsed[2]["filename"] == "app/renamed.py"
    assert parsed[2]["status"] == "renamed"
    assert parsed[2]["added_lines"] == [{"line_number": 1, "content": "y"}]
