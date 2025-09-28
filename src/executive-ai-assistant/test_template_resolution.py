#!/usr/bin/env python3
"""
Test script to verify template resolution in executive AI assistant config
This ensures {name} gets resolved to actual values like "bill"
"""
import asyncio
import sys
from pathlib import Path

# Add the eaia module to path
sys.path.insert(0, str(Path(__file__).parent / "eaia"))

from eaia.main.config import get_config

async def test_template_resolution():
    """Test that config templates are properly resolved"""

    print("🧪 Testing Executive AI Assistant Template Resolution")
    print("=" * 60)

    # Load config (this should resolve templates)
    config = await get_config({"configurable": {}})

    print(f"📝 Raw config values:")
    print(f"   name: '{config.get('name', 'NOT_FOUND')}'")
    print(f"   full_name: '{config.get('full_name', 'NOT_FOUND')}'")
    print(f"   email: '{config.get('email', 'NOT_FOUND')}'")
    print()

    # Test fields that should have resolved templates
    template_fields = [
        'background',
        'background_preferences',
        'rewrite_preferences',
        'triage_no',
        'triage_notify',
        'triage_email'
    ]

    print("🔍 Checking template resolution in config fields:")
    print("-" * 50)

    passed_tests = 0
    total_tests = 0

    for field in template_fields:
        if field in config and config[field]:
            value = config[field]
            total_tests += 1

            # Check if value contains unresolved templates
            has_templates = '{name}' in value or '{full_name}' in value

            if has_templates:
                print(f"❌ {field}: CONTAINS UNRESOLVED TEMPLATES")
                print(f"   Value snippet: {value[:100]}...")
            else:
                print(f"✅ {field}: Templates resolved correctly")
                passed_tests += 1
            print()

    # Test specific substitutions
    if 'rewrite_preferences' in config:
        rewrite_prefs = config['rewrite_preferences']
        expected_name = config.get('name', 'UNKNOWN')

        print(f"🎯 Specific Test - Rewrite Preferences:")
        print(f"   Looking for name: '{expected_name}'")

        if expected_name in rewrite_prefs:
            print(f"✅ Found '{expected_name}' in rewrite preferences")
            passed_tests += 1
        else:
            print(f"❌ '{expected_name}' NOT found in rewrite preferences")
            print(f"   Content: {rewrite_prefs[:200]}...")

        total_tests += 1
        print()

    # Summary
    print("📊 Test Results:")
    print(f"   Passed: {passed_tests}/{total_tests}")

    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Template resolution working correctly!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - Templates may not be resolving properly")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_template_resolution())
    sys.exit(0 if success else 1)