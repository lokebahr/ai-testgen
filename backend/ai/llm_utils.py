
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

from .agents.planner_agent import PlannerAgent
from .agents.generator_agent import GeneratorAgent
from .agents.executor_agent import ExecutorAgent
from .agents.reviewer_agent import ReviewerAgent
from markdown import markdown as md_to_html

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize agents
planner_agent = PlannerAgent()
generator_agent = GeneratorAgent()
executor_agent = ExecutorAgent()
reviewer_agent = ReviewerAgent()



@app.route("/plan", methods=["POST"])
def plan():
    data = request.json
    code = data.get("code")
    language = data.get("language", "python")
    framework = data.get("framework", "pytest")
    if not code:
        return jsonify({"error": "Missing code"}), 400
    print("[PLAN] Planning tests for code snippet...")
    try:
        result = planner_agent.plan(code, language=language, framework=framework)
        # Strip markdown code blocks if present
        if result.startswith("```json"):
            result = result[7:].strip()
        if result.startswith("```"):
            result = result[3:].strip()
        if result.endswith("```"):
            result = result[:-3].strip()
        
        tests = eval(result) if isinstance(result, str) else result
        print(f"[PLAN] Suggested tests: {result}")
        return jsonify({"tests": tests})
    except Exception as e:
        print(f"[PLAN][ERROR] {e}")
        return jsonify({"error": str(e), "step": "planner"}), 500


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    code = data.get("code")
    tests = data.get("tests")
    filename = data.get("filename", "code.py")
    if not code or not tests:
        return jsonify({"error": "Missing code or tests"}), 400
    print(f"[GENERATE] Generating tests for {filename} with plan: {tests}")
    try:
        test_code = generator_agent.generate(code, tests, filename=filename)
        print(f"[GENERATE] Stripped test code:\n{test_code}")
        return jsonify({"test_code": test_code})
    except Exception as e:
        print(f"[GENERATE][ERROR] {e}")
        return jsonify({"error": str(e), "step": "generator"}), 500


@app.route("/execute", methods=["POST"])
def execute():
    data = request.json
    test_code = data.get("test_code")
    print(f"[EXECUTE] Running pytest on provided test code...")
    result = executor_agent.execute(test_code)
    if isinstance(result, tuple):
        # error case
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.route("/review", methods=["POST"])
def review():
    data = request.json
    passed = data.get("passed")
    output = data.get("output")
    code = data.get("code")
    test_code = data.get("test_code")
    conversation = data.get("conversation")
    if passed is None or output is None:
        print("[REVIEW][ERROR] Missing passed or output")
        return jsonify({"error": "Missing passed or output"}), 400
    if passed:
        print("[REVIEW] All tests passed!")
        return jsonify({"status": "ALL_TESTS_PASS"})
    try:
        print(f"[REVIEW] Reviewing failed pytest output with full context (including test code)...")
        review_result = reviewer_agent.review(output, code=code, test_code=test_code, conversation=conversation)
        print(f"[REVIEW] Parsed result: {review_result}")
        
        # The reviewer agent now returns a dictionary directly
        if isinstance(review_result, dict):
            return jsonify(review_result)
        else:
            # Fallback if it somehow returns a string
            import json
            try:
                result = json.loads(review_result)
                return jsonify(result)
            except json.JSONDecodeError:
                return jsonify({
                    "status": "FAILED", 
                    "analysis_markdown": str(review_result), 
                    "fix_markdown": "No suggestion provided."
                })
    except Exception as e:
        print(f"[REVIEW][ERROR] {e}")
        return jsonify({"error": str(e), "step": "reviewer"}), 500


@app.route("/orchestrate", methods=["POST"])
def orchestrate():
    data = request.json
    code = data.get("code")
    language = data.get("language", "python")
    framework = data.get("framework", "pytest")
    filename = data.get("filename", "code.py")
    # 1. Plan
    try:
        plan_result = planner_agent.plan(code, language=language, framework=framework)
        # Strip markdown code blocks if present
        if plan_result.startswith("```json"):
            plan_result = plan_result[7:].strip()
        if plan_result.startswith("```"):
            plan_result = plan_result[3:].strip()
        if plan_result.endswith("```"):
            plan_result = plan_result[:-3].strip()
            
        tests = eval(plan_result) if isinstance(plan_result, str) else plan_result
    except Exception as e:
        return jsonify({"error": str(e), "step": "planner"}), 500
    # 2. Generate
    try:
        test_code = generator_agent.generate(code, tests, filename=filename)
    except Exception as e:
        return jsonify({"error": str(e), "step": "generator"}), 500
    # 3. Execute
    result = executor_agent.execute(test_code)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    output = result["output"]
    passed = result["passed"]
    # 4. Review
    if passed:
        return jsonify({"status": "ALL_TESTS_PASS"})
    try:
        review_result = reviewer_agent.review(output, code=code, test_code=test_code)
        
        # The reviewer agent now returns a dictionary directly
        if isinstance(review_result, dict):
            return jsonify(review_result)
        else:
            # Fallback if it somehow returns a string
            import json
            try:
                result = json.loads(review_result)
                return jsonify(result)
            except json.JSONDecodeError:
                return jsonify({
                    "status": "FAILED", 
                    "analysis_markdown": str(review_result), 
                    "fix_markdown": "No suggestion provided."
                })
    except Exception as e:
        return jsonify({"error": str(e), "step": "reviewer"}), 500
