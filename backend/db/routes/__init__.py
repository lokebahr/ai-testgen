from flask import Blueprint, request, jsonify
from db import db
from db.models import Project, File, TestStatus
from db.schemas import ProjectSchema, ProjectCreateSchema, FileSchema, FileUpdateSchema
from marshmallow import ValidationError
import os
import tempfile
import shutil
import stat
import time
from git import Repo
import uuid

def safe_rmtree(path):
    """Safely remove directory tree on Windows"""
    if os.path.exists(path):
        def remove_readonly(func, path, _):
            """Error handler for Windows readonly files during shutil.rmtree"""
            if os.path.exists(path):
                os.chmod(path, stat.S_IWRITE)
                func(path)
        
        try:
            shutil.rmtree(path, onerror=remove_readonly)
        except Exception as e:
            print(f"Warning: Could not fully remove temp directory {path}: {e}")
            # Try to remove read-only attributes and try again
            try:
                for root, dirs, files in os.walk(path):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), stat.S_IWRITE)
                    for f in files:
                        os.chmod(os.path.join(root, f), stat.S_IWRITE)
                shutil.rmtree(path)
            except Exception:
                # If still fails, leave it for the OS to clean up later
                pass

# Create blueprint
db_routes = Blueprint('db_routes', __name__)

# Initialize schemas
project_schema = ProjectSchema()
projects_schema = ProjectSchema(many=True)
project_create_schema = ProjectCreateSchema()
file_schema = FileSchema()
files_schema = FileSchema(many=True)
file_update_schema = FileUpdateSchema()

