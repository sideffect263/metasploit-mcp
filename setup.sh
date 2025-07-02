#!/bin/bash

echo "=== Simplified Metasploit MCP Server Setup ==="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if Metasploit is installed
if ! command -v msfconsole &> /dev/null; then
    echo "❌ Metasploit Framework not found. Please install Metasploit first."
    echo "   Visit: https://docs.metasploit.com/docs/using-metasploit/getting-started/nightly-installers.html"
    exit 1
fi

echo "✅ Metasploit Framework found"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Set default environment variables
echo "🔧 Setting up environment..."
echo "export MSF_PASSWORD='msf'" >> ~/.bashrc
echo "export MSF_SERVER='127.0.0.1'" >> ~/.bashrc  
echo "export MSF_PORT='55553'" >> ~/.bashrc
echo "export MSF_SSL='false'" >> ~/.bashrc

echo "✅ Environment variables added to ~/.bashrc"

# Check if msfrpcd is running
echo "🔍 Checking if msfrpcd is running..."
if pgrep -f msfrpcd > /dev/null; then
    echo "✅ msfrpcd is already running"
else
    echo "⚠️  msfrpcd is not running"
    echo "   Start it with: msfrpcd -P msf -S -a 127.0.0.1 -p 55553"
    echo "   Or run: ./start_msfrpcd.sh"
fi

echo
echo "🎉 Setup complete!"
echo
echo "Next steps:"
echo "1. Source your environment: source ~/.bashrc"
echo "2. Start msfrpcd if not running: msfrpcd -P msf -S -a 127.0.0.1 -p 55553"
echo "3. Run the server: python3 metasploit_mcp_server.py"
echo
echo "For more information, see README.md" 