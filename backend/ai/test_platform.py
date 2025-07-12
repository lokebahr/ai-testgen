from flask import Blueprint, request, jsonify
from .project_manager import project_manager
from .agents.planner_agent import PlannerAgent
from .agents.generator_agent import GeneratorAgent
from .agents.executor_agent import ExecutorAgent
from .agents.reviewer_agent import ReviewerAgent
import os
import json

# Create blueprint
test_platform = Blueprint('test_platform', __name__)

# Initialize agents
planner_agent = PlannerAgent()
generator_agent = GeneratorAgent()
executor_agent = ExecutorAgent()
reviewer_agent = ReviewerAgent()


@test_platform.route("/init", methods=["POST"])
def init_project():
    """Initialize a new project workspace"""
    try:
        data = request.json
        mode = data.get("mode")  # "single" or "git"
        
        if mode == "single":
            file_content = data.get("file")
            filename = data.get("filename", "main.py")
            result = project_manager.init_project(mode, file_content=file_content, filename=filename)
        elif mode == "git":
            git_url = data.get("git_url")
            result = project_manager.init_project(mode, git_url=git_url)
        else:
            return jsonify({"error": "Invalid mode. Use 'single' or 'git'"}), 400
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@test_platform.route("/projects/<project_id>/files", methods=["GET"])
def get_project_files(project_id):
    """Get file tree for a project"""
    try:
        file_tree = project_manager.get_file_tree(project_id)
        return jsonify(file_tree)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@test_platform.route("/projects/<project_id>/files/<path:file_path>", methods=["GET"])
def get_file_content(project_id, file_path):
    """Get content of a specific file"""
    try:
        content = project_manager.get_file_content(project_id, file_path)
        return jsonify({"content": content, "path": file_path})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@test_platform.route("/projects/<project_id>/plan", methods=["POST"])
def plan_tests(project_id):
    """Plan tests for a specific file"""
    try:
        data = request.json
        file_path = data.get("file_path")
        language = data.get("language", "python")
        framework = data.get("framework", "pytest")
        
        if not file_path:
            return jsonify({"error": "Missing file_path"}), 400
        
        # Get the file content
        code = project_manager.get_file_content(project_id, file_path)
        
        print(f"[PLAN] Planning tests for {file_path} in project {project_id}")
        result = planner_agent.plan(code, language=language, framework=framework)
        
        # Strip markdown code blocks if present
        if result.startswith("```json"):
            result = result[7:].strip()
        if result.startswith("```"):
            result = result[3:].strip()
        if result.endswith("```"):
            result = result[:-3].strip()
        
        tests = eval(result) if isinstance(result, str) else result
        print(f"[PLAN] Suggested tests: {tests}")
        return jsonify({"tests": tests, "file_path": file_path})
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"[PLAN][ERROR] {e}")
        return jsonify({"error": str(e), "step": "planner"}), 500


@test_platform.route("/projects/<project_id>/generate", methods=["POST"])
def generate_tests(project_id):
    """Generate test code for a file"""
    try:
        data = request.json
        file_path = data.get("file_path")
        test_plan = data.get("test_plan")
        
        if not file_path or not test_plan:
            return jsonify({"error": "Missing file_path or test_plan"}), 400
        
        # Get the file content
        code = project_manager.get_file_content(project_id, file_path)
        filename = os.path.basename(file_path)
        
        print(f"[GENERATE] Generating tests for {file_path} with plan: {test_plan}")
        test_code = generator_agent.generate(code, test_plan, filename=filename)
        print(f"[GENERATE] Generated test code length: {len(test_code)}")
        
        return jsonify({"test_code": test_code, "file_path": file_path})
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"[GENERATE][ERROR] {e}")
        return jsonify({"error": str(e), "step": "generator"}), 500


@test_platform.route("/projects/<project_id>/execute", methods=["POST"])
def execute_tests(project_id):
    """Execute test code in the project workspace"""
    try:
        data = request.json
        test_code = data.get("test_code")
        
        if not test_code:
            return jsonify({"error": "Missing test_code"}), 400
        
        # Get project workspace path
        project = project_manager.get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        
        workspace_path = project["root_path"]
        
        print(f"[EXECUTE] Running pytest in project workspace: {workspace_path}")
        result = executor_agent.execute(test_code, workspace_path=workspace_path)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[EXECUTE][ERROR] {e}")
        return jsonify({"error": str(e), "step": "executor"}), 500


