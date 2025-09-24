#!/usr/bin/env python3
"""
Test script to verify the main graph loads properly.
"""
import os
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add the src path to import eaia modules
sys.path.insert(0, str(Path(__file__).parent))

def test_graph_load():
    """Test that the main graph loads without errors."""
    print("Testing main graph loading...")

    try:
        from eaia.main.graph import graph
        print("✅ Main graph loaded successfully!")
        print(f"Graph type: {type(graph)}")
        return True

    except Exception as e:
        print(f"❌ Error loading main graph: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_graph_load()
    if not success:
        sys.exit(1)
    print("✅ Graph loading test completed successfully!")
