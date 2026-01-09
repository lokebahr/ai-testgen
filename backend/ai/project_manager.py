import os
import uuid
import tempfile
import shutil
import stat
import time
from typing import Dict, List, Optional, Union
from git import Repo, RemoteReference
import json


def remove_readonly(func, path, _):
    """Error handler for Windows readonly files during shutil.rmtree"""
    if os.path.exists(path):
        os.chmod(path, stat.S_IWRITE)
        func(path)

def safe_rmtree(path):
    """Safely remove directory tree on Windows"""
    if os.path.exists(path):
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


class ProjectManager:
    def __init__(self):
        # In-memory storage for projects (in production, use Redis or database)
        self.projects: Dict[str, Dict] = {}
        self.base_temp_dir = tempfile.gettempdir()
    
    def init_project(self, mode: str, file_content: Optional[str] = None, 
                    git_url: Optional[str] = None, filename: Optional[str] = None, 
                    branch: Optional[str] = None) -> Dict:
        """Initialize a new project workspace"""
        project_id = str(uuid.uuid4())
        
        if mode == "single":
            if not file_content:
                raise ValueError("file_content is required for single mode")
            
            # Create temp directory for single file
            project_dir = os.path.join(self.base_temp_dir, f"testgen_project_{project_id}")
            os.makedirs(project_dir, exist_ok=True)
            
            # Write the single file
            file_name = filename or "main.py"
            file_path = os.path.join(project_dir, file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
                
        elif mode == "git":
            if not git_url:
                raise ValueError("git_url is required for git mode")
            
            project_dir = os.path.join(self.base_temp_dir, f"testgen_project_{project_id}")
            try:
                if branch:
                    repo = Repo.clone_from(git_url, project_dir, branch=branch)
                else:
                    repo = Repo.clone_from(git_url, project_dir)
            except Exception as e:
                raise ValueError(f"Failed to clone repository: {str(e)}")
        else:
            raise ValueError("mode must be 'single' or 'git'")
        
        # Store project info
        self.projects[project_id] = {
            "id": project_id,
            "mode": mode,
            "root_path": project_dir,
            "git_url": git_url if mode == "git" else None,
            "branch": branch if mode == "git" and branch else None,
            "created_at": None
        }
        
        return {
            "project_id": project_id,
            "root_path": project_dir
        }
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project info by ID"""
        return self.projects.get(project_id)
    
    def get_file_tree(self, project_id: str) -> List[Dict]:
        """Get file tree for a project"""
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        root_path = project["root_path"]
        if not os.path.exists(root_path):
            raise ValueError(f"Project directory {root_path} not found")
        
        def build_tree(path: str, name: str = None) -> Dict:
            """Recursively build file tree"""
            if name is None:
                name = os.path.basename(path)
            
            if os.path.isfile(path):
                return {
                    "name": name,
                    "path": os.path.relpath(path, root_path).replace("\\", "/"),
                    "type": "file"
                }
            else:
                children = []
                try:
                    for item in sorted(os.listdir(path)):
                        # Skip hidden files and common build/cache directories
                        if item.startswith('.') or item in ['__pycache__', 'node_modules', '.git']:
                            continue
                        item_path = os.path.join(path, item)
                        children.append(build_tree(item_path, item))
                except PermissionError:
                    pass  # Skip directories we can't read
                
                return {
                    "name": name,
                    "path": os.path.relpath(path, root_path).replace("\\", "/"),
                    "type": "dir",
                    "children": children
                }
        
        # Return the root as a list to match the API spec
        tree = build_tree(root_path, "root")
        return tree["children"] if tree["type"] == "dir" else [tree]
    
    def get_file_content(self, project_id: str, file_path: str) -> str:
        """Get content of a specific file"""
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Normalize path separators
        file_path = file_path.replace("/", os.sep)
        full_path = os.path.join(project["root_path"], file_path)
        
        # Security check: ensure the path is within the project directory
        if not os.path.commonpath([full_path, project["root_path"]]) == project["root_path"]:
            raise ValueError("Invalid file path")
        
        if not os.path.exists(full_path):
            raise ValueError(f"File {file_path} not found")
        
        if not os.path.isfile(full_path):
            raise ValueError(f"{file_path} is not a file")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Handle binary files
            raise ValueError(f"File {file_path} is not a text file")
    
    def write_test_file(self, project_id: str, test_code: str, test_filename: str = "test_generated.py") -> str:
        """Write test code to a file in the project workspace"""
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        test_path = os.path.join(project["root_path"], test_filename)
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        return test_path
    
    def cleanup_project(self, project_id: str) -> None:
        """Clean up project workspace"""
        project = self.get_project(project_id)
        if project and os.path.exists(project["root_path"]):
            safe_rmtree(project["root_path"])
        if project_id in self.projects:
            del self.projects[project_id]
    
    def list_projects(self) -> List[Dict]:
        """List all active projects"""
        return list(self.projects.values())
    
    def get_git_branches(self, git_url: str) -> List[str]:
        """Get available branches from a git repository"""
        try:
            temp_dir = os.path.join(self.base_temp_dir, f"temp_branch_check_{uuid.uuid4()}")
            
            try:
                # Use bare clone to avoid checking out files
                repo = Repo.clone_from(git_url, temp_dir, bare=True)
                branches = []
                for ref in repo.refs:
                    if isinstance(ref, RemoteReference) and ref.remote_name == 'origin':
                        branch_name = ref.name.replace('origin/', '')
                        if branch_name != 'HEAD':
                            branches.append(branch_name)
                
                # Close the repo object to release file handles
                repo.close()
                return sorted(branches)
            finally:
                # Give a moment for file handles to be released
                time.sleep(0.1)
                safe_rmtree(temp_dir)
        except Exception as e:
            raise ValueError(f"Failed to fetch branches: {str(e)}")


# Global instance
project_manager = ProjectManager()
