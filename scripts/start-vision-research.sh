#!/bin/bash
# Start research API with vision (ngrok + API)

set -e

echo "🔧 Starting Vision Research Setup..."

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok not found. Install: brew install ngrok"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    # Export each variable individually to avoid issues with comments
    while IFS='=' read -r key value; do
        # Skip empty lines and comments
        [[ -z "$key" || "$key" =~ ^# ]] && continue
        # Remove inline comments and whitespace
        value=$(echo "$value" | sed 's/#.*//' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        # Export the variable
        export "$key=$value"
    done < .env
fi

# Configure ngrok authtoken if provided in .env
if [ -n "$NGROK_AUTHTOKEN" ] && [ "$NGROK_AUTHTOKEN" != "your-ngrok-authtoken-here" ]; then
    echo "🔑 Configuring ngrok with authtoken from .env..."
    ngrok config add-authtoken "$NGROK_AUTHTOKEN" 2>&1 | grep -v "Authtoken saved" || true
    echo "✅ Ngrok configured"
else
    echo "⚠️  No NGROK_AUTHTOKEN in .env - checking if ngrok already configured..."
    if ! ngrok config check &> /dev/null; then
        echo ""
        echo "❌ Ngrok not configured!"
        echo ""
        echo "Please add your ngrok authtoken to .env:"
        echo "  1. Get free authtoken: https://dashboard.ngrok.com/get-started/your-authtoken"
        echo "  2. Edit .env and set: NGROK_AUTHTOKEN=your-actual-token"
        echo "  3. Run this script again"
        echo ""
        exit 1
    fi
fi

# Check if ngrok is already running
if pgrep -f "ngrok http 8002" > /dev/null; then
    echo "✅ Ngrok already running"
else
    echo "🚀 Starting ngrok tunnel to worker API (port 8002)..."
    nohup ngrok http 8002 > logs/ngrok.log 2>&1 &
    sleep 3
fi

# Get ngrok URL from API
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')

if [ -z "$NGROK_URL" ] || [ "$NGROK_URL" = "null" ]; then
    echo "❌ Failed to get ngrok URL"
    exit 1
fi

echo "✅ Ngrok URL: $NGROK_URL"

# Update .env with ngrok URL
if grep -q "^NGROK_URL=" .env; then
    # Update existing line (macOS compatible)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^NGROK_URL=.*|NGROK_URL=$NGROK_URL|" .env
    else
        sed -i "s|^NGROK_URL=.*|NGROK_URL=$NGROK_URL|" .env
    fi
else
    echo "NGROK_URL=$NGROK_URL" >> .env
fi

# Enable vision
if grep -q "^RESEARCH_VISION_ENABLED=" .env; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^RESEARCH_VISION_ENABLED=.*|RESEARCH_VISION_ENABLED=true|" .env
    else
        sed -i "s|^RESEARCH_VISION_ENABLED=.*|RESEARCH_VISION_ENABLED=true|" .env
    fi
else
    echo "RESEARCH_VISION_ENABLED=true" >> .env
fi

echo "✅ Updated .env with ngrok URL"

# Start research API
echo "🚀 Starting research API..."
./scripts/start-research-api.sh

echo ""
echo ""
echo "✅ Vision research ready!"
echo "   Ngrok URL: $NGROK_URL (tunnels to worker API on port 8002)"
echo "   Research API: http://localhost:8004"
echo "   Logs: logs/research-api.log, logs/ngrok.log"
echo ""
echo "   Images are accessible via: $NGROK_URL/images/{doc_id}/{filename}"
