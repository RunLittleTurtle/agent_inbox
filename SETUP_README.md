# 🚀 Agent Inbox - One-Command Setup

This repository includes automated setup scripts for easy installation and configuration of the Agent Inbox system.

## 📋 Prerequisites

Before running the setup, ensure you have:

- **Python 3.8+** installed
- **Node.js 16+** installed
- **Git** installed (if cloning from repository)

## 🎯 One-Command Installation

### Option 1: Python Setup Script (Recommended - Cross-Platform)

```bash
python setup.py
```

### Option 2: Bash Setup Script (Unix/macOS only)

```bash
chmod +x setup.sh && ./setup.sh
```

## 🔧 What the Setup Script Does

The automated setup script will:

1. ✅ **Check system requirements** (Python, Node.js, Yarn)
2. ✅ **Create Python virtual environment** (.venv)
3. ✅ **Install all Python dependencies** (including LangGraph CLI)
4. ✅ **Install Node.js dependencies** for both UIs
5. ✅ **Create environment files** with correct configuration
6. ✅ **Verify installation** by testing imports
7. ✅ **Create convenience scripts** for easy startup

## 📁 What Gets Installed

### Python Dependencies
- **LangGraph & LangChain** ecosystem
- **LangGraph CLI with in-memory runtime** (`langgraph-cli[inmem]`)
- **FastAPI & Uvicorn** for web services
- **Rich & Typer** for beautiful CLI
- **Google APIs** for calendar integration
- **MCP adapters** for external tool integration

### Node.js Dependencies
- **Agent Inbox UI** (React/Next.js)
- **Agent Chat UI** (React/Next.js)
- All required frontend packages

### Configuration Files
- **Main `.env`** with API key templates
- **Agent Chat UI `.env.local`** with correct assistant ID
- **Agent Inbox `.env.local`** with correct assistant ID

## 🚀 After Setup - Quick Start

### Start Everything (Recommended)

**macOS/Linux:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

This starts all components:
- LangGraph API server (http://localhost:2024)
- Agent Inbox UI (http://localhost:3000)
- Agent Chat UI (http://localhost:3001)

### Start Individual Components

**macOS/Linux:**
```bash
./dev.sh langgraph    # LangGraph server only
./dev.sh inbox        # Agent Inbox UI only
./dev.sh chat         # Agent Chat UI only
```

**Windows:**
```cmd
dev.bat langgraph     # LangGraph server only
dev.bat inbox         # Agent Inbox UI only
dev.bat chat          # Agent Chat UI only
```

## 🔑 Required Configuration

After setup, you **must** add your API keys to the `.env` file:

```env
# Required for AI functionality
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Optional but recommended for observability
LANGSMITH_API_KEY=your-langsmith-key-here
```

## 🌐 Access Points

Once running, access these URLs:

| Service | URL | Description |
|---------|-----|-------------|
| **Agent Inbox** | http://localhost:3000 | Main human-in-the-loop interface |
| **Agent Chat** | http://localhost:3001 | Direct chat with AI agent |
| **LangGraph API** | http://localhost:2024 | Backend API server |

## 🧪 Testing the Installation

Test with a sample email workflow:

```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows

# Create a test email workflow
python cli.py email --subject "Test Email" --body "Hello, please help me write a response."
```

## 🛠️ Manual Setup (If Automated Setup Fails)

If the automated setup encounters issues:

1. **Create virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies:**
   ```bash
   cd agent-inbox && yarn install && cd ..
   cd agent-chat-ui && npm install && cd ..
   ```

4. **Copy environment files:**
   ```bash
   cp .env.example .env  # Edit with your API keys
   ```

## 📚 Additional Resources

- **Environment Setup Guide:** `ENVIRONMENT_SETUP.md`
- **MCP Integration:** `mcp_integration_plan.md`
- **Memory System:** `memory_plan.md`
- **Streaming Guide:** `streaming_plan.md`

## 🆘 Troubleshooting

### Common Issues

**Python virtual environment activation:**
- macOS/Linux: `source .venv/bin/activate`
- Windows: `.venv\Scripts\activate`

**Node.js dependencies:**
- Try `yarn install` or `npm install` in respective directories

**Port conflicts:**
- The system will automatically kill existing processes on required ports

**Missing API keys:**
- Add your OpenAI API key to `.env` file
- The system won't function without proper API keys

## 🤝 Support

If you encounter issues:

1. Check the console output for specific error messages
2. Ensure all prerequisites are installed
3. Try the manual setup steps
4. Check the troubleshooting section above

---

**Happy coding with Agent Inbox! 🤖📧**
