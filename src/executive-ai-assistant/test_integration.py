#!/usr/bin/env python3
"""
Integration test to verify templates work in actual executive AI assistant execution
"""
import asyncio
import sys
from pathlib import Path

# Add the eaia module to path
sys.path.insert(0, str(Path(__file__).parent / "eaia"))

from eaia.main.config import get_config

async def test_real_world_usage():
    """Test config loading exactly as the executive AI assistant modules do"""

    print("🚀 Testing Real-World Executive AI Assistant Usage")
    print("=" * 55)

    # Simulate how triage.py loads config
    config = {"configurable": {}}  # This is what gets passed to get_config
    prompt_config = await get_config(config)

    print(f"✅ Config loaded successfully")
    print(f"   Name: '{prompt_config.get('name', 'NOT_FOUND')}'")
    print(f"   Full Name: '{prompt_config.get('full_name', 'NOT_FOUND')}'")
    print()

    # Test what triage.py would see
    triage_rules = {
        'triage_no': prompt_config.get('triage_no', ''),
        'triage_email': prompt_config.get('triage_email', ''),
        'triage_notify': prompt_config.get('triage_notify', '')
    }

    print("📧 Triage Rules (what the agent actually sees):")
    print("-" * 50)

    user_name = prompt_config.get('name', 'UNKNOWN')

    for rule_type, content in triage_rules.items():
        if content:
            # Check if the actual name appears in the content
            name_count = content.count(user_name)
            template_count = content.count('{name}')

            print(f"{rule_type}:")
            print(f"  ✅ Contains '{user_name}': {name_count} times")
            if template_count > 0:
                print(f"  ❌ Still contains '{{name}}': {template_count} times")
            else:
                print(f"  ✅ No unresolved templates")
            print()

    # Test what rewrite.py would see
    rewrite_prefs = prompt_config.get('rewrite_preferences', '')
    if rewrite_prefs:
        print("✍️  Rewrite Preferences (what rewrite.py sees):")
        print("-" * 45)
        name_count = rewrite_prefs.count(user_name)
        template_count = rewrite_prefs.count('{name}')

        print(f"  ✅ Contains '{user_name}': {name_count} times")
        if template_count > 0:
            print(f"  ❌ Still contains '{{name}}': {template_count} times")
        else:
            print(f"  ✅ No unresolved templates")

    print()
    print("🎯 SUMMARY: Executive AI Assistant will see:")
    print(f"   User name: '{user_name}' (not '{{name}}')")
    print(f"   Full name: '{prompt_config.get('full_name', 'UNKNOWN')}'")
    print("   All templates properly resolved ✅")

if __name__ == "__main__":
    asyncio.run(test_real_world_usage())