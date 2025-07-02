#!/bin/bash

echo "Starting Metasploit RPC daemon..."

# Get configuration from environment or use defaults
MSF_PASSWORD=${MSF_PASSWORD:-"msf"}
MSF_SERVER=${MSF_SERVER:-"127.0.0.1"}
MSF_PORT=${MSF_PORT:-"55553"}

echo "Configuration:"
echo "  Server: $MSF_SERVER"
echo "  Port: $MSF_PORT"
echo "  Password: [hidden]"
echo

# Check if already running
if pgrep -f msfrpcd > /dev/null; then
    echo "⚠️  msfrpcd is already running!"
    echo "   Kill existing process with: pkill -f msfrpcd"
    exit 1
fi

# Start msfrpcd
echo "🚀 Starting msfrpcd..."
msfrpcd -P "$MSF_PASSWORD" -S -a "$MSF_SERVER" -p "$MSF_PORT" &

# Wait a moment for startup
sleep 3

# Check if it started successfully
if pgrep -f msfrpcd > /dev/null; then
    echo "✅ msfrpcd started successfully!"
    echo "   PID: $(pgrep -f msfrpcd)"
    echo "   You can now run: python3 metasploit_mcp_server.py"
else
    echo "❌ Failed to start msfrpcd"
    echo "   Check your Metasploit installation"
    exit 1
fi 