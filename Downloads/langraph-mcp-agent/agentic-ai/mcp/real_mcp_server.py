"""
Real MCP Server Implementation
==============================
This is how you would implement an actual MCP server for production.

To run this server:
    pip install mcp
    python -m mcp.real_mcp_server

The server communicates via JSON-RPC over stdio with MCP clients.
"""

import asyncio
import json
from typing import Any, Dict, Optional
from datetime import datetime

# ============================================================================
# OPTION 1: Using Official MCP SDK (Recommended for Production)
# ============================================================================

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_SDK_AVAILABLE = True
except ImportError:
    MCP_SDK_AVAILABLE = False
    print("MCP SDK not installed. Run: pip install mcp")


# Mock data (same as our tools.py)
SANCTIONS_DATABASE = {
    "companies": {
        "EVIL CORP": {"listed": True, "source": "OFAC", "date": "2023-01-15"},
    },
    "countries": {
        "IR": {"sanctioned": True, "level": "comprehensive", "source": "OFAC"},
        "KP": {"sanctioned": True, "level": "comprehensive", "source": "OFAC"},
    }
}


if MCP_SDK_AVAILABLE:
    # Create the MCP server
    server = Server("risk-intelligence-server")
    
    # ========================================
    # Define Tools using MCP Protocol
    # ========================================
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """
        MCP Protocol: List available tools.
        Called by clients to discover what tools this server offers.
        """
        return [
            Tool(
                name="check_sanctions",
                description="Check if a company or country is on OFAC/EU/UN sanctions lists",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "string",
                            "description": "Company name to check"
                        },
                        "country": {
                            "type": "string",
                            "description": "ISO country code (e.g., 'IR', 'US')"
                        }
                    },
                    "required": ["company"]
                }
            ),
            Tool(
                name="detect_anomalies",
                description="Detect statistical anomalies in transaction data",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "number",
                            "description": "Transaction value"
                        },
                        "country": {
                            "type": "string",
                            "description": "Transaction country"
                        },
                        "company": {
                            "type": "string",
                            "description": "Company name"
                        }
                    },
                    "required": ["value"]
                }
            ),
            Tool(
                name="search_similar_cases",
                description="Find similar historical risk cases",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company": {"type": "string"},
                        "country": {"type": "string"},
                        "value": {"type": "number"}
                    },
                    "required": ["company", "country", "value"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """
        MCP Protocol: Execute a tool.
        Called by clients to run a specific tool with arguments.
        """
        if name == "check_sanctions":
            result = await check_sanctions_impl(
                company=arguments.get("company", ""),
                country=arguments.get("country")
            )
        elif name == "detect_anomalies":
            result = await detect_anomalies_impl(
                value=arguments.get("value", 0),
                country=arguments.get("country", ""),
                company=arguments.get("company", "")
            )
        elif name == "search_similar_cases":
            result = await search_similar_impl(
                company=arguments.get("company", ""),
                country=arguments.get("country", ""),
                value=arguments.get("value", 0)
            )
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    # ========================================
    # Tool Implementations
    # ========================================
    
    async def check_sanctions_impl(company: str, country: Optional[str]) -> Dict:
        """Actual sanctions check logic."""
        result = {
            "timestamp": datetime.now().isoformat(),
            "company_hit": False,
            "country_hit": False,
            "sources": []
        }
        
        # Check company
        company_upper = company.upper()
        for sanctioned, details in SANCTIONS_DATABASE["companies"].items():
            if sanctioned in company_upper:
                result["company_hit"] = True
                result["sources"].append({"type": "company", "source": details["source"]})
        
        # Check country
        if country and country.upper() in SANCTIONS_DATABASE["countries"]:
            result["country_hit"] = True
            info = SANCTIONS_DATABASE["countries"][country.upper()]
            result["sources"].append({"type": "country", "source": info["source"]})
        
        result["hit"] = result["company_hit"] or result["country_hit"]
        return result
    
    async def detect_anomalies_impl(value: float, country: str, company: str) -> Dict:
        """Anomaly detection logic."""
        avg = 250000
        std = 150000
        z_score = (value - avg) / std
        
        return {
            "timestamp": datetime.now().isoformat(),
            "anomaly_score": min(abs(z_score) / 5, 1.0),
            "is_anomalous": abs(z_score) > 2,
            "z_score": z_score
        }
    
    async def search_similar_impl(company: str, country: str, value: float) -> Dict:
        """Similar case search logic."""
        # In production, this would query a vector database
        return {
            "timestamp": datetime.now().isoformat(),
            "matches": [],
            "highest_similarity": 0.0
        }
    
    # ========================================
    # Server Entry Point
    # ========================================
    
    async def main():
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream)
    
    if __name__ == "__main__":
        asyncio.run(main())


