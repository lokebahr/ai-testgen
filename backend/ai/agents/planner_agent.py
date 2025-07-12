import os
import openai

PLANNER_PROMPT = (
    "You are an expert in {language} and testing with {framework}.\n"
    "Suggest a list of tests for the following code, without writing any test code yet.\n"
    "Return ONLY a JSON array of short test descriptions, e.g.:\n"
    '["Invalid input test", "Edge cases", "Empty values"]\n'
    "Code:\n\n{code}"
)

class PlannerAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def plan(self, code, language="python", framework="pytest", model="gpt-4o"):
        prompt = PLANNER_PROMPT.format(language=language, framework=framework, code=code)
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": ""},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message["content"]
