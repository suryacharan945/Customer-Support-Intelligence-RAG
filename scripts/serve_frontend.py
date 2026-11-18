import os
import subprocess
import sys

web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
cmd = ["npx.cmd", "vite", "--host", "0.0.0.0", "--port", "5173"]

try:
    proc = subprocess.Popen(cmd, cwd=web_dir)
    proc.wait()
except Exception as e:
    print(f"Error starting vite: {e}", file=sys.stderr)
    sys.exit(1)
