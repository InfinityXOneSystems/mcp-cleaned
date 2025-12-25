"""
Extended MCP Server with GitHub Integration
Combines orchestrator forwarding with GitHub MCP tools
"""
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx
import os
import sqlite3
import json
import subprocess
from typing import Optional

ORCHESTRATOR_URL = os.getenv(
    "ORCHESTRATOR_URL",
    "https://orchestrator-896380409704.us-east1.run.app/execute"
)

DB_PATH = 'mcp_memory.db'

server = Server("infinity-xos-mcp-omni-hub")

# ===== TOOL DEFINITIONS =====
TOOLS = [
    Tool(
        name="execute",
        description="Forward command to Infinity XOS Orchestrator",
        inputSchema={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "payload": {"type": "object"}
            },
            "required": ["command"]
        }
    ),
    Tool(
        name="github_create_issue",
        description="Create a GitHub issue in the specified repository",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body"},
                "labels": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["owner", "repo", "title", "body"]
        }
    ),
    Tool(
        name="github_search_code",
        description="Search for code across GitHub repositories",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "max_results": {"type": "integer", "default": 10}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="github_get_file_content",
        description="Get the content of a file from a GitHub repository",
        inputSchema={
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "path": {"type": "string"},
                "branch": {"type": "string", "default": "main"}
            },
            "required": ["owner", "repo", "path"]
        }
    ),
    Tool(
        name="query_intelligence",
        description="Query intelligence sources from local memory database",
        inputSchema={
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "search": {"type": "string"},
                "limit": {"type": "integer", "default": 10}
            }
        }
    ),
    Tool(
        name="get_portfolio_status",
        description="Get current trading portfolio status",
        inputSchema={"type": "object", "properties": {}}
    ),
    # Docker Tools
    Tool(
        name="docker_list_containers",
        description="List Docker containers (running or all)",
        inputSchema={
            "type": "object",
            "properties": {
                "all": {"type": "boolean", "default": False, "description": "Include stopped containers"}
            }
        }
    ),
    Tool(
        name="docker_container_action",
        description="Control Docker containers (start/stop/restart/remove)",
        inputSchema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["start", "stop", "restart", "remove"], "description": "Action to perform"},
                "container": {"type": "string", "description": "Container name or ID"}
            },
            "required": ["action", "container"]
        }
    ),
    Tool(
        name="docker_run_container",
        description="Run a new Docker container",
        inputSchema={
            "type": "object",
            "properties": {
                "image": {"type": "string", "description": "Image name"},
                "name": {"type": "string", "description": "Container name"},
                "ports": {"type": "object", "description": "Port mappings {container_port: host_port}"},
                "environment": {"type": "object", "description": "Environment variables"},
                "detach": {"type": "boolean", "default": True}
            },
            "required": ["image"]
        }
    ),
    Tool(
        name="docker_list_images",
        description="List Docker images",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="docker_pull_image",
        description="Pull a Docker image from registry",
        inputSchema={
            "type": "object",
            "properties": {
                "image": {"type": "string", "description": "Image name with optional tag"}
            },
            "required": ["image"]
        }
    ),
    Tool(
        name="docker_container_logs",
        description="Get container logs",
        inputSchema={
            "type": "object",
            "properties": {
                "container": {"type": "string", "description": "Container name or ID"},
                "tail": {"type": "integer", "default": 100, "description": "Number of lines to show"}
            },
            "required": ["container"]
        }
    ),
    Tool(
        name="docker_container_inspect",
        description="Inspect container details",
        inputSchema={
            "type": "object",
            "properties": {
                "container": {"type": "string", "description": "Container name or ID"}
            },
            "required": ["container"]
        }
    ),
    Tool(
        name="docker_list_networks",
        description="List Docker networks",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="docker_list_volumes",
        description="List Docker volumes",
        inputSchema={"type": "object", "properties": {}}
    )
]

@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "execute":
        return await tool_execute(arguments)
    elif name == "github_create_issue":
        return await tool_github_create_issue(arguments)
    elif name == "github_search_code":
        return await tool_github_search_code(arguments)
    elif name == "github_get_file_content":
        return await tool_github_get_file_content(arguments)
    elif name == "query_intelligence":
        return tool_query_intelligence(arguments)
    elif name == "get_portfolio_status":
        return tool_get_portfolio_status()
    elif name == "docker_list_containers":
        return tool_docker_list_containers(arguments)
    elif name == "docker_container_action":
        return tool_docker_container_action(arguments)
    elif name == "docker_run_container":
        return tool_docker_run_container(arguments)
    elif name == "docker_list_images":
        return tool_docker_list_images()
    elif name == "docker_pull_image":
        return await tool_docker_pull_image(arguments)
    elif name == "docker_container_logs":
        return tool_docker_container_logs(arguments)
    elif name == "docker_container_inspect":
        return tool_docker_container_inspect(arguments)
    elif name == "docker_list_networks":
        return tool_docker_list_networks()
    elif name == "docker_list_volumes":
        return tool_docker_list_volumes()
    else:
        raise ValueError(f"Unknown tool: {name}")

