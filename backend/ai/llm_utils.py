import os
import time
import openai
from dotenv import load_dotenv
from openai.error import OpenAIError, RateLimitError, Timeout

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Missing OpenAI API key. Please set OPENAI_API_KEY in your .env file.")

openai.api_key = api_key

def _call_with_retries(payload, max_retries=3, backoff_factor=2):
    delay = 1
    for attempt in range(1, max_retries + 1):
        try:
            return openai.ChatCompletion.create(**payload)
        except (RateLimitError, Timeout):
            if attempt == max_retries:
                raise
            time.sleep(delay)
            delay *= backoff_factor
        except OpenAIError as e:
            raise RuntimeError(f"OpenAI API Error: {e}")

#för att ge clean i dfrontend
def _strip_code_blocks(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 1)[1].strip()
        if text.startswith("python"):
            text = text[len("python"):].strip()
        elif text.startswith("py"):
            text = text[len("py"):].strip()
    return text

def generate_test_plan(code, language, framework):
    prompt = f"""
You are an expert in {language} and testing with {framework}.
Suggest a list of tests for the following code, without writing any test code yet.
Return ONLY a JSON array of short test descriptions, e.g.:
["Invalid input test", "Edge cases", "Empty values"] 
Code:

{code}
"""
    payload = {
        "model": "o4-mini",
        "messages": [{"role": "user", "content": prompt}],
       
    }
    resp = _call_with_retries(payload)
    return resp.choices[0].message["content"]

def generate_tests(code, test_plan, filename):
    prompt = f"""
Given the following code in {filename}:

{code}

And the following test plan:
{test_plan}
Write complete test code using correct imports for {filename}. Use pytest style. Output only the test code. 

It is very important that all tests are directly runnable with the syntax of the code provided.

Provide only the code content inside the codeblocks, nothing else.
"""
    payload = {
        "model": "gpt-4.1",
        "messages": [{"role": "user", "content": prompt}],
        
    }
    resp = _call_with_retries(payload)
    content = resp.choices[0].message["content"]
    return _strip_code_blocks(content)

if __name__ == "__main__":
    try:
        sample_code = """
def divide(a, b):
    return a / b
"""
        plan = generate_test_plan(sample_code, "Python", "pytest")
        print("Test plan:\n", plan)
        tests = generate_tests(sample_code, plan, "math_utils.py")
        print("\nGenerated tests:\n", tests)
    except Exception as e:
        print("Error:", str(e))
