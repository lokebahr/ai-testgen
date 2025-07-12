import os
import openai

GENERATOR_PROMPT = (
    "Given the following code in {filename}:\n\n{code}\n\n"
    "And the following test plan:\n{test_plan}\n"
    "Write complete test code using correct imports for {filename}. Use pytest style. Output only the test code.\n\n"
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
        openai.api_key = self.api_key

    def generate(self, code, tests, filename="code.py", model="gpt-4o"):
        prompt = GENERATOR_PROMPT.format(filename=filename, code=code, test_plan=tests)
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": ""},
                {"role": "user", "content": prompt},
            ],
        )
        test_code = resp.choices[0].message["content"]
        return strip_code_blocks(test_code)
