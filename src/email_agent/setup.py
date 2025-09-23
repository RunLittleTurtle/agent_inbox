#!/usr/bin/env python3
"""
Setup script for email_agent package
Makes eaia module properly importable in LangGraph server context
"""

from setuptools import setup, find_packages

setup(
    name="email_agent",
    version="1.0.0",
    description="Email Agent with MCP tools and draft workflow StateGraph",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        # Core dependencies for email agent
        "langchain-core",
        "langgraph",
        "langchain-openai",
        "langchain-anthropic",
        "google-api-python-client",
        "google-auth",
        "google-auth-oauthlib",
        "python-dotenv",
        "pydantic",
    ],
    package_data={
        "eaia.create_draft_workflow": ["config.yaml"],
    },
    include_package_data=True,
)