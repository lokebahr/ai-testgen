from flask import Blueprint, request, jsonify
from .llm_utils import generate_test_plan, generate_tests

llm_blueprint = Blueprint("llm", __name__)

@llm_blueprint.route("/api/testplan", methods=["POST"])
def get_test_plan():
    data = request.json
    code = data.get("code")
    language = data.get("language", "python")
    framework = data.get("framework", "pytest")

    if not code:
        return jsonify({"error": "Missing code"}), 400

    try:
        plan = generate_test_plan(code, language, framework)
        return jsonify({"plan": plan})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@llm_blueprint.route("/api/test_creation", methods=["POST"])
def create_tests():
    data = request.json
    code = data.get("code")
    test_plan = data.get("testPlan")
    filename = data.get("filename")

    if not code or not test_plan or not filename:
        return jsonify({"error": "Missing code, testPlan, or filename"}), 400

    try:
        tests = generate_tests(code, test_plan, filename)
        return jsonify({"tests": tests})
    except Exception as e:
        return jsonify({"error": str(e)}), 500