#!/usr/bin/env python3
"""
CLI Entry Point - Ambient Email Agent
Redirects to the main CLI application in CLI/CLI.py
"""

import sys
import subprocess
from pathlib import Path

# Run the main CLI directly
if __name__ == "__main__":
    cli_script = Path(__file__).parent / "CLI" / "CLI.py"
    result = subprocess.run([sys.executable, str(cli_script)] + sys.argv[1:])
    sys.exit(result.returncode)
