import os
import openai

REVIEWER_PROMPT = """
You are a test reviewer agent. You receive a JSON input with:
- `passed` (boolean): whether pytest reported all tests passing.
- `output` (string): the raw pytest stdout/stderr.

If `passed` is true, return exactly:
{"status": "ALL_TESTS_PASS"}

If `passed` is false, return exactly a JSON object with three keys:
{
  "status": "FAILED",
  "analysis_markdown": "...",
  "fix_markdown": "..."
}

Requirements for the failed case:
1. **analysis_markdown**: a concise Markdown explanation of each test failure—what assertion failed, why it failed, and which part of the code under test is at fault.
2. **fix_markdown**: a Markdown-formatted code block containing a **complete**, ready-to-paste replacement function (or functions) that, if substituted for the original, would make all tests pass. Include language fences (```python) and preserve function signature.

Do not include any additional keys or text outside of the specified JSON object. Be as concise as possible.
"""

def strip_code_blocks(text):
    text = text.strip()
    if text.startswith("````"):
        text = text.split("````", 1)[1].strip()
    if text.startswith("```python"):
        text = text[len("```python"):].strip()
    elif text.startswith("```py"):
        text = text[len("```py"):].strip()
    elif text.startswith("```"):
        text = text[len("```"):].strip()
    if text.endswith("```"):
        text = text[:text.rfind("```")].strip()
    return text


class ReviewerAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def review(self, output, code=None, test_code=None, conversation=None, model="gpt-4o"):
        user_prompt = f"""
Pytest output (failed):
{output}

User's code under test:
{code or ''}

Test code (pytest):
{test_code or ''}

Conversation history:
{conversation or ''}
"""
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": REVIEWER_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        review_result = resp.choices[0].message["content"]
        
        # Parse the JSON response from OpenAI and return the parsed object
        try:
            import json
            result = json.loads(review_result)
            return result
        except json.JSONDecodeError:
            # If parsing fails, return a fallback structure
            return {
                "status": "FAILED",
                "analysis_markdown": review_result,
                "fix_markdown": "Unable to parse fix suggestion."
            }
