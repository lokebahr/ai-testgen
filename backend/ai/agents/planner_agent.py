import os
from openai import OpenAI

PLANNER_PROMPT = (
    "You are an expert in {language} and testing with {framework}.\n"
    "Suggest a concise list of practical tests for the following code, without writing any test code yet.\n"
    "Focus on essential functionality rather than exhaustive edge cases:\n"
    "- Main functionality works correctly\n"
    "- Basic input validation (empty, null, wrong types)\n"
    "- Key edge cases that are likely to occur\n"
    "- Avoid overly specific or brittle test scenarios\n"
    "Return ONLY a JSON array of short test descriptions, e.g.:\n"
    '["Basic functionality", "Invalid input handling", "Key edge cases"]\n'
    "Code:\n\n{code}"
)

class PlannerAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)

    def plan(self, code, language="python", framework="pytest", model="gpt-4o"):
        prompt = PLANNER_PROMPT.format(language=language, framework=framework, code=code)
        resp = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ""},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content
