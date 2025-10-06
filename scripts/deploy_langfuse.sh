#!/bin/bash
#
# LangFuse Deployment Script for Agent Inbox
# Deploys LangFuse to Railway and configures integration
#

set -e  # Exit on error

echo "============================================"
echo " LangFuse Deployment for Agent Inbox"
echo "============================================"
echo

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}Railway CLI not found. Install it:${NC}"
    echo "npm i -g @railway/cli"
    exit 1
fi

if ! command -v npx &> /dev/null; then
    echo -e "${YELLOW}npx not found. Install Node.js first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"
echo

# Step 1: Generate secrets
echo -e "${BLUE}Step 1: Generating secrets...${NC}"
NEXTAUTH_SECRET=$(openssl rand -base64 32)
SALT=$(openssl rand -base64 32)
echo -e "${GREEN}✓ Secrets generated${NC}"
echo

# Step 2: Choose deployment option
echo -e "${BLUE}Step 2: Choose deployment option${NC}"
echo "1) LangFuse Cloud (Quick start, free tier)"
echo "2) Self-hosted on Railway (Full control)"
read -p "Enter choice [1-2]: " choice

case $choice in
    1)
        echo
        echo -e "${GREEN}LangFuse Cloud Selected${NC}"
        echo "1. Go to: https://cloud.langfuse.com"
        echo "2. Sign up and create a new project"
        echo "3. Get your API keys from Settings → API Keys"
        echo
        echo "Enter your LangFuse credentials:"
        read -p "Public Key (pk-lf-...): " LANGFUSE_PUBLIC_KEY
        read -sp "Secret Key (sk-lf-...): " LANGFUSE_SECRET_KEY
        echo
        LANGFUSE_HOST="https://cloud.langfuse.com"
        ;;
    2)
        echo
        echo -e "${GREEN}Railway Self-Hosted Selected${NC}"
        echo "Deploying LangFuse to Railway..."

        cd langfuse-railway

        # Check if already initialized
        if [ ! -f "railway.toml" ]; then
            railway init
        fi

        # Set environment variables
        railway variables set NEXTAUTH_SECRET="$NEXTAUTH_SECRET"
        railway variables set SALT="$SALT"

        # Deploy
        echo "Deploying to Railway..."
        railway up

        # Get the deployment URL
        LANGFUSE_HOST=$(railway domain)

        echo
        echo -e "${GREEN}✓ Deployed to: $LANGFUSE_HOST${NC}"
        echo
        echo "Now:"
        echo "1. Visit $LANGFUSE_HOST"
        echo "2. Sign up and create a project"
        echo "3. Get your API keys from Settings → API Keys"
        echo
        read -p "Public Key (pk-lf-...): " LANGFUSE_PUBLIC_KEY
        read -sp "Secret Key (sk-lf-...): " LANGFUSE_SECRET_KEY
        echo

        cd ..
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

# Step 3: Apply Supabase migration
echo
echo -e "${BLUE}Step 3: Applying Supabase migration...${NC}"
read -p "Enter your Supabase project URL (or press Enter to skip): " SUPABASE_URL

if [ -n "$SUPABASE_URL" ]; then
    npx supabase db push --db-url "$SUPABASE_URL" --file supabase_langfuse_migration.sql
    echo -e "${GREEN}✓ Migration applied${NC}"
else
    echo -e "${YELLOW}⚠ Skipped - Apply manually in Supabase SQL editor${NC}"
fi

# Step 4: Update config
echo
echo -e "${BLUE}Step 4: Updating configuration...${NC}"
echo
echo "Go to your config-app and add these values:"
echo
echo -e "${GREEN}Global Environment → LangFuse (User Tracing):${NC}"
echo "  Public Key: $LANGFUSE_PUBLIC_KEY"
echo "  Secret Key: $LANGFUSE_SECRET_KEY"
echo "  Host URL: $LANGFUSE_HOST"
echo

# Step 5: Deploy updates
echo -e "${BLUE}Step 5: Deploying updated code...${NC}"
echo
read -p "Deploy config API to Railway? [y/N]: " deploy_config
if [[ $deploy_config =~ ^[Yy]$ ]]; then
    cd src/config_api
    git add .
    git commit -m "feat: add LangFuse integration" || true
    git push
    cd ../..
    echo -e "${GREEN}✓ Config API deployed${NC}"
fi

echo
read -p "Deploy executive AI assistant to LangGraph Cloud? [y/N]: " deploy_agent
if [[ $deploy_agent =~ ^[Yy]$ ]]; then
    cd src/executive-ai-assistant
    langgraph deploy
    cd ../..
    echo -e "${GREEN}✓ Agent deployed${NC}"
fi

echo
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN} LangFuse Deployment Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo
echo "Next steps:"
echo "1. Configure LangFuse keys in config-app UI"
echo "2. Test agent invocation"
echo "3. View traces at: $LANGFUSE_HOST"
echo
echo "Documentation: See LANGFUSE_SETUP.md for details"
echo
