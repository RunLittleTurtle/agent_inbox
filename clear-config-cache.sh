#!/bin/bash
# Clear Next.js Config Cache - Based on MCP_AGENT_CONFIGURATION_GUIDE.md
# CRITICAL: This solution ALWAYS WORKS for Next.js cache corruption issues
# This script handles the directory navigation automatically

echo "🧹 Clearing Next.js config cache (MCP Guide Solution)..."
echo "📋 This fixes: ENOENT: no such file or directory, open '.next/server/pages/_document.js'"

# Step 1: Stop all development servers
echo "🔍 Stopping any running processes on port 3004..."
lsof -ti:3004 | xargs kill -9 2>/dev/null || true
echo "✅ Port 3004 cleared"

# Step 2: Navigate to agent-inbox
cd agent-inbox 2>/dev/null || { echo "❌ Error: agent-inbox directory not found"; exit 1; }
echo "📂 Working in: $(pwd)"

# Step 3: Clear ALL Next.js cache (as per MCP guide)
echo "🗑️  Removing .next directory..."
rm -rf .next
echo "✅ .next directory removed"

echo "🗑️  Removing node_modules/.cache..."
rm -rf node_modules/.cache
echo "✅ node_modules/.cache removed"

echo "🧹 Cleaning npm cache..."
npm cache clean --force 2>/dev/null
echo "✅ npm cache cleaned"

# Success message
echo ""
echo "✨ Cache cleared successfully!"
echo "📝 Next steps:"
echo "   1. Start config server: cd agent-inbox && npm run dev:config"
echo "   2. Or use the CLI: python cli.py config"
echo ""
echo "🔧 This fixes common issues:"
echo "   - Black and white unstyled UI"
echo "   - Runtime errors about missing build files"
echo "   - Server failing to load styled components"