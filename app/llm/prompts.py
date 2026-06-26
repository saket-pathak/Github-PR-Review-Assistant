SYSTEM_INSTRUCTION = """You are a senior software engineer and code reviewer.
Your goal is to review the code changes in a pull request and provide constructive, high-quality review feedback.

Analyze the changes for:
1. Logical bugs, edge cases, and runtime safety issues.
2. Security vulnerabilities (e.g., credentials, injections, unsafe operations).
3. Performance issues or inefficiencies.
4. Code readability, styling, clean code principles, and refactoring opportunities.

You must respond ONLY with a JSON object. Do not include markdown code block syntax (like ```json ... ```) or any trailing text.
The JSON structure must match this:
{
  "summary": "A concise high-level summary of the PR, key concerns, and positive aspects (2-3 sentences).",
  "comments": [
    {
      "path": "path/to/file.py",
      "line": 42,
      "comment": "Constructive feedback on this specific line of code. Explain the problem and suggest a fix."
    }
  ]
}

CRITICAL RULES:
1. ONLY comment on the lines listed in the 'Added/Modified Lines' section of the prompt.
2. The 'line' attribute in your comments MUST correspond to one of the provided line numbers in the diff. Never comment on a line number that was not explicitly provided in the prompt.
3. If there are no issues, return an empty comments list: "comments": [].
4. Be polite, clear, and actionable in your suggestions.
"""

PYTHON_RULES = """
PYTHON-SPECIFIC RULES (STRICT):
- Check for PEP 8 compliance (naming, formatting structure).
- Watch out for common logical bugs like mutable default arguments (e.g., def fn(arg=[])).
- Avoid bare except clauses (always catch specific exceptions or use `except Exception:`).
- Ensure proper use of docstrings, type annotations, and clean code principles.
- Check for performance issues (e.g., unnecessary loops, slow string concatenations).
- Look for security issues (e.g., use of eval, unsafe deserialization, hardcoded credentials).
"""

CONFIG_RULES = """
CONFIG-SPECIFIC RULES (LENIENT):
- Focus on correctness, syntax, and structural errors.
- Check for security risks (e.g., exposed API keys, passwords, or private configuration details).
- Avoid style nitpicking or minor formatting preferences unless it leads to parsing issues.
"""

WEB_RULES = """
JS/TS/HTML/CSS-SPECIFIC RULES:
- Ensure correct asynchronous code handling (e.g., unhandled promises, missing awaits).
- Watch out for potential null/undefined reference errors (recommend optional chaining `?.`).
- Look for left-over debug statements like console.log or debugger.
- Ensure semantic HTML tags are used correctly for accessibility.
"""

SHELL_DOCKER_RULES = """
SHELL/DOCKER-SPECIFIC RULES:
- For Dockerfiles, verify image size optimizations (multi-stage builds, clean package caches) and security (avoid running as root, pin base images).
- For shell scripts, ensure variables are quoted to avoid splitting and wildcard expansion.
"""

def get_language_instructions(filenames: list[str]) -> str:
    """
    Returns language-specific instructions depending on the file types modified in the PR.
    """
    rules = []
    has_python = False
    has_config = False
    has_web = False
    has_shell = False
    
    for filename in filenames:
        name_lower = filename.lower()
        if name_lower.endswith(".py"):
            has_python = True
        elif any(name_lower.endswith(ext) for ext in [".json", ".yaml", ".yml", ".toml", ".ini", ".xml"]):
            has_config = True
        elif any(name_lower.endswith(ext) for ext in [".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".scss"]):
            has_web = True
        elif name_lower.endswith(".sh") or "dockerfile" in name_lower:
            has_shell = True
            
    if has_python:
        rules.append(PYTHON_RULES.strip())
    if has_config:
        rules.append(CONFIG_RULES.strip())
    if has_web:
        rules.append(WEB_RULES.strip())
    if has_shell:
        rules.append(SHELL_DOCKER_RULES.strip())
        
    if rules:
        return "\n\nADDITIONAL LANGUAGE-SPECIFIC GUIDELINES:\n" + "\n\n".join(rules)
    return ""

def get_system_instruction(filenames: list[str]) -> str:
    """
    Constructs the system instruction dynamically, combining core instructions with language-specific rules.
    """
    lang_rules = get_language_instructions(filenames)
    if lang_rules:
        return SYSTEM_INSTRUCTION + lang_rules
    return SYSTEM_INSTRUCTION

def format_review_prompt(parsed_files: list) -> str:
    """
    Formats the diff changes into a structured prompt for the LLM, 
    detailing the file name, status, and specific added/modified line numbers.
    """
    prompt = "Below are the pull request changes for your review. Please review only the added/modified lines:\n\n"
    for file in parsed_files:
        prompt += f"File: {file['filename']}\n"
        prompt += f"Status: {file['status']}\n"
        prompt += "Added/Modified Lines:\n"
        if not file['added_lines']:
            prompt += "(No lines added or modified in this file)\n"
        else:
            for line in file['added_lines']:
                prompt += f"Line {line['line_number']}: {line['content']}\n"
        prompt += "---------------------------------------\n\n"
    
    prompt += "Provide the review comments using the exact JSON format specified in system instructions."
    return prompt

