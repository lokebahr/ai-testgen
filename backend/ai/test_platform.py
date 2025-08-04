from flask import Blueprint, request, jsonify
from .project_manager import project_manager, safe_rmtree
from .agents.planner_agent import PlannerAgent
from .agents.generator_agent import GeneratorAgent
from .agents.executor_agent import ExecutorAgent
from .agents.reviewer_agent import ReviewerAgent
from db import db
from db.models import Project, File, TestStatus
import os
import json
import threading
import time
import tempfile

# Create blueprint
test_platform = Blueprint('test_platform', __name__)

# Initialize agents
planner_agent = PlannerAgent()
generator_agent = GeneratorAgent()
executor_agent = ExecutorAgent()
reviewer_agent = ReviewerAgent()

workflow_status = {}

def update_workflow_status(workflow_id, step, status, message="", progress=0):
    workflow_status[workflow_id] = {
        "step": step,
        "status": status,
        "message": message,
        "progress": progress,
        "timestamp": time.time()
    }

def update_file_test_status(project_id, file_path, status):
    """Update file test status in database"""
    try:
        # Find the file in the database
        file = File.query.filter_by(project_id=project_id, path=file_path).first()
        if file:
            file.test_status = status
            db.session.commit()
            print(f"[DB] Updated file {file_path} status to {status.value}")
        else:
            print(f"[DB] File {file_path} not found in project {project_id}")
    except Exception as e:
        print(f"[DB] Error updating file status: {e}")
        db.session.rollback()

@test_platform.route("/workflow/<workflow_id>/status", methods=["GET"])
def get_workflow_status(workflow_id):
    """Get the current status of a workflow"""
    status = workflow_status.get(workflow_id, {"step": "unknown", "status": "not_found", "message": "Workflow not found", "progress": 0})
    return jsonify(status)


