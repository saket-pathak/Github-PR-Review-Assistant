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
