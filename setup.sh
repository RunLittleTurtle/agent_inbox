#!/bin/bash

# Agent Inbox Setup Script
# Automated installation and configuration for the Agent Inbox system
# Run with: chmod +x setup.sh && ./setup.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "╭─────────────────────────────────────╮"
    echo "│          Agent Inbox Setup          │"
    echo "│     Automated Installation Script   │"
    echo "╰─────────────────────────────────────╯"
    echo -e "${NC}"
}

# Check requirements
check_requirements() {
    print_info "Checking system requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is required but not installed."
        print_info "Please install Node.js from https://nodejs.org/"
        exit 1
    fi
    
    # Check yarn
    if ! command -v yarn &> /dev/null; then
        print_warning "Yarn not found, installing globally..."
        npm install -g yarn
    fi
    
    print_status "System requirements check passed"
}

# Setup Python virtual environment
setup_python_env() {
    print_info "Setting up Python virtual environment..."
    
    # Remove existing venv if it exists
    if [ -d ".venv" ]; then
        print_warning "Existing virtual environment found, removing..."
        rm -rf .venv
    fi
    
    # Create new virtual environment
    python3 -m venv .venv
    print_status "Virtual environment created"
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip
    print_info "Upgrading pip..."
    .venv/bin/pip install --upgrade pip
    
    # Install Python dependencies
    print_info "Installing Python dependencies (this may take a few minutes)..."
    .venv/bin/pip install -r requirements.txt
    
    print_status "Python environment setup complete"
}

# Setup Node.js dependencies
setup_nodejs_deps() {
    print_info "Installing Node.js dependencies..."
    
    # Install Agent Inbox dependencies
    if [ -d "agent-inbox" ]; then
        print_info "Installing Agent Inbox dependencies..."
        cd agent-inbox
        yarn install --silent
        cd ..
        print_status "Agent Inbox dependencies installed"
    else
        print_warning "Agent Inbox directory not found, skipping..."
    fi
    
    # Install Agent Chat UI dependencies
    if [ -d "agent-chat-ui" ]; then
        print_info "Installing Agent Chat UI dependencies..."
        cd agent-chat-ui
        npm install --silent
        cd ..
        print_status "Agent Chat UI dependencies installed"
    else
        print_warning "Agent Chat UI directory not found, skipping..."
    fi
}

# Setup environment files
setup_env_files() {
    print_info "Setting up environment files..."
    
    # Main .env file
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# OpenAI API Key (Required - replace with your actual key)
OPENAI_API_KEY=your_openai_api_key_here

# LangSmith Configuration (Optional but recommended)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_TRACING=true
LANGCHAIN_PROJECT=agent-inbox-project

# MCP Server Configuration (Optional - for calendar functionality)
PIPEDREAM_MCP_SERVER=your_pipedream_mcp_server_url
EOF
        print_status "Created main .env file"
    else
        print_warning "Main .env file already exists, skipping..."
    fi
    
    # Agent Chat UI .env.local
    if [ -d "agent-chat-ui" ] && [ ! -f "agent-chat-ui/.env.local" ]; then
        cat > agent-chat-ui/.env.local << EOF
# Agent Chat UI Configuration
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=agent
EOF
        print_status "Created Agent Chat UI environment file"
    fi
    
    # Agent Inbox .env.local
    if [ -d "agent-inbox" ] && [ ! -f "agent-inbox/.env.local" ]; then
        cat > agent-inbox/.env.local << EOF
# Agent Inbox Configuration
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=agent
EOF
        print_status "Created Agent Inbox environment file"
    fi
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."
    
    # Check Python dependencies
    source .venv/bin/activate
    if python -c "import langgraph, langchain, fastapi, typer, psutil" 2>/dev/null; then
        print_status "Python dependencies verified"
    else
        print_error "Python dependencies verification failed"
        exit 1
    fi
    
    # Check CLI availability
    if python -c "from CLI.CLI import app" 2>/dev/null; then
        print_status "CLI system verified"
    else
        print_error "CLI system verification failed"
        exit 1
    fi
    
    print_status "Installation verification complete"
}

# Create convenience scripts
create_scripts() {
    print_info "Creating convenience scripts..."
    
    # Create start script
    cat > start.sh << 'EOF'
#!/bin/bash
# Agent Inbox Start Script
source .venv/bin/activate
python cli.py start
EOF
    chmod +x start.sh
    
    # Create dev script for individual components
    cat > dev.sh << 'EOF'
#!/bin/bash
# Agent Inbox Development Script
# Usage: ./dev.sh [langgraph|inbox|chat]

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
EOF
    chmod +x dev.sh
    
    print_status "Convenience scripts created"
}

# Main installation process
main() {
    print_header
    
    print_info "Starting Agent Inbox setup..."
    print_info "This will install Python and Node.js dependencies and configure the system."
    echo
    
    # Run setup steps
    check_requirements
    setup_python_env
    setup_nodejs_deps
    setup_env_files
    verify_installation
    create_scripts
    
    echo
    print_status "🎉 Agent Inbox setup complete!"
    echo
    print_info "Next steps:"
    echo "1. Add your OpenAI API key to the .env file"
    echo "2. (Optional) Add your LangSmith API key to the .env file"
    echo "3. Start the system with: ./start.sh"
    echo "   Or start individual components with: ./dev.sh [langgraph|inbox|chat]"
    echo
    print_info "Available URLs after starting:"
    echo "• Agent Inbox:    http://localhost:3000"
    echo "• Agent Chat UI:  http://localhost:3001" 
    echo "• LangGraph API:  http://localhost:2024"
    echo
    print_warning "Remember to activate the virtual environment: source .venv/bin/activate"
}

# Run main function
main "$@"
