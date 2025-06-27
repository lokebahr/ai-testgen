import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_test_plan(code, language, framework):
    prompt = f"""
    You are an expert in {language} and testing with {framework}.
    Suggest a list of tests for the following code, without writing any test code yet.
    Return ONLY a JSON array of short test descriptions, e.g.:
    ["Invalid input test", "Edge cases", "Empty values"]
    Code:
    ```
    {code}
    ```
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message["content"]

def generate_tests(code, test_plan, filename):
    prompt = f"""
    Given the following code in {filename}:
    ```
    {code}
    ```
    And the following test plan:
    {test_plan}
    Write complete test code using correct imports for {filename}. Use pytest style. Output only the test code. 
    It should be instantly runnable
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message["content"]