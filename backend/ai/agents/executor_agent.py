import tempfile
import subprocess
import os

class ExecutorAgent:
    def execute(self, test_code, workspace_path=None):
        """Execute test code in the given workspace or temporary directory"""
        if not test_code:
            return {"error": "Missing test_code"}, 400
        
        try:
            if workspace_path and os.path.exists(workspace_path):
                # Use the project workspace
                test_file = os.path.join(workspace_path, "test_generated.py")
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write(test_code)
                
                # Run pytest in the workspace directory
                proc = subprocess.run(
                    ["pytest", test_file, "-v", "--tb=short", "--maxfail=1"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=30,
                    cwd=workspace_path  # Run in the project workspace
                )
                output = proc.stdout
                passed = proc.returncode == 0
                
                # Clean up the test file
                try:
                    os.remove(test_file)
                except:
                    pass  # Ignore cleanup errors
                    
            else:
                # Fallback to temporary directory (original behavior)
                with tempfile.TemporaryDirectory() as tmpdir:
                    test_file = os.path.join(tmpdir, "test_file.py")
                    with open(test_file, "w", encoding="utf-8") as f:
                        f.write(test_code)
                    proc = subprocess.run(
                        ["pytest", test_file, "-v", "--tb=short", "--maxfail=1"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=30,
                    )
                    output = proc.stdout
                    passed = proc.returncode == 0
            
            return {"passed": passed, "output": output}
        except Exception as e:
            return {"error": str(e), "step": "executor"}, 500
