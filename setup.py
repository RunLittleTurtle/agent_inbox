#!/usr/bin/env python3
"""
Agent Inbox Setup Script (Cross-Platform)
Automated installation and configuration for the Agent Inbox system
Run with: python setup.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import platform

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_status(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.NC}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")

def print_header():
    print(f"{Colors.BLUE}")
    print("╭─────────────────────────────────────╮")
    print("│          Agent Inbox Setup          │")
    print("│   Cross-Platform Python Installer   │")
    print("╰─────────────────────────────────────╯")
    print(f"{Colors.NC}")

def run_command(cmd, cwd=None, shell=False):
    """Run a command and return success status"""
    try:
        if shell:
            result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, 
                                  capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, cwd=cwd, check=True, 
                                  capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_requirements():
    """Check system requirements"""
    print_info("Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print_error("Python 3.8+ is required")
        return False
    
    # Check Node.js
    if not shutil.which("node"):
        print_error("Node.js is required but not installed")
        print_info("Please install Node.js from https://nodejs.org/")
        return False
    
    # Check/install yarn
    if not shutil.which("yarn"):
        print_warning("Yarn not found, installing globally...")
        success, _ = run_command(["npm", "install", "-g", "yarn"])
        if not success:
            print_error("Failed to install yarn")
            return False
    
    print_status("System requirements check passed")
    return True

def setup_python_env():
    """Setup Python virtual environment"""
    print_info("Setting up Python virtual environment...")
    
    venv_path = Path(".venv")
    
    # Remove existing venv if it exists
    if venv_path.exists():
        print_warning("Existing virtual environment found, removing...")
        shutil.rmtree(venv_path)
    
    # Create new virtual environment
    success, output = run_command([sys.executable, "-m", "venv", ".venv"])
    if not success:
        print_error("Failed to create virtual environment")
        return False
    
    print_status("Virtual environment created")
    
    # Determine pip executable path
    if platform.system() == "Windows":
        pip_exe = venv_path / "Scripts" / "pip"
        python_exe = venv_path / "Scripts" / "python"
    else:
        pip_exe = venv_path / "bin" / "pip"
        python_exe = venv_path / "bin" / "python"
    
    # Upgrade pip
    print_info("Upgrading pip...")
    success, _ = run_command([str(pip_exe), "install", "--upgrade", "pip"])
    if not success:
        print_error("Failed to upgrade pip")
        return False
    
    # Install Python dependencies
    print_info("Installing Python dependencies (this may take a few minutes)...")
    success, _ = run_command([str(pip_exe), "install", "-r", "requirements.txt"])
    if not success:
        print_error("Failed to install Python dependencies")
        return False
    
    print_status("Python environment setup complete")
    return True

def setup_nodejs_deps():
    """Setup Node.js dependencies"""
    print_info("Installing Node.js dependencies...")
    
    # Install Agent Inbox dependencies
    agent_inbox_path = Path("agent-inbox")
    if agent_inbox_path.exists():
        print_info("Installing Agent Inbox dependencies...")
        success, _ = run_command(["yarn", "install"], cwd=agent_inbox_path)
        if success:
            print_status("Agent Inbox dependencies installed")
        else:
            print_warning("Failed to install Agent Inbox dependencies")
    else:
        print_warning("Agent Inbox directory not found, skipping...")
    
    # Install Agent Chat UI dependencies
    agent_chat_path = Path("agent-chat-ui")
    if agent_chat_path.exists():
        print_info("Installing Agent Chat UI dependencies...")
        success, _ = run_command(["npm", "install"], cwd=agent_chat_path)
        if success:
            print_status("Agent Chat UI dependencies installed")
        else:
            print_warning("Failed to install Agent Chat UI dependencies")
    else:
        print_warning("Agent Chat UI directory not found, skipping...")
    
    return True

def setup_env_files():
    """Setup environment files"""
    print_info("Setting up environment files...")
    
    # Main .env file
    env_path = Path(".env")
    if not env_path.exists():
        env_content = """# OpenAI API Key (Required - replace with your actual key)
OPENAI_API_KEY=your_openai_api_key_here

# LangSmith Configuration (Optional but recommended)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_TRACING=true
LANGCHAIN_PROJECT=agent-inbox-project

