import os
from openai import OpenAI

REVIEWER_PROMPT = """
You are an code reviewer and debugger. You receive pytest output and analyze test failures to provide practical fixes.

CRITICAL: You must respond with ONLY valid JSON, no additional text before or after.

If all tests passed, return exactly:
{"status": "ALL_TESTS_PASS"}

If tests failed, analyze the root cause and provide a working fix. Return exactly this JSON structure:
{
  "status": "FAILED",
  "issues": [
    {
      "test_name": "name_of_failing_test",
      "error_type": "AssertionError|TypeError|ValueError|etc",
      "description": "Clear explanation of what went wrong",
      "expected": "what was expected",
      "actual": "what actually happened", 
      "cause": "root cause in the original code"
    }
  ],
  "summary": "Concise summary of the main problems",
  "fixed_code": "Complete corrected function code that will make the tests pass"
}

Requirements for fixed_code:
- Must be complete, runnable code with all imports and function signatures
- Should fix the actual logic errors, not just make tests pass superficially
- Include proper type hints and docstrings from original code
- Focus on the most likely and practical fixes
- Ensure the fix addresses the root cause, not just symptoms

Example for a function that returns too few elements:
{
  "status": "FAILED", 
  "issues": [{"test_name": "test_function", "error_type": "AssertionError", "description": "Function returns fewer elements than expected", "expected": "3 elements", "actual": "2 elements", "cause": "Off-by-one error in loop range"}],
  "summary": "Function has off-by-one error in loop calculation",
  "fixed_code": "def function(data, window): # Complete working function here"
}
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
        self.client = OpenAI(api_key=self.api_key)

    def review(self, output, code=None, test_code=None, conversation=None, model="gpt-4o-2024-08-06"):
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
        resp = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": REVIEWER_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        review_result = resp.choices[0].message.content
        print(f"[REVIEWER] Raw response: {review_result}")
        
        try:
            import json
            
            
            cleaned_result = review_result.strip()
            
           
            if cleaned_result.startswith("```json"):
                cleaned_result = cleaned_result[7:].strip()
            elif cleaned_result.startswith("```"):
                cleaned_result = cleaned_result[3:].strip()
            
            if cleaned_result.endswith("```"):
                cleaned_result = cleaned_result[:-3].strip()
            
            result = json.loads(cleaned_result)
            print(f"[REVIEWER] Parsed result: {result}")
            return result
            
        except json.JSONDecodeError as e:
            print(f"[REVIEWER] JSON Parse error: {e}")
            print(f"[REVIEWER] Raw content was: {review_result}")
            
            # Generic fallback when JSON parsing fails
            return {
                "status": "FAILED",
                "issues": [{"test_name": "unknown", "error_type": "ParseError", "description": "Failed to parse test results", "expected": "", "actual": "", "cause": "Unable to analyze output"}],
                "summary": "Unable to parse test analysis",
                "fixed_code": "Unable to generate fix suggestion."
            }
