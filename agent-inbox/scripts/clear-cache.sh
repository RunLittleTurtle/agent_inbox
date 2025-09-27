#!/bin/bash
# Next.js Cache Clear Script - Permanent Fix for Cache Corruption

echo "🧹 Clearing Next.js cache to prevent runtime errors..."

# Kill any processes on config port
lsof -ti:3004 | xargs kill -9 2>/dev/null || true

# Clear all Next.js cache directories
rm -rf .next 2>/dev/null || true
rm -rf node_modules/.cache 2>/dev/null || true

# Clear npm cache
npm cache clean --force 2>/dev/null || true

echo "✅ Cache cleared successfully!"
echo "📝 You can now run 'npm run dev:config' to start the server"