@db_routes.route('/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    try:
        projects = Project.query.order_by(Project.updated_at.desc()).all()
        result = projects_schema.dump(projects)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@db_routes.route('/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        # Validate input
        data = project_create_schema.load(request.json)
        
        # Create project
        project = Project(
            title=data['title'],
            git_repo=data.get('git_repo'),
            branch=data.get('branch'),
            mode=data['mode']
        )
        
        db.session.add(project)
        db.session.flush()  # Get the project ID
        
        # Handle project initialization based on mode
        if data['mode'] == 'single':
            # Create a single file
            file = File(
                project_id=project.id,
                path=data.get('filename', 'main.py'),
                title=data.get('filename', 'main.py'),
                file_content=data.get('file_content', ''),
                test_status=TestStatus.UNTESTED
            )
            db.session.add(file)
            
        elif data['mode'] == 'git':
            # Clone repository and scan files
            temp_dir = None
            try:
                temp_dir = os.path.join(tempfile.gettempdir(), f"scan_{project.id}")
                
                # Use shallow clone to reduce file operations
                if data.get('branch'):
                    repo = Repo.clone_from(data['git_repo'], temp_dir, branch=data['branch'], depth=1)
                else:
                    repo = Repo.clone_from(data['git_repo'], temp_dir, depth=1)
                
                # Close the repo object to release file handles
                repo.close()
                
                # Scan for Python files (can be extended for other languages)
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
        
        db.session.commit()
        
        # Return the created project with files
        result = project_schema.dump(project)
        return jsonify(result), 201
        
    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@db_routes.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project with its files"""
    try:
        project = Project.query.get_or_404(project_id)
        result = project_schema.dump(project)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@db_routes.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project and all its files"""
    try:
        project = Project.query.get_or_404(project_id)
        db.session.delete(project)
        db.session.commit()
        return jsonify({"message": "Project deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@db_routes.route('/projects/<project_id>/files', methods=['GET'])
def get_project_files(project_id):
    """Get all files for a project"""
    try:
        project = Project.query.get_or_404(project_id)
        files = File.query.filter_by(project_id=project_id).all()
        result = files_schema.dump(files)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@db_routes.route('/projects/<project_id>/files/<file_id>', methods=['GET'])
def get_file(project_id, file_id):
    """Get a specific file"""
    try:
        file = File.query.filter_by(id=file_id, project_id=project_id).first_or_404()
        result = file_schema.dump(file)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@db_routes.route('/projects/<project_id>/files/<file_id>', methods=['PUT'])
def update_file(project_id, file_id):
    """Update a file's test status or content"""
    try:
        file = File.query.filter_by(id=file_id, project_id=project_id).first_or_404()
        
        # Validate input
        data = file_update_schema.load(request.json)
        
        # Update fields
        if 'test_status' in data:
            file.test_status = data['test_status']
        if 'file_content' in data:
            file.file_content = data['file_content']
        
        db.session.commit()
        
        result = file_schema.dump(file)
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@db_routes.route('/projects/<project_id>/files/<file_id>/test-status', methods=['PUT'])
def update_file_test_status(project_id, file_id):
    """Update a file's test status specifically"""
    try:
        file = File.query.filter_by(id=file_id, project_id=project_id).first_or_404()
        
        data = request.json
        if 'test_status' not in data:
            return jsonify({"error": "test_status is required"}), 400
        
        # Validate status
        valid_statuses = ['untested', 'completed', 'failed']
        if data['test_status'] not in valid_statuses:
            return jsonify({"error": f"Invalid status. Must be one of: {valid_statuses}"}), 400
        
        file.test_status = TestStatus(data['test_status'])
        db.session.commit()
        
        result = file_schema.dump(file)
        return jsonify(result), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@db_routes.route('/projects/<project_id>/branches', methods=['GET'])
def get_project_branches(project_id):
    """Get available branches for a git project"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if project.mode != 'git' or not project.git_repo:
            return jsonify({"error": "Project is not a git repository"}), 400
        
        temp_dir = None
        try:
            temp_dir = os.path.join(tempfile.gettempdir(), f"branches_{project.id}_{uuid.uuid4()}")
            
            # Use bare clone to avoid checking out files
            repo = Repo.clone_from(project.git_repo, temp_dir, bare=True)
            branches = []
            for ref in repo.refs:
                if hasattr(ref, 'remote_name') and ref.remote_name == 'origin':
                    branch_name = ref.name.replace('origin/', '')
                    if branch_name != 'HEAD':
                        branches.append(branch_name)
            
            repo.close()
            return jsonify({"branches": sorted(branches), "current_branch": project.branch}), 200
            
        except Exception as e:
            return jsonify({"error": f"Failed to fetch branches: {str(e)}"}), 500
        finally:
            if temp_dir and os.path.exists(temp_dir):
                time.sleep(0.1)
                safe_rmtree(temp_dir)
                
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@db_routes.route('/projects/<project_id>/switch-branch', methods=['POST'])
def switch_branch(project_id):
    """Switch to a different branch and sync files"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if project.mode != 'git' or not project.git_repo:
            return jsonify({"error": "Project is not a git repository"}), 400
        
        data = request.json
        new_branch = data.get('branch')
        if not new_branch:
            return jsonify({"error": "Branch name is required"}), 400
        
        # Update project branch
        project.branch = new_branch
        
        # Clear existing files and re-scan from new branch
        File.query.filter_by(project_id=project.id).delete()
        
        # Clone and scan files from new branch
        temp_dir = None
        try:
            temp_dir = os.path.join(tempfile.gettempdir(), f"switch_{project.id}_{uuid.uuid4()}")
            
            repo = Repo.clone_from(project.git_repo, temp_dir, branch=new_branch, depth=1)
            repo.close()
            
            # Scan for files
            for root, dirs, files in os.walk(temp_dir):
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
                            continue
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to switch branch: {str(e)}"}), 500
        finally:
            if temp_dir and os.path.exists(temp_dir):
                time.sleep(0.1)
                safe_rmtree(temp_dir)
        
        # Return updated project
        result = project_schema.dump(project)
        return jsonify(result), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@db_routes.route('/projects/<project_id>/sync', methods=['POST'])
def sync_project(project_id):
    """Sync project files with the latest version from git"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if project.mode == 'single':
            return jsonify({"message": "Single file projects don't need syncing"}), 200
        
        if not project.git_repo:
            return jsonify({"error": "Project has no git repository"}), 400
        
        # Clear existing files and re-scan
        File.query.filter_by(project_id=project.id).delete()
        
        # Clone and scan files from current branch
        temp_dir = None
        try:
            temp_dir = os.path.join(tempfile.gettempdir(), f"sync_{project.id}_{uuid.uuid4()}")
            
            if project.branch:
                repo = Repo.clone_from(project.git_repo, temp_dir, branch=project.branch, depth=1)
            else:
                repo = Repo.clone_from(project.git_repo, temp_dir, depth=1)
            
            repo.close()
            
            # Scan for files
            file_count = 0
            for root, dirs, files in os.walk(temp_dir):
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
                            file_count += 1
                        except (UnicodeDecodeError, IOError):
                            continue
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to sync project: {str(e)}"}), 500
        finally:
            if temp_dir and os.path.exists(temp_dir):
                time.sleep(0.1)
                safe_rmtree(temp_dir)
        
        # Return updated project
        result = project_schema.dump(project)
        return jsonify({
            "message": f"Project synced successfully. {file_count} files updated.",
            "project": result
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