# MCP Server Configuration (Optional - for calendar functionality)
PIPEDREAM_MCP_SERVER=your_pipedream_mcp_server_url
"""
        env_path.write_text(env_content)
        print_status("Created main .env file")
    else:
        print_warning("Main .env file already exists, skipping...")
    
    # Agent Chat UI .env.local
    chat_ui_path = Path("agent-chat-ui")
    if chat_ui_path.exists():
        chat_env_path = chat_ui_path / ".env.local"
        if not chat_env_path.exists():
            chat_env_content = """# Agent Chat UI Configuration
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=agent
"""
            chat_env_path.write_text(chat_env_content)
            print_status("Created Agent Chat UI environment file")
    
    # Agent Inbox .env.local
    inbox_path = Path("agent-inbox")
    if inbox_path.exists():
        inbox_env_path = inbox_path / ".env.local"
        if not inbox_env_path.exists():
            inbox_env_content = """# Agent Inbox Configuration
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=agent
"""
            inbox_env_path.write_text(inbox_env_content)
            print_status("Created Agent Inbox environment file")
    
    return True

def verify_installation():
    """Verify installation"""
    print_info("Verifying installation...")
    
    # Determine python executable path
    if platform.system() == "Windows":
        python_exe = Path(".venv") / "Scripts" / "python"
    else:
        python_exe = Path(".venv") / "bin" / "python"
    
    # Check Python dependencies
    test_imports = "import langgraph, langchain, fastapi, typer, psutil"
    success, _ = run_command([str(python_exe), "-c", test_imports])
    if success:
        print_status("Python dependencies verified")
    else:
        print_error("Python dependencies verification failed")
        return False
    
    # Check CLI availability  
    cli_test = "from CLI.CLI import app"
    success, _ = run_command([str(python_exe), "-c", cli_test])
    if success:
        print_status("CLI system verified")
    else:
        print_error("CLI system verification failed")
        return False
    
    print_status("Installation verification complete")
    return True

def create_scripts():
    """Create convenience scripts"""
    print_info("Creating convenience scripts...")
    
    if platform.system() == "Windows":
        # Create Windows batch files
        start_script = Path("start.bat")
        start_content = """@echo off
call .venv\\Scripts\\activate
python cli.py start
"""
        start_script.write_text(start_content)
        
        dev_script = Path("dev.bat")
        dev_content = """@echo off
call .venv\\Scripts\\activate

if "%1"=="langgraph" (
    python cli.py langgraph
) else if "%1"=="inbox" (
    python cli.py inbox
) else if "%1"=="chat" (
    cd agent-chat-ui && npm run dev
) else (
    echo Usage: %0 {langgraph^|inbox^|chat}
    echo   langgraph - Start LangGraph server only
    echo   inbox     - Start Agent Inbox UI only
    echo   chat      - Start Agent Chat UI only
)
"""
        dev_script.write_text(dev_content)
    else:
        # Create Unix shell scripts
        start_script = Path("start.sh")
        start_content = """#!/bin/bash
source .venv/bin/activate
python cli.py start
"""
        start_script.write_text(start_content)
        start_script.chmod(0o755)
        
        dev_script = Path("dev.sh")
        dev_content = """#!/bin/bash
source .venv/bin/activate

case "$1" in
    langgraph)
        python cli.py langgraph
        ;;
    inbox)
        python cli.py inbox
        ;;
    chat)
        cd agent-chat-ui && npm run dev
        ;;
    *)
        echo "Usage: $0 {langgraph|inbox|chat}"
        echo "  langgraph - Start LangGraph server only"
        echo "  inbox     - Start Agent Inbox UI only" 
        echo "  chat      - Start Agent Chat UI only"
        exit 1
        ;;
esac
"""
        dev_script.write_text(dev_content)
        dev_script.chmod(0o755)
    
    print_status("Convenience scripts created")
    return True

def main():
    """Main installation process"""
    print_header()
    
    print_info("Starting Agent Inbox setup...")
    print_info("This will install Python and Node.js dependencies and configure the system.")
    print()
    
    # Run setup steps
    if not check_requirements():
        sys.exit(1)
    
    if not setup_python_env():
        sys.exit(1)
    
    if not setup_nodejs_deps():
        sys.exit(1)
    
    if not setup_env_files():
        sys.exit(1)
    
    if not verify_installation():
        sys.exit(1)
    
    if not create_scripts():
        sys.exit(1)
    
    print()
    print_status("🎉 Agent Inbox setup complete!")
    print()
    print_info("Next steps:")
    print("1. Add your OpenAI API key to the .env file")
    print("2. (Optional) Add your LangSmith API key to the .env file")
    
    if platform.system() == "Windows":
        print("3. Start the system with: start.bat")
        print("   Or start individual components with: dev.bat [langgraph|inbox|chat]")
        print_warning("Remember to activate the virtual environment: .venv\\Scripts\\activate")
    else:
        print("3. Start the system with: ./start.sh")
        print("   Or start individual components with: ./dev.sh [langgraph|inbox|chat]")
        print_warning("Remember to activate the virtual environment: source .venv/bin/activate")
    
    print()
    print_info("Available URLs after starting:")
    print("• Agent Inbox:    http://localhost:3000")
    print("• Agent Chat UI:  http://localhost:3001")
    print("• LangGraph API:  http://localhost:2024")

if __name__ == "__main__":
    main()
