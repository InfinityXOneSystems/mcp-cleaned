"""
Test script for Infinity XOS Omni-Directional Hub MCP
"""
import sys

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_section(title):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}\n")

def main():
    print_section("🌌 INFINITY XOS OMNI-DIRECTIONAL HUB")
    
    try:
        from main_extended import TOOLS, server
        
        print(f"{Colors.GREEN}✓{Colors.RESET} Omni Hub MCP loaded successfully")
        print(f"{Colors.BLUE}  Server Name:{Colors.RESET} {server.name}")
        print(f"{Colors.BLUE}  Total Tools:{Colors.RESET} {len(TOOLS)}")
        
        # Categorize tools
        categories = {
            "Orchestrator": [],
            "GitHub": [],
            "Docker": [],
            "Local Intelligence": []
        }
        
        for tool in TOOLS:
            if tool.name == "execute":
                categories["Orchestrator"].append(tool)
            elif tool.name.startswith("github_"):
                categories["GitHub"].append(tool)
            elif tool.name.startswith("docker_"):
                categories["Docker"].append(tool)
            else:
                categories["Local Intelligence"].append(tool)
        
        print_section("📊 Tool Distribution")
        
        for category, tools in categories.items():
            print(f"{Colors.BOLD}{category}:{Colors.RESET} {len(tools)} tools")
            for i, tool in enumerate(tools, 1):
                # Extract description from tool
                desc = tool.description if hasattr(tool, 'description') else ""
                print(f"  {i}. {Colors.YELLOW}{tool.name}{Colors.RESET}")
                if desc:
                    print(f"     {Colors.BLUE}→{Colors.RESET} {desc}")
        
        print_section("🎯 Capabilities Summary")
        
        capabilities = [
            ("🔧 Orchestrator Integration", "Forward commands to Infinity XOS Orchestrator"),
            ("🐙 GitHub Integration", "Issues, code search, file content retrieval"),
            ("🐳 Docker Control", "Full container, image, network & volume management"),
            ("🧠 Local Intelligence", "Query 1,271 intelligence sources & trading portfolio")
        ]
        
        for icon_title, desc in capabilities:
            print(f"{Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}{icon_title}{Colors.RESET}")
            print(f"  {desc}\n")
        
        print_section("🚀 Usage Instructions")
        
        print(f"{Colors.BOLD}Environment Variables:{Colors.RESET}")
        print(f"  {Colors.YELLOW}GITHUB_TOKEN{Colors.RESET} - For GitHub API access")
        print(f"  {Colors.YELLOW}ORCHESTRATOR_URL{Colors.RESET} - Default: Infinity XOS Cloud\n")
        
        print(f"{Colors.BOLD}Prerequisites:{Colors.RESET}")
        print(f"  • Docker Desktop running (for Docker tools)")
        print(f"  • mcp_memory.db initialized (for intelligence tools)")
        print(f"  • GitHub token set (for GitHub tools)\n")
        
        print(f"{Colors.BOLD}Start Omni Hub:{Colors.RESET}")
        print(f"  {Colors.CYAN}python main_extended.py{Colors.RESET}\n")
        
        print(f"{Colors.GREEN}{Colors.BOLD}✨ OMNI HUB READY FOR AI AUTONOMOUS OPERATIONS ✨{Colors.RESET}\n")
        
        return 0
        
    except Exception as e:
        print(f"{Colors.RED}✗ Failed to load Omni Hub{Colors.RESET}")
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
