#!/usr/bin/env python3
"""
Simulate the exact triage logic execution to verify template resolution
This replicates what triage.py does when processing an email
"""
import asyncio
import sys
from pathlib import Path

# Add the eaia module to path
sys.path.insert(0, str(Path(__file__).parent / "eaia"))

from eaia.main.config import get_config

async def simulate_triage_processing():
    """Simulate exactly what triage.py does when processing an email"""

    print("🔍 Simulating Executive AI Assistant Triage Processing")
    print("=" * 60)

    # This is exactly what triage.py does - loads config with empty configurable
    config = {"configurable": {}}
    prompt_config = await get_config(config)

    print(f"📋 Config loaded:")
    print(f"   name: '{prompt_config.get('name', 'NOT_FOUND')}'")
    print(f"   full_name: '{prompt_config.get('full_name', 'NOT_FOUND')}'")
    print()

    # Simulate the triage_prompt.format() call from triage.py line 51-63
    print("🎯 Simulating triage prompt formatting (what the LLM actually sees):")
    print("-" * 70)

    # Extract the exact values that would be passed to the prompt
    name = prompt_config["name"]
    full_name = prompt_config["full_name"]
    background = prompt_config["background"]
    triage_no = prompt_config["triage_no"]
    triage_email = prompt_config["triage_email"]
    triage_notify = prompt_config["triage_notify"]

    # Simulate a sample email (like our test email)
    sample_email = {
        "subject": "Quick question about the AI project",
        "from_email": "colleague@company.com",
        "to_email": "info@800m.ca",
        "page_content": "Hi bill, I wanted to ask about the LangGraph implementation you're working on. Could we schedule a quick call to discuss the architecture?"
    }

    # This simulates the triage_prompt.format() call from triage.py
    print(f"📧 Sample Email: {sample_email['subject']}")
    print(f"   From: {sample_email['from_email']}")
    print(f"   Content: {sample_email['page_content'][:80]}...")
    print()

    print(f"🧠 What the AI model would see in triage prompt:")
    print(f"   name: '{name}'")
    print(f"   full_name: '{full_name}'")
    print(f"   background: '{background[:100]}...'")
    print()

    print(f"📝 Triage rules (checking for name references):")

    # Check triage_email rules
    if "bill" in triage_email:
        print(f"✅ triage_email: Contains 'bill' ({triage_email.count('bill')} times)")
    else:
        print(f"❌ triage_email: Does NOT contain 'bill'")

    if "{name}" in triage_email:
        print(f"❌ triage_email: Still contains '{{name}}' template ({triage_email.count('{name}')} times)")
    else:
        print(f"✅ triage_email: No unresolved templates")

    print()

    # Check a sample from triage_email rules
    sample_rules = triage_email.split('\n')[:3]  # First 3 lines
    print(f"📋 Sample triage rules (what AI sees):")
    for i, rule in enumerate(sample_rules, 1):
        if rule.strip():
            print(f"   {i}. {rule.strip()}")

    print()
    print(f"🎉 CONCLUSION:")
    if "bill" in triage_email and "{name}" not in triage_email:
        print(f"   ✅ Executive AI Assistant correctly sees 'bill' instead of templates!")
        print(f"   ✅ Triage logic will work with proper name personalization")
    else:
        print(f"   ❌ Templates not properly resolved - AI may see literal '{{name}}'")

if __name__ == "__main__":
    asyncio.run(simulate_triage_processing())