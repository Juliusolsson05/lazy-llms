#!/usr/bin/env python3
"""Fix all decorator applications to ensure every tool has logging"""
import re
from pathlib import Path

def fix_decorators():
    server_path = Path(__file__).parent.parent / "mcp/src/server.py"

    with open(server_path) as f:
        content = f.read()

    # Pattern 1: Tools with only @mcp.tool()
    pattern1 = r'@mcp\.tool\(\)\n(?!@log_command_usage_decorator\n)(def pm_)'
    replacement1 = r'@mcp.tool()\n@log_command_usage_decorator\n\1'
    content = re.sub(pattern1, replacement1, content)

    # Pattern 2: Tools with @mcp.tool() that already have decorator (ensure correct order)
    # Make sure @log_command_usage_decorator comes AFTER @mcp.tool()
    pattern2 = r'@log_command_usage_decorator\n@mcp\.tool\(\)\n(def pm_)'
    replacement2 = r'@mcp.tool()\n@log_command_usage_decorator\n\1'
    content = re.sub(pattern2, replacement2, content)

    with open(server_path, 'w') as f:
        f.write(content)

    # Count results
    decorated_count = len(re.findall(r'@mcp\.tool\(\)\n@log_command_usage_decorator', content))
    total_tools = len(re.findall(r'@mcp\.tool\(\)', content))

    print(f"✅ Fixed decorators: {decorated_count}/{total_tools} tools have logging")

if __name__ == "__main__":
    fix_decorators()