@test_platform.route("/init", methods=["POST"])
def init_project():
    """Initialize a new project workspace and store in database"""
    try:
        data = request.json
        mode = data.get("mode")  # "single" or "git"
        
        # Create database project entry
        from db.models import Project, File, TestStatus
        from db import db
        
        if mode == "single":
            file_content = data.get("file")
            filename = data.get("filename", "main.py")
            title = data.get("title", f"Single File: {filename}")
            
            # Create project in database
            project = Project(
                title=title,
                mode=mode,
                git_repo=None,
                branch=None
            )
            db.session.add(project)
            db.session.flush()  # Get project ID
            
            # Create file in database
            file = File(
                project_id=project.id,
                path=filename,
                title=filename,
                file_content=file_content,
                test_status=TestStatus.UNTESTED
            )
            db.session.add(file)
            
            # Initialize with project manager for workspace
            result = project_manager.init_project(mode, file_content=file_content, filename=filename)
            # Map the project manager ID to our database ID
            project_manager.projects[result["project_id"]]["db_project_id"] = project.id
            
        elif mode == "git":
            git_url = data.get("git_url")
            branch = data.get("branch")
            title = data.get("title", f"Git: {git_url.split('/')[-1] if git_url else 'Unknown'}")
            
            # Create project in database
            project = Project(
                title=title,
                mode=mode,
                git_repo=git_url,
                branch=branch
            )
            db.session.add(project)
            db.session.flush()  # Get project ID
            
            # Initialize with project manager for workspace
            result = project_manager.init_project(mode, git_url=git_url, branch=branch)
            # Map the project manager ID to our database ID
            project_manager.projects[result["project_id"]]["db_project_id"] = project.id
            
            # Scan and add files to database
            import tempfile
            import shutil
            from git import Repo
            
            temp_dir = None
            try:
                temp_dir = os.path.join(tempfile.gettempdir(), f"scan_{project.id}")
                
                # Use shallow clone to reduce file operations
                if branch:
                    repo = Repo.clone_from(git_url, temp_dir, branch=branch, depth=1)
                else:
                    repo = Repo.clone_from(git_url, temp_dir, depth=1)
                
                # Close the repo object to release file handles
                repo.close()
                
                # Scan for source files
                for root, dirs, files in os.walk(temp_dir):
                    # Skip .git and other hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
                    
                    for filename in files:
                        if filename.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
                            file_path = os.path.join(root, filename)
                            relative_path = os.path.relpath(file_path, temp_dir).replace('\\', '/')
                            
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                
                                file = File(
                                    project_id=project.id,
                                    path=relative_path,
                                    title=filename,
                                    file_content=content,
                                    test_status=TestStatus.UNTESTED
                                )
                                db.session.add(file)
                            except (UnicodeDecodeError, IOError):
                                # Skip binary or unreadable files
                                continue
                                
            except Exception as e:
                db.session.rollback()
                return jsonify({"error": f"Failed to clone repository: {str(e)}"}), 400
            finally:
                if temp_dir and os.path.exists(temp_dir):
                    # Give a moment for file handles to be released
                    time.sleep(0.1)
                    safe_rmtree(temp_dir)
        else:
            return jsonify({"error": "Invalid mode. Use 'single' or 'git'"}), 400
        
        db.session.commit()
        
        return jsonify({
            "project_id": project.id,  # Return database project ID
            "root_path": result["root_path"]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@test_platform.route("/projects/<project_id>/files", methods=["GET"])
def get_project_files(project_id):
    """Get file tree for a project with test status information"""
    try:
        # Get files from database with test status
        files = File.query.filter_by(project_id=project_id).all()
        
        if not files:
            return jsonify({"error": "Project not found or has no files"}), 404
        
        # Build file tree structure with test status
        file_tree = []
        for file in files:
            file_node = {
                "name": file.title,
                "path": file.path,
                "type": "file",
                "test_status": file.test_status.value,
                "status_color": file.get_status_color()
            }
            file_tree.append(file_node)
        
        return jsonify(file_tree)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@test_platform.route("/projects/<project_id>/files/<path:file_path>", methods=["GET"])
def get_file_content(project_id, file_path):
    """Get content of a specific file with test status"""
    try:
        # Get file from database with test status
        file = File.query.filter_by(project_id=project_id, path=file_path).first()
        
        if not file:
            # Fallback to project manager if not in database
            content = project_manager.get_file_content(project_id, file_path)
            return jsonify({
                "content": content, 
                "path": file_path,
                "test_status": "untested",
                "status_color": "text-yellow-600 bg-yellow-50"
            })
        
        return jsonify({
            "content": file.file_content, 
            "path": file.path,
            "test_status": file.test_status.value,
            "status_color": file.get_status_color(),
            "title": file.title
        })
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
        return jsonify({"test_plan": tests, "file_path": file_path})
        
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
        source_file_path = data.get("source_file_path")  # Optional: path to the source file being tested
        
        if not test_code:
            return jsonify({"error": "Missing test_code"}), 400
        
        # Get project workspace path
        project = project_manager.get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404
        
        workspace_path = project["root_path"]
        
        # If source_file_path is relative, make it absolute within the workspace
        absolute_source_path = None
        if source_file_path:
            if os.path.isabs(source_file_path):
                absolute_source_path = source_file_path
            else:
                absolute_source_path = os.path.join(workspace_path, source_file_path)
        
        print(f"[EXECUTE] Running pytest in project workspace: {workspace_path}")
        if absolute_source_path:
            print(f"[EXECUTE] Source file: {absolute_source_path}")
        
        result = executor_agent.execute(test_code, workspace_path=workspace_path, source_file_path=absolute_source_path)
        
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
    """Orchestrate only the planning step - returns test plan for user confirmation"""
    try:
        data = request.json
        file_path = data.get("file_path")
        language = data.get("language", "python")
        framework = data.get("framework", "pytest")
        
        if not file_path:
            return jsonify({"error": "Missing file_path"}), 400
        
        # Get file content from database
        file = File.query.filter_by(project_id=project_id, path=file_path).first()
        if not file:
            return jsonify({"error": "File not found"}), 404
        
        code = file.file_content
        
        # 1. Plan only
        print(f"[ORCHESTRATE] Planning tests for {file_path}")
        try:
            plan_result = planner_agent.plan(code, language=language, framework=framework)
            # Strip markdown code blocks if present
            if plan_result.startswith("```json"):
                plan_result = plan_result[7:].strip()
            if plan_result.startswith("```"):
                plan_result = plan_result[3:].strip()
            if plan_result.endswith("```"):
                plan_result = plan_result[:-3].strip()
                
            test_plan = eval(plan_result) if isinstance(plan_result, str) else plan_result
            
            return jsonify({
                "test_plan": test_plan,
                "file_path": file_path
            })
            
        except Exception as e:
            return jsonify({"error": str(e), "step": "planner"}), 500
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"[ORCHESTRATE][ERROR] {e}")
        return jsonify({"error": str(e)}), 500


@test_platform.route("/projects/<project_id>/run", methods=["POST"])
def run_tests(project_id):
    """Run the complete test pipeline: generate → execute → review after plan approval"""
    try:
        data = request.json
        file_path = data.get("file_path")
        test_plan = data.get("test_plan")
        workflow_id = data.get("workflow_id", f"{project_id}_{int(time.time())}")
        
        if not file_path or not test_plan:
            return jsonify({"error": "Missing file_path or test_plan"}), 400
        
        update_workflow_status(workflow_id, "initializing", "running", "Setting up test environment", 5)
        
        # Get file content from database
        file = File.query.filter_by(project_id=project_id, path=file_path).first()
        if not file:
            return jsonify({"error": "File not found"}), 404
        
        # Get project from database
        db_project = Project.query.get(project_id)
        if not db_project:
            return jsonify({"error": "Project not found"}), 404
        
        code = file.file_content
        filename = os.path.basename(file_path)
        
        # Create or get workspace for test execution
        temp_workspace = None
        try:
            if db_project.mode == 'git':
                # Create temporary workspace for git projects
                temp_workspace = os.path.join(tempfile.gettempdir(), f"test_workspace_{project_id}_{int(time.time())}")
                os.makedirs(temp_workspace, exist_ok=True)
                
                # Write the file content to temp workspace
                file_full_path = os.path.join(temp_workspace, file_path)
                os.makedirs(os.path.dirname(file_full_path), exist_ok=True)
                with open(file_full_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                    
                workspace_path = temp_workspace
            else:
                # For single file projects, still need a workspace
                temp_workspace = os.path.join(tempfile.gettempdir(), f"test_workspace_{project_id}_{int(time.time())}")
                os.makedirs(temp_workspace, exist_ok=True)
                
                # Write the file to workspace
                file_full_path = os.path.join(temp_workspace, filename)
                with open(file_full_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                    
                workspace_path = temp_workspace
            
            update_workflow_status(workflow_id, "generating", "running", "AI is generating test code", 25)
            print(f"[RUN] Step 1: Generating test code")
            try:
                test_code = generator_agent.generate(code, test_plan, filename=filename)
            except Exception as e:
                update_workflow_status(workflow_id, "generating", "failed", f"Failed to generate tests: {str(e)}", 25)
                return jsonify({"error": str(e), "step": "generator"}), 500
            
            update_workflow_status(workflow_id, "executing", "running", "Running tests in workspace", 50)
            print(f"[RUN] Step 2: Executing tests in workspace")
            
            absolute_source_path = os.path.join(workspace_path, file_path if db_project.mode == 'git' else filename)
            
            result = executor_agent.execute(test_code, workspace_path=workspace_path, source_file_path=absolute_source_path)
            if isinstance(result, tuple):
                update_workflow_status(workflow_id, "executing", "failed", f"Test execution failed: {result[0].get('error', 'Unknown error')}", 50)
                return jsonify(result[0]), result[1]
            
            output = result["output"]
            passed = result["passed"]
            
            update_workflow_status(workflow_id, "reviewing", "running", "AI is analyzing test results", 75)
            print(f"[RUN] Step 3: Reviewing results")
            
            if passed:
                update_workflow_status(workflow_id, "completed", "success", "All tests passed!", 100)
                update_file_test_status(project_id, file_path, TestStatus.COMPLETED)  # Update file status to completed
                return jsonify({
                    "status": "ALL_TESTS_PASS",
                    "file_path": file_path,
                    "test_plan": test_plan,
                    "test_code": test_code,
                    "execution_result": result,
                    "workflow_id": workflow_id
                })
            
            # Tests failed - update status to failed
            update_file_test_status(project_id, file_path, TestStatus.FAILED)
            
            try:
                review_result = reviewer_agent.review(output, code=code, test_code=test_code)
                
                update_workflow_status(workflow_id, "completed", "completed", "Analysis complete", 100)
                
                if isinstance(review_result, dict):
                    review_result.update({
                        "file_path": file_path,
                        "test_plan": test_plan,
                        "test_code": test_code,
                        "execution_result": result,
                        "workflow_id": workflow_id
                    })
                    return jsonify(review_result)
                else:
                    try:
                        result_dict = json.loads(review_result)
                        result_dict.update({
                            "file_path": file_path,
                            "test_plan": test_plan,
                            "test_code": test_code,
                            "execution_result": result,
                            "workflow_id": workflow_id
                        })
                        return jsonify(result_dict)
                    except json.JSONDecodeError:
                        return jsonify({
                            "status": "FAILED", 
                            "issues": [{"test_name": "unknown", "error_type": "ParseError", "description": "Failed to parse analysis", "expected": "", "actual": "", "cause": "Analysis parsing error"}],
                            "summary": "Failed to parse test analysis",
                            "fixed_code": "No suggestion provided.",
                            "file_path": file_path,
                            "test_plan": test_plan,
                            "test_code": test_code,
                            "execution_result": result,
                            "workflow_id": workflow_id
                        })
            except Exception as e:
                update_workflow_status(workflow_id, "reviewing", "failed", f"Analysis failed: {str(e)}", 75)
                return jsonify({
                    "error": str(e), 
                    "step": "reviewer",
                    "file_path": file_path,
                    "test_plan": test_plan,
                    "test_code": test_code,
                    "execution_result": result,
                    "workflow_id": workflow_id
                }), 500
        
        finally:
            # Clean up temporary workspace
            if temp_workspace and os.path.exists(temp_workspace):
                time.sleep(0.1)  # Give time for file handles to be released
                safe_rmtree(temp_workspace)
                
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        print(f"[RUN][ERROR] {e}")
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


@test_platform.route("/git/branches", methods=["POST"])
def get_git_branches():
    """Get available branches from a git repository"""
    try:
        data = request.json
        git_url = data.get("git_url")
        
        if not git_url:
            return jsonify({"error": "git_url is required"}), 400
        
        branches = project_manager.get_git_branches(git_url)
        return jsonify({"branches": branches})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
