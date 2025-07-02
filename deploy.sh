#!/bin/bash

echo "🚀 Deploying Metasploit MCP Server to Digital Ocean Droplet"
echo "============================================================"

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
sudo apt install -y python3 python3-pip nginx ufw curl git

# Install Metasploit Framework if not present
if ! command -v msfconsole &> /dev/null; then
    echo "📦 Installing Metasploit Framework..."
    curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall
    chmod 755 msfinstall
    sudo ./msfinstall
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Set up directory structure
echo "📁 Setting up directory structure..."
sudo mkdir -p /opt/metasploit-mcp
sudo mkdir -p /var/www/metasploit-mcp
sudo cp * /opt/metasploit-mcp/
sudo cp index.html /var/www/metasploit-mcp/

# Set permissions
sudo chown -R $USER:$USER /opt/metasploit-mcp
sudo chown -R www-data:www-data /var/www/metasploit-mcp

# Configure nginx
echo "🌐 Configuring nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/metasploit-mcp
sudo ln -sf /etc/nginx/sites-available/metasploit-mcp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Set up systemd service for MCP server
echo "⚙️ Setting up systemd service..."
sudo cp metasploit-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw allow 55553/tcp  # MSF RPC port
sudo ufw --force enable

# Set environment variables
echo "🔧 Setting up environment variables..."
sudo tee /etc/environment > /dev/null <<EOF
MSF_PASSWORD=msf123!@#
MSF_SERVER=127.0.0.1
MSF_PORT=55553
MSF_SSL=false
EOF

# Create MSF RPC startup script
echo "🚀 Creating MSF RPC startup script..."
sudo tee /opt/metasploit-mcp/start_msfrpcd.sh > /dev/null <<'EOF'
#!/bin/bash
export MSF_PASSWORD=msf123!@#
msfrpcd -P $MSF_PASSWORD -S -a 127.0.0.1 -p 55553 -f
EOF

sudo chmod +x /opt/metasploit-mcp/start_msfrpcd.sh

# Start services
echo "🔄 Starting services..."
sudo systemctl restart nginx
sudo systemctl enable nginx

# Start MSF RPC daemon
echo "🚀 Starting Metasploit RPC daemon..."
cd /opt/metasploit-mcp
sudo -u $USER bash start_msfrpcd.sh &

# Wait a moment for MSF RPC to start
sleep 5

# Start MCP server
echo "🚀 Starting MCP server..."
sudo systemctl start metasploit-mcp
sudo systemctl enable metasploit-mcp

# Get server IP
SERVER_IP=$(curl -s https://api.ipify.org)

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo "🌐 Landing Page: http://$SERVER_IP"
echo "🔧 MCP Server: Running on localhost:stdio"
echo "🛡️ MSF RPC: Running on localhost:55553"
echo ""
echo "📋 Next Steps:"
echo "1. Visit http://$SERVER_IP to see your landing page"
echo "2. Configure your MCP client to connect to this server"
echo "3. Check service status: sudo systemctl status metasploit-mcp"
echo "4. View logs: sudo journalctl -u metasploit-mcp -f"
echo ""
echo "🔒 Security Notes:"
echo "- Default MSF password is 'msf123!@#' (change this!)"
echo "- MSF RPC only listens on localhost for security"
echo "- Firewall is configured to allow only necessary ports" 