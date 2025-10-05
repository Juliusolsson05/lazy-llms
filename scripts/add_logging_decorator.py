#!/usr/bin/env python3
"""Script to add @log_command_usage_decorator to all @mcp.tool() functions"""
import re
from pathlib import Path

def add_decorators():
    server_path = Path(__file__).parent.parent / "mcp/src/server.py"

    with open(server_path) as f:
        content = f.read()

    pattern = r'(@mcp\.tool\(\))\n(def )'
    replacement = r'@mcp.tool()\n@log_command_usage_decorator\n\2'

    updated_content = re.sub(pattern, replacement, content)

    with open(server_path, 'w') as f:
        f.write(updated_content)

    print("✅ Added @log_command_usage_decorator to all MCP tools")

if __name__ == "__main__":
    add_decorators()
