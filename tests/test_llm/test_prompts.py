from app.llm.prompts import (
    format_review_prompt,
    SYSTEM_INSTRUCTION,
    get_language_instructions,
    get_system_instruction
)

def test_system_instruction_contains_key_elements():
    # Verify key requirements are in the system instruction text
    assert "JSON" in SYSTEM_INSTRUCTION
    assert "summary" in SYSTEM_INSTRUCTION
    assert "comments" in SYSTEM_INSTRUCTION
    assert "CRITICAL RULES" in SYSTEM_INSTRUCTION

def test_format_review_prompt_with_changes():
    parsed_files = [
        {
            "filename": "app/main.py",
            "status": "modified",
            "added_lines": [
                {"line_number": 10, "content": "def hello():"},
                {"line_number": 11, "content": "    print('world')"}
            ]
        }
    ]
    prompt = format_review_prompt(parsed_files)
    
    assert "File: app/main.py" in prompt
    assert "Status: modified" in prompt
    assert "Line 10: def hello():" in prompt
    assert "Line 11:     print('world')" in prompt
    assert "Provide the review comments using the exact JSON format" in prompt

def test_format_review_prompt_no_changes():
    parsed_files = [
        {
            "filename": "app/utils.py",
            "status": "added",
            "added_lines": []
        }
    ]
    prompt = format_review_prompt(parsed_files)
    
    assert "File: app/utils.py" in prompt
    assert "Status: added" in prompt
    assert "(No lines added or modified in this file)" in prompt

def test_get_language_instructions_python():
    instructions = get_language_instructions(["app/main.py", "app/utils.py"])
    assert "PYTHON-SPECIFIC RULES" in instructions
    assert "CONFIG-SPECIFIC RULES" not in instructions

def test_get_language_instructions_config():
    instructions = get_language_instructions(["docker-compose.yml", "package.json"])
    assert "CONFIG-SPECIFIC RULES" in instructions
    assert "PYTHON-SPECIFIC RULES" not in instructions

def test_get_language_instructions_mixed():
    instructions = get_language_instructions(["app/main.py", "docker-compose.yml"])
    assert "PYTHON-SPECIFIC RULES" in instructions
    assert "CONFIG-SPECIFIC RULES" in instructions

def test_get_language_instructions_other():
    instructions = get_language_instructions(["README.md", "LICENSE"])
    assert instructions == ""

def test_get_system_instruction_python():
    sys_inst = get_system_instruction(["app/main.py"])
    assert "PYTHON-SPECIFIC RULES" in sys_inst
    
    sys_inst_no_files = get_system_instruction([])
    assert sys_inst_no_files == SYSTEM_INSTRUCTION

