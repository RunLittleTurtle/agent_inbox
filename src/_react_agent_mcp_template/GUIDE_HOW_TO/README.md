# React Agent MCP Template - Guide Documentation

Complete documentation for creating new MCP-enabled React Agents compatible with the Agent Inbox ecosystem.

## 📚 Current Guides (Updated 2025)

### Core Setup Guides

1. **[Config Setup Guide](01_CONFIG_SETUP_GUIDE.md)** ⚙️
   - Configuration system integration with config app
   - Two-way sync between UI and Python files
   - Field definitions and validation
   - Environment variable management

2. **[Agent Setup Guide](02_AGENT_SETUP_GUIDE.md)** 🤖
   - Template duplication and customization
   - MCP tool discovery and configuration
   - Supervisor integration
   - Testing and validation

3. **[Prompt Management Guide](03_PROMPT_MANAGEMENT_GUIDE.md)** 💭
   - System prompt design and structure
   - Config UI integration for prompt editing
   - Context integration and dynamic enhancement
   - Best practices for multi-agent systems

## 🚀 Quick Start Workflow

1. **Copy template** and navigate to new agent directory
2. **Configure identity** in `config.py` (replace ALL placeholders)
3. **Discover tools** using `python discover_tools.py --format copy-paste`
4. **Update tool list** in `tools.py` with discovered tools
5. **Set up config UI** following Config Setup Guide
6. **Test integration** with `python x_agent_orchestrator.py`
7. **Integrate with supervisor** using Agent Setup Guide

## 📋 File Structure Overview

```
src/your_agent/
├── config.py              # Main configuration & context
├── prompt.py               # System prompts (editable via UI)
├── tools.py                # MCP tools & discovery system
├── ui_config.py           # Configuration UI schema
├── x_agent_orchestrator.py # React agent creation
├── discover_tools.py       # Tool discovery script
├── schemas.py             # Data structures (optional)
├── human_inbox.py         # Human-in-the-loop integration
└── GUIDE_HOW_TO/          # Documentation
    ├── 01_CONFIG_SETUP_GUIDE.md
    ├── 02_AGENT_SETUP_GUIDE.md
    └── 03_PROMPT_MANAGEMENT_GUIDE.md
```

## 🔧 Key Features

- **Tool Discovery System**: Automatic MCP tool discovery with multiple output formats
- **Config UI Integration**: Web-based configuration with two-way sync
- **Modular Architecture**: Clear separation of concerns across files
- **LangGraph Compatible**: Follows LangGraph v1 best practices
- **Production Ready**: Error handling, logging, and debugging support

## 📖 Legacy Documentation

The following files are deprecated but kept for reference:

- `DEPRECATED_MCP_AGENT_CONFIGURATION_GUIDE.md` - Old configuration guide
- `DEPRECATED_TWO_WAY_SYNC_IMPLEMENTATION_GUIDE.md` - Old sync implementation
- `DEPRECATED_template_improvement_notes.md` - Historical improvement notes

**Use the new guides above instead of these deprecated files.**

## 🎯 Design Principles

1. **KISS**: Keep it simple, essentials only
2. **Clear Errors**: No graceful fallbacks, clear error messages
3. **MessagesState**: Use standard state, avoid custom state classes
4. **Supervisor Ready**: Automatic integration with supervisor routing
5. **MCP First**: Leverage MCP provider tools (Rube, Composio, Pipedream, etc.), add local tools sparingly
6. **Tool Discovery**: Use automatic discovery to find exact tool names

## ❓ Need Help?

1. **Config Issues**: See [Config Setup Guide](01_CONFIG_SETUP_GUIDE.md)
2. **Agent Setup**: See [Agent Setup Guide](02_AGENT_SETUP_GUIDE.md)
3. **Prompt Problems**: See [Prompt Management Guide](03_PROMPT_MANAGEMENT_GUIDE.md)
4. **Tool Discovery**: Use `python discover_tools.py --help`
5. **Testing**: Use `python x_agent_orchestrator.py` and `python tools.py`

## 🔄 Updates

**Latest Update**: September 2025
- Complete rewrite of documentation structure
- Separated concerns into focused guides
- Added comprehensive config app integration
- Enhanced tool discovery workflows
- Improved prompt management system

The template now provides a streamlined, production-ready foundation for creating MCP-enabled agents that integrate seamlessly with Agent Inbox, Agent Chat UI, and the Config App.