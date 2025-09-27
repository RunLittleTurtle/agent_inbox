#!/usr/bin/env python3
"""
MCP Tool Discovery Script for React Agent Template

This script helps you discover the exact tool names available from your MCP server
before configuring USEFUL_TOOL_NAMES in tools.py.

Usage:
    python discover_tools.py                    # Discover and display all tools
    python discover_tools.py --json             # Output in JSON format
    python discover_tools.py --copy-paste       # Output ready for copy-paste to USEFUL_TOOL_NAMES
    python discover_tools.py --save output.txt  # Save results to file

Best Practice Workflow:
1. Configure your agent in config.py
2. Run this script to discover available tools
3. Copy the tool names you want to USEFUL_TOOL_NAMES in tools.py
4. Test your agent
"""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from tools import discover_mcp_tools_sync, _agent_mcp
    from config import AGENT_NAME, MCP_SERVICE, MCP_ENV_VAR
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this script from the agent directory")
    print("and that you've configured the template in config.py")
    sys.exit(1)


def print_header():
    """Print script header"""
    print("="*70)
    print("🔍 MCP TOOL DISCOVERY - React Agent Template")
    print("="*70)
    print(f"Agent: {AGENT_NAME}")
    print(f"Service: {MCP_SERVICE}")
    print(f"Environment Variable: {MCP_ENV_VAR}")
    print(f"MCP URL: {os.getenv(MCP_ENV_VAR, 'NOT SET')}")
    print("-"*70)


def format_tools_for_copy_paste(tools_info):
    """Format tools for easy copy-paste to USEFUL_TOOL_NAMES"""
    if not tools_info:
        return "# No tools discovered"

    output = "USEFUL_TOOL_NAMES = {\n"

    # Group tools by category based on prefixes
    categories = {}
    for tool in tools_info:
        name = tool['name']
        # Extract category from tool name (e.g., 'google_drive-upload-file' -> 'File Operations')
        if '-create-' in name:
            category = "Creation"
        elif '-delete-' in name or '-remove-' in name:
            category = "Deletion"
        elif '-update-' in name or '-move-' in name:
            category = "Modification"
        elif '-list-' in name or '-find-' in name or '-search-' in name or '-get-' in name:
            category = "Query & Search"
        elif '-comment' in name or '-reply' in name:
            category = "Comments"
        elif '-share' in name or '-access' in name or '-permission' in name:
            category = "Sharing & Permissions"
        elif '-upload-' in name or '-download-' in name:
            category = "Transfer"
        else:
            category = "Other"

        if category not in categories:
            categories[category] = []
        categories[category].append(tool)

    # Output by category
    for category, tools in categories.items():
        output += f"    # {category}\n"
        for tool in tools:
            desc = tool['description'][:60] + '...' if len(tool['description']) > 60 else tool['description']
            output += f"    '{tool['name']}',  # {desc}\n"
        output += "\n"

    output += "}"
    return output


def format_tools_as_json(tools_info):
    """Format tools as JSON"""
    return json.dumps(tools_info, indent=2)


def format_tools_as_table(tools_info):
    """Format tools as a readable table"""
    if not tools_info:
        return "No tools discovered."

    output = f"\n📊 Discovered {len(tools_info)} tools:\n\n"

    for i, tool in enumerate(tools_info, 1):
        output += f"{i:2d}. {tool['name']}\n"
        output += f"    Description: {tool['description']}\n"
        output += f"    Inputs: {tool['inputs']}\n"
        output += "\n"

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Discover MCP tools for React Agent Template",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--format', '-f',
        choices=['table', 'json', 'copy-paste'],
        default='table',
        help='Output format (default: table)'
    )

    parser.add_argument(
        '--save', '-s',
        type=str,
        help='Save output to file'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress header and extra output'
    )

    parser.add_argument(
        '--validate-env',
        action='store_true',
        help='Only validate environment configuration'
    )

    args = parser.parse_args()

    if not args.quiet:
        print_header()

    # Check if template is configured
    if AGENT_NAME == "{AGENT_NAME}" or MCP_SERVICE == "{MCP_SERVICE}":
        print("❌ Template not configured yet!")
        print("Please configure the following in config.py:")
        print(f"  - AGENT_NAME: currently '{AGENT_NAME}'")
        print(f"  - MCP_SERVICE: currently '{MCP_SERVICE}'")
        print("\nExample configuration:")
        print("  AGENT_NAME = 'gmail'")
        print("  MCP_SERVICE = 'google_gmail'")
        sys.exit(1)

    # Validate environment
    mcp_url = os.getenv(MCP_ENV_VAR)
    if not mcp_url:
        print(f"❌ Environment variable {MCP_ENV_VAR} is not set")
        print(f"Please add it to your .env file:")
        print(f"{MCP_ENV_VAR}=https://mcp.pipedream.net/your-id/{MCP_SERVICE}")
        sys.exit(1)

    if args.validate_env:
        print("✅ Environment configuration is valid")
        return

    if not args.quiet:
        print("🔄 Discovering tools from MCP server...")

    try:
        # Discover tools
        tools_info = discover_mcp_tools_sync()

        if not tools_info:
            print("❌ No tools discovered. Check your MCP server configuration.")
            sys.exit(1)

        # Format output
        if args.format == 'json':
            output = format_tools_as_json(tools_info)
        elif args.format == 'copy-paste':
            output = format_tools_for_copy_paste(tools_info)
        else:  # table
            output = format_tools_as_table(tools_info)

        # Display or save
        if args.save:
            Path(args.save).write_text(output)
            print(f"✅ Results saved to {args.save}")
        else:
            print(output)

        if not args.quiet and args.format == 'table':
            print("\n" + "="*70)
            print("💡 TIP: Use --format copy-paste to get ready-to-use USEFUL_TOOL_NAMES")
            print("💡 TIP: Use --save output.txt to save results to a file")

    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
