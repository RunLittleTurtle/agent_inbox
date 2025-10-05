#!/bin/bash
"""
Wrapper script for OS-level cron job
This script ensures proper environment setup when run by cron
"""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../.." &> /dev/null && pwd )"
EXECUTIVE_DIR="$PROJECT_ROOT/src/executive-ai-assistant"

# Change to executive assistant directory
cd "$EXECUTIVE_DIR"

# Activate virtual environment
source "$PROJECT_ROOT/.venv/bin/activate"

# Run the cron job with logging
python scripts/run_cron_job.py --minutes-since 30 --url http://127.0.0.1:2025 >> "$PROJECT_ROOT/logs/cron.log" 2>&1