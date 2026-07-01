from app.bitbucket.parser import BitbucketDiffParser

def test_bitbucket_diff_parser_empty():
    assert BitbucketDiffParser.parse_pr_diff("") == []

def test_bitbucket_diff_parser_valid():
    diff_text = """diff --git a/app/config.py b/app/config.py
index 123456..789101 100644
--- a/app/config.py
+++ b/app/config.py
@@ -1,5 +1,6 @@
 import os
-old_line = "value"
+new_line = "value"
+added_line = "yes"
 
 def fn():
     pass
diff --git a/setup.py b/setup.py
new file mode 100644
index 000000..123456
--- /dev/null
+++ b/setup.py
@@ -0,0 +1 @@
+print("hello")
"""
    result = BitbucketDiffParser.parse_pr_diff(diff_text)
    assert len(result) == 2
    
    # Check config.py
    config_file = result[0]
    assert config_file["filename"] == "app/config.py"
    assert config_file["status"] == "modified"
    assert len(config_file["added_lines"]) == 2
    assert config_file["added_lines"][0] == {"line_number": 2, "content": "new_line = \"value\""}
    assert config_file["added_lines"][1] == {"line_number": 3, "content": "added_line = \"yes\""}
    
    # Check setup.py
    setup_file = result[1]
    assert setup_file["filename"] == "setup.py"
    assert setup_file["status"] == "added"
    assert len(setup_file["added_lines"]) == 1
    assert setup_file["added_lines"][0] == {"line_number": 1, "content": "print(\"hello\")"}