# ===== TOOL IMPLEMENTATIONS =====
async def tool_execute(args: dict) -> list[TextContent]:
    """Forward command to Infinity XOS Orchestrator"""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            ORCHESTRATOR_URL,
            json={"command": args["command"], "payload": args.get("payload", {})}
        )
        r.raise_for_status()
        return [TextContent(type="text", text=json.dumps(r.json()))]

async def tool_github_create_issue(args: dict) -> list[TextContent]:
    """Create a GitHub issue"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        payload = {
            "title": args["title"],
            "body": args["body"]
        }
        if args.get("labels"):
            payload["labels"] = args["labels"]
        
        r = await client.post(
            f"https://api.github.com/repos/{args['owner']}/{args['repo']}/issues",
            headers=headers,
            json=payload
        )
        r.raise_for_status()
        return [TextContent(type="text", text=json.dumps(r.json()))]

async def tool_github_search_code(args: dict) -> list[TextContent]:
    """Search for code across GitHub"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    search_query = args["query"]
    if args.get("owner") and args.get("repo"):
        search_query += f" repo:{args['owner']}/{args['repo']}"
    elif args.get("owner"):
        search_query += f" user:{args['owner']}"
    
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }
        
        r = await client.get(
            "https://api.github.com/search/code",
            headers=headers,
            params={"q": search_query, "per_page": args.get("max_results", 10)}
        )
        r.raise_for_status()
        data = r.json()
        
        results = {
            "total_count": data.get("total_count", 0),
            "results": [
                {
                    "name": item["name"],
                    "path": item["path"],
                    "repo": item["repository"]["full_name"],
                    "url": item["html_url"]
                }
                for item in data.get("items", [])
            ]
        }
        return [TextContent(type="text", text=json.dumps(results))]

async def tool_github_get_file_content(args: dict) -> list[TextContent]:
    """Get file content from GitHub"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "GITHUB_TOKEN not set"}))]
    
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.raw+json"
        }
        
        r = await client.get(
            f"https://api.github.com/repos/{args['owner']}/{args['repo']}/contents/{args['path']}",
            headers=headers,
            params={"ref": args.get("branch", "main")}
        )
        r.raise_for_status()
        
        result = {
            "path": args["path"],
            "content": r.text,
            "repo": f"{args['owner']}/{args['repo']}"
        }
        return [TextContent(type="text", text=json.dumps(result))]

def tool_query_intelligence(args: dict) -> list[TextContent]:
    """Query intelligence database"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    query = "SELECT id, key, value FROM memory WHERE 1=1"
    params = []
    
    if args.get("category"):
        query += " AND value LIKE ?"
        params.append(f"%{args['category']}%")
    
    if args.get("search"):
        query += " AND (key LIKE ? OR value LIKE ?)"
        params.extend([f"%{args['search']}%", f"%{args['search']}%"])
    
    query += f" LIMIT {args.get('limit', 10)}"
    
    cur.execute(query, params)
    results = []
    for row in cur.fetchall():
        results.append({
            "id": row[0],
            "url": row[1][:100] if row[1] else "",
            "data_size": len(row[2]) if row[2] else 0
        })
    
    conn.close()
    return [TextContent(type="text", text=json.dumps({"count": len(results), "sources": results}))]

def tool_get_portfolio_status() -> list[TextContent]:
    """Get portfolio status"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT account_name, current_balance, starting_balance
        FROM paper_accounts
    """)
    accounts = []
    for row in cur.fetchall():
        accounts.append({
            "name": row[0],
            "balance": row[1],
            "starting": row[2],
            "pnl": row[1] - row[2],
            "pnl_pct": ((row[1] - row[2]) / row[2] * 100) if row[2] > 0 else 0
        })
    
    cur.execute("SELECT COUNT(*) FROM paper_positions WHERE status = 'open'")
    open_positions = cur.fetchone()[0]
    
    conn.close()
    
    result = {
        "accounts": accounts,
        "open_positions": open_positions
    }
    return [TextContent(type="text", text=json.dumps(result))]

