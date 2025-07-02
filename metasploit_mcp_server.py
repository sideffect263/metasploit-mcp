#!/usr/bin/env python3
"""
Simplified Metasploit MCP Server
A clean, easy-to-use MCP server providing comprehensive Metasploit functionality.
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Metasploit imports
try:
    from pymetasploit3.msfrpc import MsfRpcClient, MsfRpcError
except ImportError:
    print("Error: pymetasploit3 not installed. Install with: pip install pymetasploit3")
    sys.exit(1)

# Configure logging to stderr instead of stdout to avoid JSON-RPC pollution
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # This is the key fix!
)
logger = logging.getLogger("metasploit-mcp")

# Configuration
MSF_PASSWORD = os.environ.get('MSF_PASSWORD', 'yourpassword')
MSF_SERVER = os.environ.get('MSF_SERVER', '127.0.0.1')
MSF_PORT = int(os.environ.get('MSF_PORT', '55553'))
MSF_SSL = os.environ.get('MSF_SSL', 'false').lower() == 'true'

# Global client instance
msf_client: Optional[MsfRpcClient] = None

def get_msf_client() -> MsfRpcClient:
    """Get or create MSF RPC client"""
    global msf_client
    if msf_client is None:
        try:
            msf_client = MsfRpcClient(
                password=MSF_PASSWORD,
                server=MSF_SERVER,
                port=MSF_PORT,
                ssl=MSF_SSL
            )
            logger.info(f"Connected to Metasploit at {MSF_SERVER}:{MSF_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Metasploit: {e}")
            raise
    return msf_client

# Initialize MCP server
server = Server("metasploit-mcp")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available Metasploit tools"""
    return [
        Tool(
            name="list_exploits",
            description="List available Metasploit exploits with optional search filter",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Optional search term to filter exploits"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="list_payloads",
            description="List available Metasploit payloads with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": "Filter by platform (windows, linux, etc.)"
                    },
                    "arch": {
                        "type": "string", 
                        "description": "Filter by architecture (x86, x64, etc.)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="get_exploit_info",
            description="Get detailed information about a specific exploit",
            inputSchema={
                "type": "object",
                "properties": {
                    "exploit_name": {
                        "type": "string",
                        "description": "Name of the exploit (e.g., 'windows/smb/ms17_010_eternalblue')"
                    }
                },
                "required": ["exploit_name"]
            }
        ),
        Tool(
            name="run_exploit",
            description="Execute a Metasploit exploit module",
            inputSchema={
                "type": "object",
                "properties": {
                    "exploit_name": {
                        "type": "string",
                        "description": "Name of the exploit module"
                    },
                    "target": {
                        "type": "string",
                        "description": "Target host/IP address"
                    },
                    "payload": {
                        "type": "string",
                        "description": "Payload to use (e.g., 'windows/meterpreter/reverse_tcp')"
                    },
                    "lhost": {
                        "type": "string",
                        "description": "Local host for reverse connections"
                    },
                    "lport": {
                        "type": "integer",
                        "description": "Local port for reverse connections"
                    },
                    "options": {
                        "type": "object",
                        "description": "Additional exploit options"
                    }
                },
                "required": ["exploit_name", "target", "payload", "lhost", "lport"]
            }
        ),
        Tool(
            name="run_auxiliary",
            description="Execute a Metasploit auxiliary module (scanners, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "description": "Name of the auxiliary module"
                    },
                    "options": {
                        "type": "object",
                        "description": "Module options (e.g., RHOSTS, RPORT)"
                    }
                },
                "required": ["module_name", "options"]
            }
        ),
        Tool(
            name="list_sessions",
            description="List all active Metasploit sessions",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="interact_session",
            description="Send commands to an active session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "integer",
                        "description": "ID of the session to interact with"
                    },
                    "command": {
                        "type": "string",
                        "description": "Command to execute in the session"
                    }
                },
                "required": ["session_id", "command"]
            }
        ),
        Tool(
            name="generate_payload",
            description="Generate a Metasploit payload",
            inputSchema={
                "type": "object",
                "properties": {
                    "payload_type": {
                        "type": "string",
                        "description": "Type of payload (e.g., 'windows/meterpreter/reverse_tcp')"
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format (exe, raw, python, etc.)",
                        "default": "exe"
                    },
                    "lhost": {
                        "type": "string",
                        "description": "Local host for connections"
                    },
                    "lport": {
                        "type": "integer",
                        "description": "Local port for connections"
                    },
                    "options": {
                        "type": "object",
                        "description": "Additional payload options"
                    }
                },
                "required": ["payload_type", "lhost", "lport"]
            }
        ),
        Tool(
            name="start_handler",
            description="Start a payload handler (listener)",
            inputSchema={
                "type": "object",
                "properties": {
                    "payload_type": {
                        "type": "string",
                        "description": "Payload type to handle"
                    },
                    "lhost": {
                        "type": "string",
                        "description": "Local host to listen on"
                    },
                    "lport": {
                        "type": "integer",
                        "description": "Local port to listen on"
                    },
                    "options": {
                        "type": "object",
                        "description": "Additional handler options"
                    }
                },
                "required": ["payload_type", "lhost", "lport"]
            }
        ),
        Tool(
            name="list_jobs",
            description="List active Metasploit jobs",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="stop_job",
            description="Stop a running job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "integer",
                        "description": "ID of the job to stop"
                    }
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="run_post_module",
            description="Run a post-exploitation module on a session",
            inputSchema={
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "description": "Name of the post module"
                    },
                    "session_id": {
                        "type": "integer",
                        "description": "Target session ID"
                    },
                    "options": {
                        "type": "object",
                        "description": "Additional module options"
                    }
                },
                "required": ["module_name", "session_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool execution with timeout"""
    try:
        # Add timeout to prevent hanging
        timeout = 30  # 30 second timeout
        
        client = get_msf_client()
        
        if name == "list_exploits":
            result = await asyncio.wait_for(list_exploits(client, arguments), timeout=timeout)
        elif name == "list_payloads":
            result = await asyncio.wait_for(list_payloads(client, arguments), timeout=timeout)
        elif name == "get_exploit_info":
            result = await asyncio.wait_for(get_exploit_info(client, arguments), timeout=timeout)
        elif name == "run_exploit":
            result = await asyncio.wait_for(run_exploit(client, arguments), timeout=timeout)
        elif name == "run_auxiliary":
            result = await asyncio.wait_for(run_auxiliary(client, arguments), timeout=timeout)
        elif name == "list_sessions":
            result = await asyncio.wait_for(list_sessions(client, arguments), timeout=timeout)
        elif name == "interact_session":
            result = await asyncio.wait_for(interact_session(client, arguments), timeout=timeout)
        elif name == "generate_payload":
            result = await asyncio.wait_for(generate_payload(client, arguments), timeout=timeout)
        elif name == "start_handler":
            result = await asyncio.wait_for(start_handler(client, arguments), timeout=timeout)
        elif name == "list_jobs":
            result = await asyncio.wait_for(list_jobs(client, arguments), timeout=timeout)
        elif name == "stop_job":
            result = await asyncio.wait_for(stop_job(client, arguments), timeout=timeout)
        elif name == "run_post_module":
            result = await asyncio.wait_for(run_post_module(client, arguments), timeout=timeout)
        else:
            result = [TextContent(type="text", text=f"Unknown tool: {name}")]
            
        return result
            
    except asyncio.TimeoutError:
        logger.error(f"Tool {name} timed out after {timeout} seconds")
        return [TextContent(type="text", text=f"Error: Tool {name} timed out after {timeout} seconds")]
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

# Tool implementations
async def list_exploits(client: MsfRpcClient, args: Dict[str, Any]) -> List[TextContent]:
    """List available exploits"""
    search_term = args.get("search", "")
    limit = args.get("limit", 50)
    
    try:
        # Run synchronous Metasploit operation in thread pool
        def _get_exploits():
            exploits = client.modules.exploits
            if search_term:
                exploits = [e for e in exploits if search_term.lower() in e.lower()]
            return exploits[:limit]
        
        exploits = await asyncio.to_thread(_get_exploits)
        
        result = {
            "total_found": len(exploits),
            "exploits": exploits,
            "search_term": search_term if search_term else "none"
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing exploits: {e}")]

async def list_payloads(client: MsfRpcClient, args: Dict[str, Any]) -> List[TextContent]:
    """List available payloads"""
    platform = args.get("platform", "")
    arch = args.get("arch", "")
    limit = args.get("limit", 50)
    
    try:
        # Run synchronous Metasploit operation in thread pool
        def _get_payloads():
            payloads = client.modules.payloads
            
            if platform:
                payloads = [p for p in payloads if platform.lower() in p.lower()]
            if arch:
                payloads = [p for p in payloads if arch.lower() in p.lower()]
                
            return payloads[:limit]
        
        payloads = await asyncio.to_thread(_get_payloads)
        
        result = {
            "total_found": len(payloads),
            "payloads": payloads,
            "filters": {"platform": platform, "arch": arch}
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing payloads: {e}")]

async def get_exploit_info(client: MsfRpcClient, args: Dict[str, Any]) -> List[TextContent]:
    """Get detailed exploit information"""
    exploit_name = args["exploit_name"]
    
    try:
        # Run synchronous Metasploit operation in thread pool
        def _get_exploit_info():
            # Get exploit module
            exploit = client.modules.use('exploit', exploit_name)
            
            # Get module info
            info = {
                "name": exploit_name,
                "description": getattr(exploit, 'description', 'No description available'),
                "targets": getattr(exploit, 'targets', []),
                "options": {},
                "payloads": getattr(exploit, 'payloads', [])
            }
            
            # Get options
            try:
                options = exploit.options
                for opt_name, opt_info in options.items():
                    info["options"][opt_name] = {
                        "required": opt_info.get('required', False),
                        "default": opt_info.get('default', ''),
                        "description": opt_info.get('desc', '')
                    }
            except:
                pass
                
            return info
        
        info = await asyncio.to_thread(_get_exploit_info)
        return [TextContent(type="text", text=json.dumps(info, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting exploit info: {e}")]

async def run_exploit(client: MsfRpcClient, args: Dict[str, Any]) -> List[TextContent]:
    """Execute an exploit"""
    exploit_name = args["exploit_name"]
    target = args["target"]
    payload_name = args["payload"]
    lhost = args["lhost"]
    lport = args["lport"]
    options = args.get("options", {})
    
    try:
        # Run synchronous Metasploit operation in thread pool
        def _execute_exploit():
            # Get exploit module
            exploit = client.modules.use('exploit', exploit_name)
            
            # Set basic options (conditional based on exploit type)
            if exploit_name != "multi/handler":  # Handlers don't use RHOSTS
                exploit['RHOSTS'] = target
            
            exploit['LHOST'] = lhost
            exploit['LPORT'] = lport
            
            # Set additional options
            for key, value in options.items():
                exploit[key] = value
                
            # Set payload
            payload = client.modules.use('payload', payload_name)
            payload['LHOST'] = lhost
            payload['LPORT'] = lport
            
            # Execute exploit
            job_id = exploit.execute(payload=payload)
            return job_id
        
        # Execute in thread pool
        job_id = await asyncio.to_thread(_execute_exploit)
        
        # Simple result without session checking (which was causing the hang)
        result = {
            "status": "success",
            "job_id": job_id,
            "exploit": exploit_name,
            "target": target,
            "payload": payload_name,
            "note": "Check sessions separately using list_sessions"
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error running exploit: {e}")]

async def run_auxiliary(client: MsfRpcClient, args: Dict[str, Any]) -> List[TextContent]:
    """Run auxiliary module"""
    module_name = args["module_name"]
    options = args["options"]
    
    try:
        # Run synchronous Metasploit operation in thread pool
        def _execute_auxiliary():
            # Get auxiliary module
            aux = client.modules.use('auxiliary', module_name)
            
            # Set options
            for key, value in options.items():
                aux[key] = value
                
            # Execute module
            job_id = aux.execute()
            return job_id
        
        job_id = await asyncio.to_thread(_execute_auxiliary)
        
        result = {
            "status": "success",
            "job_id": job_id,
            "module": module_name,
            "options": options
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error running auxiliary module: {e}")]

async def list_sessions(client: MsfRpcClient, args: Dict[str, Any]) -> List[TextContent]:
    """List active sessions"""
    try:
        # Run synchronous operation in thread pool
        def _get_sessions():
            return client.sessions.list
        
        sessions = await asyncio.to_thread(_get_sessions)
        
        result = {
            "active_sessions": len(sessions),
            "sessions": sessions
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing sessions: {e}")]

async def interact_session(client: MsfRpcClient, args: Dict[str, Any]) -> List[TextContent]:
    """Interact with a session"""
    session_id = str(args["session_id"])
    command = args["command"]
    
    try:
        # Get session
        session = client.sessions.session(session_id)
        
        # Execute command
        session.write(command)
        
        # Wait for output
        await asyncio.sleep(2)
        
        # Read output
        output = session.read()
        
        result = {
            "session_id": session_id,
            "command": command,
            "output": output
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error interacting with session: {e}")]

async def generate_payload(client: MsfRpcClient, args: Dict[str, Any]) -> List[TextContent]:
    """Generate a payload"""
    payload_type = args["payload_type"]
    format_type = args.get("format", "exe")
    lhost = args["lhost"]
    lport = args["lport"]
    options = args.get("options", {})
    
    try:
        # Run synchronous Metasploit operation in thread pool
        def _generate_payload():
            # Get payload module
            payload = client.modules.use('payload', payload_type)
            
            # Set options
            payload['LHOST'] = lhost
            payload['LPORT'] = lport
            
            for key, value in options.items():
                payload[key] = value
                
            # Generate payload
            payload_data = payload.payload_generate(fmt=format_type)
            return payload_data
        
        payload_data = await asyncio.to_thread(_generate_payload)
        
        # Save to file
        import base64
        import os
        filename = f"payload_{int(time.time())}.{format_type}"
        filepath = os.path.join("/tmp", filename)
        
        with open(filepath, "wb") as f:
            if isinstance(payload_data, str):
                f.write(payload_data.encode())
            else:
                f.write(payload_data)
        
        result = {
            "status": "success",
            "payload_type": payload_type,
            "format": format_type,
            "size": len(payload_data),
            "saved_to": filepath
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error generating payload: {e}")]

async def start_handler(client: MsfRpcClient, args: Dict[str, Any]) -> List[TextContent]:
    """Start a payload handler"""
    payload_type = args["payload_type"]
    lhost = args["lhost"]
    lport = args["lport"]
    options = args.get("options", {})
    
    try:
        # Run synchronous Metasploit operation in thread pool
        def _start_handler():
            # Use multi/handler exploit
            handler = client.modules.use('exploit', 'multi/handler')
            
            # Set payload
            payload = client.modules.use('payload', payload_type)
            payload['LHOST'] = lhost
            payload['LPORT'] = lport
            
            # Set handler options
            for key, value in options.items():
                handler[key] = value
                
            # Start handler
            job_id = handler.execute(payload=payload)
            return job_id
        
        job_id = await asyncio.to_thread(_start_handler)
        
        result = {
            "status": "success",
            "job_id": job_id,
            "payload_type": payload_type,
            "lhost": lhost,
            "lport": lport
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error starting handler: {e}")]

async def list_jobs(client: MsfRpcClient, args: Dict[str, Any]) -> List[TextContent]:
    """List active jobs"""
    try:
        # Run synchronous operation in thread pool
        def _get_jobs():
            return client.jobs.list
        
        jobs = await asyncio.to_thread(_get_jobs)
        
        result = {
            "active_jobs": len(jobs),
            "jobs": jobs
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing jobs: {e}")]

async def stop_job(client: MsfRpcClient, args: Dict[str, Any]) -> List[TextContent]:
    """Stop a job"""
    job_id = str(args["job_id"])
    
    try:
        result = client.jobs.stop(job_id)
        
        response = {
            "status": "success",
            "job_id": job_id,
            "result": result
        }
        
        return [TextContent(type="text", text=json.dumps(response, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error stopping job: {e}")]

async def run_post_module(client: MsfRpcClient, args: Dict[str, Any]) -> List[TextContent]:
    """Run post-exploitation module"""
    module_name = args["module_name"]
    session_id = args["session_id"]
    options = args.get("options", {})
    
    try:
        # Get post module
        post = client.modules.use('post', module_name)
        
        # Set session
        post['SESSION'] = session_id
        
        # Set additional options
        for key, value in options.items():
            post[key] = value
            
        # Execute module
        job_id = post.execute()
        
        result = {
            "status": "success",
            "job_id": job_id,
            "module": module_name,
            "session_id": session_id
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error running post module: {e}")]

async def main():
    """Main entry point"""
    # Test MSF connection
    try:
        client = get_msf_client()
        logger.info("Successfully connected to Metasploit")
    except Exception as e:
        logger.error(f"Failed to connect to Metasploit: {e}")
        sys.exit(1)
    
    # Run MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="metasploit-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 