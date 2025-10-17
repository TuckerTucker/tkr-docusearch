"""
Standalone test runner for file_validator module.

This runner avoids importing the processing module's __init__.py
which has heavy dependencies (torch, etc.).
"""

import subprocess
import sys
from pathlib import Path

# Get the processing directory
processing_dir = Path(__file__).parent

# Run pytest directly on the test file without importing the module
result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        str(processing_dir / "test_file_validator.py"),
        "-v",
        "--tb=short",
        "-p",
        "no:cacheprovider",
    ],
    env={
        **dict(os.environ),
        "PYTHONDONTWRITEBYTECODE": "1",
    },
    cwd=processing_dir,
)

sys.exit(result.returncode)
