"""
Google OAuth Agent Template
Generic template for building LangGraph agents with Google Workspace OAuth.

To use this template:
1. Copy this folder to src/{your_agent_name}/
2. Find and replace all {DOMAIN} placeholders with your domain (e.g., 'contacts', 'email', 'drive')
3. Update google_workspace_executor.py with your Google API service
4. Define your tools in google_workspace_tools.py
5. Customize prompts in prompt.py
6. Update state.py with domain-specific fields
"""

from .agent_orchestrator import create_google_auth_agent, GoogleAuthAgent

__all__ = ["create_google_auth_agent", "GoogleAuthAgent"]
