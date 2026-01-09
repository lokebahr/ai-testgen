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
import hashlib
from datetime import datetime
from git import Repo
import uuid
import subprocess

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
            file_content = data.get('file_content', '')
            file = File(
                project_id=project.id,
                path=data.get('filename', 'main.py'),
                title=data.get('filename', 'main.py'),
                file_content=file_content,
                content_hash=hashlib.sha256(file_content.encode('utf-8')).hexdigest() if file_content else None,
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
                                    content_hash=hashlib.sha256(content.encode('utf-8')).hexdigest(),
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
            file.update_content(data['file_content'])
        
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
            
            # Use ls-remote to get branches without cloning
            
            result = subprocess.run(
                ['git', 'ls-remote', '--heads', project.git_repo], 
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                return jsonify({"error": f"Failed to fetch branches: {result.stderr}"}), 500
            
            branches = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    # Format: "commit_hash refs/heads/branch_name"
                    parts = line.split('\t')
                    if len(parts) == 2 and parts[1].startswith('refs/heads/'):
                        branch_name = parts[1].replace('refs/heads/', '')
                        branches.append(branch_name)
            
            return jsonify({"branches": sorted(branches), "current_branch": project.branch}), 200
            
        except Exception as e:
            return jsonify({"error": f"Failed to fetch branches: {str(e)}"}), 500
                
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
                                content_hash=hashlib.sha256(content.encode('utf-8')).hexdigest(),
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
    """Sync project files with the latest version from git, preserving test results for unchanged files"""
    try:
        project = Project.query.get_or_404(project_id)
        
        if project.mode == 'single':
            return jsonify({"message": "Single file projects don't need syncing"}), 200
        
        if not project.git_repo:
            return jsonify({"error": "Project has no git repository"}), 400
        
        # Get current files in the database
        existing_files = {file.path: file for file in File.query.filter_by(project_id=project.id).all()}
        
        # Clone and scan files from current branch
        temp_dir = None
        try:
            temp_dir = os.path.join(tempfile.gettempdir(), f"sync_{project.id}_{uuid.uuid4()}")
            
            if project.branch:
                repo = Repo.clone_from(project.git_repo, temp_dir, branch=project.branch, depth=1)
            else:
                repo = Repo.clone_from(project.git_repo, temp_dir, depth=1)
            
            repo.close()
            
            # Track statistics
            files_added = 0
            files_updated = 0
            files_removed = 0
            files_unchanged = 0
            
            # Scan for files in the repository
            scanned_files = set()
            for root, dirs, files in os.walk(temp_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
                
                for filename in files:
                    if filename.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
                        file_path = os.path.join(root, filename)
                        relative_path = os.path.relpath(file_path, temp_dir).replace('\\', '/')
                        scanned_files.add(relative_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                new_content = f.read()
                            
                            new_content_hash = hashlib.sha256(new_content.encode('utf-8')).hexdigest()
                            
                            # Check if file exists and if content has changed
                            if relative_path in existing_files:
                                existing_file = existing_files[relative_path]
                                
                                if existing_file.content_hash != new_content_hash:
                                    # File content has changed - update it and reset test status
                                    existing_file.file_content = new_content
                                    existing_file.content_hash = new_content_hash
                                    existing_file.title = filename
                                    existing_file.test_status = TestStatus.UNTESTED
                                    existing_file.updated_at = datetime.utcnow()
                                    files_updated += 1
                                else:
                                    # File content unchanged - preserve test status
                                    files_unchanged += 1
                            else:
                                # New file - add it
                                file = File(
                                    project_id=project.id,
                                    path=relative_path,
                                    title=filename,
                                    file_content=new_content,
                                    content_hash=new_content_hash,
                                    test_status=TestStatus.UNTESTED
                                )
                                db.session.add(file)
                                files_added += 1
                                
                        except (UnicodeDecodeError, IOError):
                            continue
            
            # Remove files that no longer exist in the repository
            for file_path, file_obj in existing_files.items():
                if file_path not in scanned_files:
                    db.session.delete(file_obj)
                    files_removed += 1
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to sync project: {str(e)}"}), 500
        finally:
            if temp_dir and os.path.exists(temp_dir):
                time.sleep(0.1)
                safe_rmtree(temp_dir)
        
        # Return updated project with sync statistics
        result = project_schema.dump(project)
        return jsonify({
            "message": f"Project synced successfully.",
            "sync_stats": {
                "files_added": files_added,
                "files_updated": files_updated,
                "files_removed": files_removed,
                "files_unchanged": files_unchanged,
                "total_files": files_added + files_updated + files_unchanged
            },
            "project": result
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
