#!/usr/bin/env python3
"""
Phase 0 Verification Test - DEFAULTS Export Verification
Tests that all agents properly export DEFAULTS for FastAPI config bridge
"""

import sys
import importlib
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_agent_defaults(agent_module_name: str, agent_display_name: str) -> dict:
    """Test that an agent has proper DEFAULTS exports"""
    print(f"\n{'='*60}")
    print(f"Testing: {agent_display_name} ({agent_module_name})")
    print(f"{'='*60}")

    results = {"agent": agent_display_name, "passed": True, "errors": []}

    try:
        # Test config.py
        config_mod = importlib.import_module(f"{agent_module_name}.config")

        if not hasattr(config_mod, "DEFAULTS"):
            results["passed"] = False
            results["errors"].append("config.py missing DEFAULTS export")
            print("❌ config.py: Missing DEFAULTS export")
        else:
            config_defaults = config_mod.DEFAULTS
            print(f"✓ config.py DEFAULTS keys: {list(config_defaults.keys())}")

            # Verify config structure
            if "llm" in config_defaults:
                print(f"  ✓ llm config: {len(config_defaults['llm'])} settings")
            if "agent_identity" in config_defaults:
                print(f"  ✓ agent_identity: {config_defaults['agent_identity'].get('agent_name', 'N/A')}")

        # Test prompt.py
        prompt_mod = importlib.import_module(f"{agent_module_name}.prompt")

        if not hasattr(prompt_mod, "DEFAULTS"):
            results["passed"] = False
            results["errors"].append("prompt.py missing DEFAULTS export")
            print("❌ prompt.py: Missing DEFAULTS export")
        else:
            prompt_defaults = prompt_mod.DEFAULTS
            print(f"✓ prompt.py DEFAULTS keys: {list(prompt_defaults.keys())}")
            print(f"  ✓ {len(prompt_defaults)} prompt templates exported")

        # Test ui_config.py (if it exists and should have DEFAULTS)
        try:
            ui_mod = importlib.import_module(f"{agent_module_name}.ui_config")
            if hasattr(ui_mod, "DEFAULTS"):
                ui_defaults = ui_mod.DEFAULTS
                print(f"✓ ui_config.py DEFAULTS keys: {list(ui_defaults.keys())}")
        except ImportError:
            print("  (ui_config.py not tested - may not exist)")

        print(f"\n✅ {agent_display_name}: All tests passed!")

    except Exception as e:
        results["passed"] = False
        results["errors"].append(str(e))
        print(f"\n❌ {agent_display_name}: FAILED")
        print(f"   Error: {e}")

    return results

def main():
    """Run all Phase 0 verification tests"""
    print("="*60)
    print("PHASE 0 VERIFICATION TEST")
    print("Testing DEFAULTS exports for FastAPI config bridge")
    print("="*60)

    # Define all agents to test
    agents = [
        ("calendar_agent", "Calendar Agent"),
        ("multi_tool_rube_agent", "Multi-Tool Rube Agent"),
        ("executive-ai-assistant", "Executive AI Assistant"),
        ("_react_agent_mcp_template", "React Agent MCP Template"),
    ]

    all_results = []

    # Test each agent
    for module_name, display_name in agents:
        result = test_agent_defaults(module_name, display_name)
        all_results.append(result)

    # Summary
    print("\n" + "="*60)
    print("PHASE 0 VERIFICATION SUMMARY")
    print("="*60)

    passed_count = sum(1 for r in all_results if r["passed"])
    total_count = len(all_results)

    for result in all_results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status}: {result['agent']}")
        if result["errors"]:
            for error in result["errors"]:
                print(f"       - {error}")

    print(f"\nResults: {passed_count}/{total_count} agents passed")

    if passed_count == total_count:
        print("\n🎉 SUCCESS! All agents have proper DEFAULTS exports!")
        print("✅ Phase 0 verification complete - ready for Phase 1")
        return 0
    else:
        print("\n⚠️  Some agents failed verification")
        print("❌ Fix errors before proceeding to Phase 1")
        return 1

if __name__ == "__main__":
    sys.exit(main())
