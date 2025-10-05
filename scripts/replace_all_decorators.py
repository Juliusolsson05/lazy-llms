#!/usr/bin/env python3
"""Replace all @mcp.tool()/@log_command_usage_decorator with @conditional_mcp_tool"""
import re
from pathlib import Path

def replace_decorators():
    server_path = Path(__file__).parent.parent / "mcp/src/server.py"

    with open(server_path) as f:
        content = f.read()

    # Replace patterns:
    # 1. @mcp.tool()\n@log_command_usage_decorator\n
    # 2. @log_command_usage_decorator\n@mcp.tool()\n
    # 3. Just @mcp.tool()\n (without log decorator)

    # Pattern 1: @mcp.tool() followed by @log_command_usage_decorator
    pattern1 = r'@mcp\.tool\(\)\n@log_command_usage_decorator\n'
    replacement1 = '@conditional_mcp_tool\n'
    content = re.sub(pattern1, replacement1, content)

    # Pattern 2: @log_command_usage_decorator followed by @mcp.tool()
    pattern2 = r'@log_command_usage_decorator\n@mcp\.tool\(\)\n'
    replacement2 = '@conditional_mcp_tool\n'
    content = re.sub(pattern2, replacement2, content)

    # Pattern 3: Just @mcp.tool() without log decorator
    pattern3 = r'@mcp\.tool\(\)\n(?!@)'
    replacement3 = '@conditional_mcp_tool\n'
    content = re.sub(pattern3, replacement3, content)

    with open(server_path, 'w') as f:
        f.write(content)

    # Count results
    conditional_count = len(re.findall(r'@conditional_mcp_tool', content))
    mcp_count = len(re.findall(r'@mcp\.tool\(\)', content))

    print(f"✅ Replaced decorators:")
    print(f"   - @conditional_mcp_tool: {conditional_count}")
    print(f"   - @mcp.tool() remaining: {mcp_count}")

if __name__ == "__main__":
    replace_decorators()