@test_platform.route("/projects/<project_id>/review", methods=["POST"])
def review_tests(project_id):
    """Review test execution results"""
    try:
        data = request.json
        passed = data.get("passed")
        output = data.get("output")
        code = data.get("code")
        test_code = data.get("test_code")
        conversation = data.get("conversation")
        
        if passed is None or output is None:
            return jsonify({"error": "Missing passed or output"}), 400
        
        if passed:
            print("[REVIEW] All tests passed!")
            return jsonify({"status": "ALL_TESTS_PASS"})
        
        print(f"[REVIEW] Reviewing failed pytest output for project {project_id}")
        review_result = reviewer_agent.review(output, code=code, test_code=test_code, conversation=conversation)
        print(f"[REVIEW] Parsed result: {review_result}")
        
        # The reviewer agent returns a dictionary directly
        if isinstance(review_result, dict):
            return jsonify(review_result)
        else:
            # Fallback if it somehow returns a string
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


@test_platform.route("/projects/<project_id>/test", methods=["POST"])
def orchestrate_tests(project_id):
    """Orchestrate the full test pipeline: plan → generate → execute → review"""
    try:
        data = request.json
        file_path = data.get("file_path")
        language = data.get("language", "python")
        framework = data.get("framework", "pytest")
        
        if not file_path:
            return jsonify({"error": "Missing file_path"}), 400
        
        # Get project and file content
        project = project_manager.get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        
        code = project_manager.get_file_content(project_id, file_path)
        filename = os.path.basename(file_path)
        workspace_path = project["root_path"]
        
        # 1. Plan
        print(f"[ORCHESTRATE] Step 1: Planning tests for {file_path}")
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
        print(f"[ORCHESTRATE] Step 2: Generating test code")
        try:
            test_code = generator_agent.generate(code, tests, filename=filename)
        except Exception as e:
            return jsonify({"error": str(e), "step": "generator"}), 500
        
        # 3. Execute
        print(f"[ORCHESTRATE] Step 3: Executing tests in workspace")
        result = executor_agent.execute(test_code, workspace_path=workspace_path)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        
        output = result["output"]
        passed = result["passed"]
        
        # 4. Review
        print(f"[ORCHESTRATE] Step 4: Reviewing results")
        if passed:
            return jsonify({
                "status": "ALL_TESTS_PASS",
                "file_path": file_path,
                "test_plan": tests,
                "test_code": test_code,
                "execution_result": result
            })
        
        try:
            review_result = reviewer_agent.review(output, code=code, test_code=test_code)
            
            # The reviewer agent returns a dictionary directly
            if isinstance(review_result, dict):
                review_result.update({
                    "file_path": file_path,
                    "test_plan": tests,
                    "test_code": test_code,
                    "execution_result": result
                })
                return jsonify(review_result)
            else:
                # Fallback if it somehow returns a string
                try:
                    result_dict = json.loads(review_result)
                    result_dict.update({
                        "file_path": file_path,
                        "test_plan": tests,
                        "test_code": test_code,
                        "execution_result": result
                    })
                    return jsonify(result_dict)
                except json.JSONDecodeError:
                    return jsonify({
                        "status": "FAILED", 
                        "analysis_markdown": str(review_result), 
                        "fix_markdown": "No suggestion provided.",
                        "file_path": file_path,
                        "test_plan": tests,
                        "test_code": test_code,
                        "execution_result": result
                    })
        except Exception as e:
            return jsonify({
                "error": str(e), 
                "step": "reviewer",
                "file_path": file_path,
                "test_plan": tests,
                "test_code": test_code,
                "execution_result": result
            }), 500
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"[ORCHESTRATE][ERROR] {e}")
        return jsonify({"error": str(e)}), 500


@test_platform.route("/projects", methods=["GET"])
def list_projects():
    """List all active projects"""
    try:
        projects = project_manager.list_projects()
        return jsonify({"projects": projects})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@test_platform.route("/projects/<project_id>", methods=["DELETE"])
def cleanup_project(project_id):
    """Clean up a project workspace"""
    try:
        project_manager.cleanup_project(project_id)
        return jsonify({"message": f"Project {project_id} cleaned up successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