# ===== DOCKER TOOLS =====
def run_docker_command(args: list) -> dict:
    """Execute docker command and return JSON result"""
    try:
        result = subprocess.run(
            ["docker"] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return {"error": result.stderr.strip()}
        return {"output": result.stdout.strip(), "success": True}
    except subprocess.TimeoutExpired:
        return {"error": "Command timeout"}
    except FileNotFoundError:
        return {"error": "Docker not found. Is Docker installed?"}
    except Exception as e:
        return {"error": str(e)}

def tool_docker_list_containers(args: dict) -> list[TextContent]:
    """List Docker containers"""
    cmd_args = ["ps", "--format", "json"]
    if args.get("all", False):
        cmd_args.append("-a")
    
    result = run_docker_command(cmd_args)
    if "error" in result:
        return [TextContent(type="text", text=json.dumps(result))]
    
    # Parse JSON lines output
    containers = []
    for line in result["output"].split("\n"):
        if line.strip():
            try:
                containers.append(json.loads(line))
            except:
                pass
    
    return [TextContent(type="text", text=json.dumps({"containers": containers, "count": len(containers)}))]

def tool_docker_container_action(args: dict) -> list[TextContent]:
    """Control Docker containers"""
    action = args["action"]
    container = args["container"]
    
    result = run_docker_command([action, container])
    return [TextContent(type="text", text=json.dumps(result))]

def tool_docker_run_container(args: dict) -> list[TextContent]:
    """Run a new Docker container"""
    cmd_args = ["run"]
    
    if args.get("detach", True):
        cmd_args.append("-d")
    
    if args.get("name"):
        cmd_args.extend(["--name", args["name"]])
    
    if args.get("ports"):
        for container_port, host_port in args["ports"].items():
            cmd_args.extend(["-p", f"{host_port}:{container_port}"])
    
    if args.get("environment"):
        for key, value in args["environment"].items():
            cmd_args.extend(["-e", f"{key}={value}"])
    
    cmd_args.append(args["image"])
    
    result = run_docker_command(cmd_args)
    return [TextContent(type="text", text=json.dumps(result))]

def tool_docker_list_images() -> list[TextContent]:
    """List Docker images"""
    result = run_docker_command(["images", "--format", "json"])
    if "error" in result:
        return [TextContent(type="text", text=json.dumps(result))]
    
    images = []
    for line in result["output"].split("\n"):
        if line.strip():
            try:
                images.append(json.loads(line))
            except:
                pass
    
    return [TextContent(type="text", text=json.dumps({"images": images, "count": len(images)}))]

async def tool_docker_pull_image(args: dict) -> list[TextContent]:
    """Pull a Docker image"""
    result = run_docker_command(["pull", args["image"]])
    return [TextContent(type="text", text=json.dumps(result))]

def tool_docker_container_logs(args: dict) -> list[TextContent]:
    """Get container logs"""
    cmd_args = ["logs", "--tail", str(args.get("tail", 100)), args["container"]]
    result = run_docker_command(cmd_args)
    return [TextContent(type="text", text=json.dumps(result))]

def tool_docker_container_inspect(args: dict) -> list[TextContent]:
    """Inspect container"""
    result = run_docker_command(["inspect", args["container"]])
    if "error" in result:
        return [TextContent(type="text", text=json.dumps(result))]
    
    try:
        inspect_data = json.loads(result["output"])
        return [TextContent(type="text", text=json.dumps(inspect_data))]
    except:
        return [TextContent(type="text", text=json.dumps({"error": "Failed to parse inspect output"}))]

def tool_docker_list_networks() -> list[TextContent]:
    """List Docker networks"""
    result = run_docker_command(["network", "ls", "--format", "json"])
    if "error" in result:
        return [TextContent(type="text", text=json.dumps(result))]
    
    networks = []
    for line in result["output"].split("\n"):
        if line.strip():
            try:
                networks.append(json.loads(line))
            except:
                pass
    
    return [TextContent(type="text", text=json.dumps({"networks": networks, "count": len(networks)}))]

def tool_docker_list_volumes() -> list[TextContent]:
    """List Docker volumes"""
    result = run_docker_command(["volume", "ls", "--format", "json"])
    if "error" in result:
        return [TextContent(type="text", text=json.dumps(result))]
    
    volumes = []
    for line in result["output"].split("\n"):
        if line.strip():
            try:
                volumes.append(json.loads(line))
            except:
                pass
    
    return [TextContent(type="text", text=json.dumps({"volumes": volumes, "count": len(volumes)}))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

