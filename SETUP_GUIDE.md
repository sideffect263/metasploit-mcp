# 🚀 Metasploit MCP Client Setup & Testing Guide

This guide will walk you through setting up and testing the complete Metasploit MCP (Model Context Protocol) system with the Node.js client.

## Prerequisites

Before starting, ensure you have:

- ✅ **Metasploit Framework** installed with `msfrpcd` available
- ✅ **Python 3.8+** with required packages for the MCP server
- ✅ **Node.js 18+** for the client
- ✅ **Windows PowerShell** (if using the PowerShell startup script)

## Step-by-Step Setup

### 1. Install Dependencies

**For Windows (using PowerShell script):**
```powershell
# Run the setup script
.\start-metasploit-client.ps1 setup
```

**Manual setup:**
```bash
# Install Node.js dependencies
cd nodejs-mcp-client
npm install
```

### 2. Start the Services (3 Terminals Required)

You need to start these services in **separate terminals** in this order:

#### Terminal 1: Start Metasploit RPC Daemon
```bash
# Start msfrpcd with your password
msfrpcd -P yourpassword -S -a 127.0.0.1 -p 55553
```
**Expected output:** 
```
[*] MSGRPC starting on 127.0.0.1:55553 (SSL:False)...
[*] MSGRPC ready
```

#### Terminal 2: Start Metasploit MCP Server
```bash
# Navigate to the MCP server directory
cd MetasploitMCP

# Set environment variable (optional, defaults to 'yourpassword')
export MSF_PASSWORD=yourpassword

# Start the MCP server
python MetasploitMCP.py --transport http
```
**Expected output:**
```
[MCP Server] 2024-01-15 10:30:00 - INFO - Starting MCP server in HTTP/SSE transport mode.
[MCP Server] 2024-01-15 10:30:00 - INFO - Successfully connected to Metasploit RPC at 127.0.0.1:55553
[MCP Server] 2024-01-15 10:30:00 - INFO - Starting Uvicorn HTTP server on http://127.0.0.1:8085
```

#### Terminal 3: Test the Node.js Client
```bash
# Navigate to client directory
cd nodejs-mcp-client

# Run connection tests
npm test
```

### 3. Quick Testing Commands

Once all services are running, test with these commands:

```bash
# Basic connection test
npm test

# Interactive mode
npm start interactive

# List exploits
npm start list-exploits --search ms17

# List payloads
npm start list-payloads --platform windows --arch x64

# Check active sessions
npm start list-sessions

# Get server info
npm start info
```

## PowerShell Automation (Windows)

For Windows users, use the provided PowerShell script:

```powershell
# Setup dependencies
.\start-metasploit-client.ps1 setup

# Start services (will guide you through manual steps)
.\start-metasploit-client.ps1 start -MsfPassword yourpassword

# Test connection
.\start-metasploit-client.ps1 test

# Stop services when done
.\start-metasploit-client.ps1 stop
```

## Verification Checklist

Run through this checklist to ensure everything works:

### ✅ **Step 1: Basic Connectivity**
```bash
cd nodejs-mcp-client
npm test
```
**Expected:** All 4 tests pass (Connection, Initialization, Tools List, Basic Operations)

### ✅ **Step 2: List Available Tools**
```bash
npm start info
```
**Expected:** JSON output showing connected: true, initialized: true, and list of available tools

### ✅ **Step 3: Test Core Functions**
```bash
# Test exploit listing
npm start list-exploits --search eternal

# Test payload listing  
npm start list-payloads --platform windows

# Test session listing (should show 0 sessions initially)
npm start list-sessions
```

### ✅ **Step 4: Interactive Mode**
```bash
npm start interactive
```
Try each menu option to ensure they work:
- 📋 List Exploits
- 🎯 List Payloads  
- 💻 List Sessions
- 🎪 List Listeners
- 📊 Server Info

## Common Issues & Solutions

### 🔴 **Issue: "ECONNREFUSED" Error**
**Cause:** MCP server not running or wrong URL
**Solution:**
```bash
# Check if MCP server is running
curl http://127.0.0.1:8085/healthz

# Check server logs for errors
# Restart MCP server if needed
```

### 🔴 **Issue: "Failed to connect to Metasploit RPC"**
**Cause:** msfrpcd not running or wrong password
**Solution:**
```bash
# Check if msfrpcd is running
ps aux | grep msfrpcd

# Restart msfrpcd with correct password
msfrpcd -P yourpassword -S -a 127.0.0.1 -p 55553
```

### 🔴 **Issue: "No tools available"**
**Cause:** MCP server not properly initialized
**Solution:**
```bash
# Check MCP server logs
# Ensure MSF_PASSWORD environment variable matches msfrpcd password
# Restart MCP server
```

### 🔴 **Issue: npm install fails**
**Cause:** Missing Node.js or network issues
**Solution:**
```bash
# Check Node.js version (need 18+)
node --version

# Clear npm cache
npm cache clean --force

# Try installing again
npm install
```

## Test Scenarios

### 📝 **Scenario 1: Information Gathering**
```bash
# List Windows exploits
npm start list-exploits --search windows

# List meterpreter payloads
npm start list-payloads --arch meterpreter

# Check server capabilities
npm start info
```

### 📝 **Scenario 2: Full Workflow Test (Safe)**
```javascript
// Use the basic-usage.js example
node examples/basic-usage.js

// For advanced testing (only on authorized targets!)
node examples/basic-usage.js --advanced
```

### 📝 **Scenario 3: Error Handling Test**
```bash
# Test with invalid module (should handle gracefully)
npm start interactive
# Choose "Run Exploit" and enter invalid module name
```

## Performance Benchmarks

Expected response times (on local machine):
- ✅ Connection establishment: < 2 seconds
- ✅ List exploits (no filter): < 5 seconds  
- ✅ List payloads (with filter): < 3 seconds
- ✅ Server info: < 1 second

## Security Notes

⚠️ **IMPORTANT SECURITY WARNINGS:**

1. **Only run against authorized targets**
2. **Use strong passwords for msfrpcd**
3. **Don't expose MCP server to untrusted networks**
4. **Monitor all activities for security compliance**

## Next Steps

Once basic testing passes:

1. **Try payload generation** (creates files on server)
2. **Test handler management** (starts background jobs)
3. **Explore post-exploitation modules** (requires active sessions)
4. **Build custom workflows** using the API

## Support

If you encounter issues:

1. **Check logs** in all three terminals
2. **Verify network connectivity** between components
3. **Ensure all passwords match** across services
4. **Review the troubleshooting section** in the main README

---

**🎯 You're ready to go!** The Node.js MCP client provides a powerful interface to Metasploit through the MCP protocol. Happy testing! 🚀 