# ============================================================================
# OPTION 2: Manual JSON-RPC Implementation (Educational)
# ============================================================================

class ManualMCPServer:
    """
    Manual implementation showing MCP protocol structure.
    This is what the SDK does under the hood.
    """
    
    def __init__(self):
        self.tools = {
            "check_sanctions": self._check_sanctions,
            "detect_anomalies": self._detect_anomalies,
        }
    
    async def handle_request(self, request: Dict) -> Dict:
        """
        Handle incoming JSON-RPC request.
        
        MCP uses JSON-RPC 2.0 format:
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "check_sanctions", "arguments": {...}}
        }
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "tools/list":
                # Client wants to know what tools are available
                result = self._list_tools()
            
            elif method == "tools/call":
                # Client wants to execute a tool
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await self._call_tool(tool_name, arguments)
            
            elif method == "initialize":
                # Handshake when client connects
                result = {
                    "protocolVersion": "0.1.0",
                    "serverInfo": {
                        "name": "risk-intelligence-server",
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "tools": {}
                    }
                }
            
            else:
                return self._error_response(request_id, -32601, f"Unknown method: {method}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            return self._error_response(request_id, -32603, str(e))
    
    def _list_tools(self) -> Dict:
        """Return tool definitions in MCP format."""
        return {
            "tools": [
                {
                    "name": "check_sanctions",
                    "description": "Check sanctions lists",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "company": {"type": "string"},
                            "country": {"type": "string"}
                        }
                    }
                },
                {
                    "name": "detect_anomalies",
                    "description": "Statistical anomaly detection",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "number"},
                            "country": {"type": "string"}
                        }
                    }
                }
            ]
        }
    
    async def _call_tool(self, name: str, arguments: Dict) -> Dict:
        """Execute a tool by name."""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        
        result = await self.tools[name](**arguments)
        
        return {
            "content": [
                {"type": "text", "text": json.dumps(result)}
            ]
        }
    
    async def _check_sanctions(self, company: str, country: str = None) -> Dict:
        # Same implementation as above
        return {"hit": False, "source": "OFAC"}
    
    async def _detect_anomalies(self, value: float, country: str = "") -> Dict:
        return {"anomaly_score": 0.5, "is_anomalous": False}
    
    def _error_response(self, request_id: Any, code: int, message: str) -> Dict:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message}
        }


# ============================================================================
# Example: How to connect from a client
# ============================================================================

"""
To use this MCP server with Claude or other MCP clients:

1. Install the MCP SDK:
   pip install mcp

2. Run the server:
   python real_mcp_server.py

3. Configure in claude_desktop_config.json:
   {
     "mcpServers": {
       "risk-intelligence": {
         "command": "python",
         "args": ["/path/to/real_mcp_server.py"]
       }
     }
   }

4. Claude can now use your tools:
   "Please check if ABC Corp in Iran is sanctioned"
   → Claude calls check_sanctions tool via MCP
   → Server returns structured result
   → Claude interprets and responds

Protocol flow:
   Client                          Server
     │                               │
     │──── initialize ──────────────▶│
     │◀─── capabilities ─────────────│
     │                               │
     │──── tools/list ──────────────▶│
     │◀─── [check_sanctions, ...] ───│
     │                               │
     │──── tools/call ──────────────▶│
     │     {name: "check_sanctions", │
     │      arguments: {...}}        │
     │◀─── {hit: true, ...} ─────────│
     │                               │
"""
