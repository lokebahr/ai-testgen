import tempfile
import subprocess
import os
import sys
import shutil

class ExecutorAgent:
    def execute(self, test_code, workspace_path=None, source_file_path=None):
       
        if not test_code:
            return {"error": "Missing test_code"}, 400
        
        def setup_workspace_for_imports(workspace_root, source_path):
    
            try:
                if source_path and os.path.exists(source_path):
                
                    source_filename = os.path.basename(source_path)
                    
                   
                    function_py_path = os.path.join(workspace_root, "function.py")
                    shutil.copy2(source_path, function_py_path)
                    
                   
                    original_name_path = os.path.join(workspace_root, source_filename)
                    if original_name_path != function_py_path:
                        shutil.copy2(source_path, original_name_path)
                    
                    print(f"[EXECUTE] Copied {source_path} to {function_py_path} and {original_name_path}")
                
                # create init.py was needed if it did not exist
                init_py_path = os.path.join(workspace_root, "__init__.py")
                if not os.path.exists(init_py_path):
                    with open(init_py_path, "w") as f:
                        f.write("# Auto-generated __init__.py for test execution\n")
                    print(f"[EXECUTE] Created {init_py_path}")
                
                return True
            except Exception as e:
                print(f"[EXECUTE] Error setting up workspace: {e}")
                return False
        
        def run_pytest_with_path(test_file_path, cwd_path, retry_count=0):
            env = os.environ.copy()
            # Add workspace to PYTHONPATH
            env["PYTHONPATH"] = cwd_path + os.pathsep + env.get("PYTHONPATH", "")
            
            # Also add to sys.path by modifying the test file
            modified_test_code = f"""import sys
import os
sys.path.insert(0, r'{cwd_path}')

{test_code}"""
            
           #write into the new testfile
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(modified_test_code)
            
            proc = subprocess.run(
                ["pytest", test_file_path, "-v", "--tb=short", "--maxfail=1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=30,
                cwd=cwd_path,
                env=env
            )
            
            # Check for ImportError and provide suggestion
            if proc.returncode != 0 and "ImportError" in proc.stdout and retry_count == 0:
                print(f"[EXECUTE] ImportError detected on first attempt, retrying...")
                # Ensure workspace setup is complete
                if source_file_path:
                    setup_workspace_for_imports(cwd_path, source_file_path)
                
                # Retry with the same setup
                proc = subprocess.run(
                    ["pytest", test_file_path, "-v", "--tb=short", "--maxfail=1"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=30,
                    cwd=cwd_path,
                    env=env
                )
            
            return proc
        
        try:
            if workspace_path and os.path.exists(workspace_path):
                # Use the project workspace
                test_file = os.path.join(workspace_path, "test_generated.py")
                
                # Set up workspace for proper imports
                setup_success = setup_workspace_for_imports(workspace_path, source_file_path)
                if not setup_success:
                    print(f"[EXECUTE] Warning: Failed to fully set up workspace for imports")
                
                # Run pytest in the workspace directory with retry logic
                proc = run_pytest_with_path(test_file, workspace_path)
                output = proc.stdout
                passed = proc.returncode == 0
                
                # Build result with additional information
                result = {"passed": passed, "output": output}
                
                if not passed:
                    if "ImportError" in output:
                        result["errorStep"] = "import"
                        result["suggestion"] = "Ensure the source file is properly accessible. Check that function.py exists in the workspace."
                    elif "ModuleNotFoundError" in output:
                        result["errorStep"] = "import"
                        result["suggestion"] = "Module not found. Verify the import statements in the test code match the actual file structure."
                
                # Clean up the test file
                try:
                    os.remove(test_file)
                except:
                    pass  # Ignore cleanup errors
                    
            else:
                # Fallback to temporary directory (original behavior)
                with tempfile.TemporaryDirectory() as tmpdir:
                    test_file = os.path.join(tmpdir, "test_file.py")
                    
                    # If we have a source file, copy it to the temp directory as well
                    if source_file_path and os.path.exists(source_file_path):
                        setup_workspace_for_imports(tmpdir, source_file_path)
                    
                    proc = run_pytest_with_path(test_file, tmpdir)
                    output = proc.stdout
                    passed = proc.returncode == 0
                    
                    result = {"passed": passed, "output": output}
                    if not passed and "ImportError" in output:
                        result["errorStep"] = "import"
                        result["suggestion"] = "Import error in temporary workspace. This may be due to missing dependencies or incorrect import paths."
            
            return result
        except Exception as e:
            return {"error": str(e), "step": "executor"}, 500
