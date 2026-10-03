"""One-command local setup after MySQL schemas have been created."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
commands = [
    [sys.executable, str(ROOT / "scripts" / "generate_data.py"), "--rows", "100000"],
    [sys.executable, str(ROOT / "scripts" / "load_oltp.py")],
    [sys.executable, str(ROOT / "scripts" / "run_etl.py")],
]
for command in commands:
    print("\n>>>", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)
print("\nDemo setup complete. Start the UI with: streamlit run app.py")
