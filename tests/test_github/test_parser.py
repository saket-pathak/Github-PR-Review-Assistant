from app.github.parser import parse_patch, PRDiffParser

def test_parse_patch_empty():
    assert parse_patch("") == []
    assert parse_patch(None) == []

def test_parse_patch_valid():
    patch = (
        "@@ -1,4 +1,6 @@\n"
        " Some context line\n"
        "-removed line\n"
        "+added line 1\n"
        "+added line 2\n"
        " another context line\n"
        "@@ -10,3 +12,4 @@\n"
        " context line\n"
        "+added line 3\n"
    )
    result = parse_patch(patch)
    assert result == [
        {"line_number": 2, "content": "added line 1"},
        {"line_number": 3, "content": "added line 2"},
        {"line_number": 13, "content": "added line 3"},
    ]

def test_pr_diff_parser_parse_files():
    files_payload = [
        {
            "filename": "app/main.py",
            "status": "modified",
            "patch": "@@ -1,2 +1,3 @@\n context\n+added line\n"
        },
        {
            "filename": "app/utils.py",
            "status": "added",
            "patch": ""
        }
    ]
    parsed = PRDiffParser.parse_files(files_payload)
    assert len(parsed) == 1
    assert parsed[0]["filename"] == "app/main.py"
    assert parsed[0]["status"] == "modified"
    assert parsed[0]["added_lines"] == [{"line_number": 2, "content": "added line"}]
