import tempfile
import subprocess
import os

class ExecutorAgent:
    def execute(self, test_code):
        if not test_code:
            return {"error": "Missing test_code"}, 400
        try:
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
