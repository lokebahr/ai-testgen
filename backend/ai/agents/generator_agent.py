import os
from openai import OpenAI

GENERATOR_PROMPT = (
    "Given the following code in {filename}:\n\n{code}\n\n"
    "And the following test plan:\n{test_plan}\n"
    "Write complete test code using correct imports for {filename}. Use pytest style. Output only the test code.\n\n"
    "CRITICAL REQUIREMENTS:\n"
    "- Code must be syntactically correct and compile without errors\n"
    "- All imports must be valid and available\n"
    "- Mock objects must be properly configured with return_value, not accessing attributes\n"
    "- Test assertions must compare actual values, not mock objects\n"
    "- Use proper pytest syntax and patterns\n\n"
    "Make the tests practical and not overly strict. Focus on:\n"
    "- Core functionality works as expected\n"
    "- Basic edge cases (empty inputs, null values)\n"
    "- Type validation for critical parameters\n"
    "- Avoid overly specific assertions that may be brittle\n"
    "- Use reasonable tolerances for floating point comparisons\n"
    "- Test the most important behaviors rather than every possible edge case\n\n"
    "It is very important that all tests are directly runnable with the syntax of the code provided.\n\n"
    "Provide only the code content inside the codeblocks, nothing else."
    "Also when the provided file is run with pytest test.py it should print the results in a txt file in the same directory"
)

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

class GeneratorAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, code, tests, filename="code.py", model="gpt-4o", previous_error=None):
        if previous_error:
            prompt = GENERATOR_PROMPT.format(filename=filename, code=code, test_plan=tests) + f"\n\nIMPORTANT: The previous attempt failed with this error: {previous_error}\nFix this specific issue in the new test code."
        else:
            prompt = GENERATOR_PROMPT.format(filename=filename, code=code, test_plan=tests)
            
        resp = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ""},
                {"role": "user", "content": prompt},
            ],
        )
        test_code = resp.choices[0].message.content
        return strip_code_blocks(test_code)
