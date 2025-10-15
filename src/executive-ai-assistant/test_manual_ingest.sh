#!/bin/bash
# Manual Email Ingestion Test Script
# This script ingests recent emails into the executive AI assistant

# Configuration
DEPLOYMENT_URL="https://smith.langchain.com/o/87613dbc-ed91-41a3-b131-c2137c9e3dd2/deployments/dfc775bd-b1ed-4e8-b74d-f0e8f4e1d8e5"
USER_ID="user_33Z8MWmIOt29U9ii3uA54m3FoU5"
EMAIL="info@800m.ca"

# Test 1: Ingest last 10 emails (from last 7 days)
echo "========================================"
echo "Testing Manual Email Ingestion"
echo "========================================"
echo ""
echo "Ingesting emails from last 7 days (10080 minutes)..."
echo "This will process approximately the last 10 emails"
echo ""

python scripts/run_ingest.py \
  --url "$DEPLOYMENT_URL" \
  --minutes-since 10080 \
  --email "$EMAIL" \
  --rerun 0 \
  --early 1

echo ""
echo "========================================"
echo "Ingestion Complete!"
echo "========================================"
echo ""
echo "Check LangSmith to see the workflow runs:"
echo "$DEPLOYMENT_URL"
