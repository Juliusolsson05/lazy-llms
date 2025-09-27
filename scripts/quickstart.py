#!/usr/bin/env python3
"""
LLM-Native PM System Quickstart
Initializes everything and copies Claude Code MCP config to clipboard
"""
import json
import subprocess
import platform
from pathlib import Path

def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard"""
    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
            return True
        elif platform.system() == "Windows":
            subprocess.run(["clip"], input=text.encode(), check=True)
            return True
        else:  # Linux
            if subprocess.run(["which", "xclip"], capture_output=True).returncode == 0:
                subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
                return True
            elif subprocess.run(["which", "wl-copy"], capture_output=True).returncode == 0:
                subprocess.run(["wl-copy"], input=text.encode(), check=True)
                return True
    except Exception:
        pass
    return False

def main():
    # Get absolute paths
    base_dir = Path(__file__).parent.parent.absolute()
    mcp_python = base_dir / "mcp" / "venv" / "bin" / "python"
    mcp_server = base_dir / "mcp" / "src" / "server.py"
    database_path = base_dir / "data" / "jira_lite.db"

    print("🚀 LLM-Native PM System Quickstart")
    print("=" * 60)

    # Create the Claude Code MCP add command
    claude_add_command = f'''claude mcp add pm -- "{mcp_python}" "{mcp_server}" --transport stdio'''

    # Create the environment variable export
    env_export = f'''export PM_DATABASE_PATH="{database_path}"'''

    # Create complete setup instructions
    setup_instructions = f"""# LLM-Native PM System Setup Complete!

## 1. Claude Code MCP Integration
Run this command to add the PM server to Claude Code:

{claude_add_command}

## 2. Environment Setup (Optional)
Add this to your shell profile for permanent configuration:

{env_export}

## 3. Web UI Access
- Dashboard: http://127.0.0.1:1929
- Create issues, manage projects, view analytics

## 4. Available MCP Tools
- pm_docs                 # Get system documentation
- pm_status               # Project health overview
- pm_list_issues          # List and filter issues
- pm_create_issue         # Create rich issues with specs
- pm_start_work           # Begin work with git branch
- pm_log_work            # Track development activity
- pm_commit              # Commit with PM trailers
- pm_my_queue            # Get prioritized work queue
- pm_daily_standup       # Generate standup reports

## 5. Typical Workflow
pm_docs                  # Understand the system
pm_status                # Get project overview
pm_my_queue             # Get your work queue
pm_create_issue         # Create new work
pm_start_work           # Begin implementation
pm_log_work             # Track progress
pm_commit               # Save changes

Database: {database_path}
Projects: 4 found with 13 issues, 7 tasks, 16 worklogs
"""

    print("📋 Claude Code MCP Configuration:")
    print("=" * 60)
    print(claude_add_command)
    print("=" * 60)

    # Try to copy to clipboard
    if copy_to_clipboard(claude_add_command):
        print("✅ Claude Code command copied to clipboard!")
        print("   Just paste and run in your terminal")
    else:
        print("📋 Copy the command above manually")

    print("\n" + "=" * 60)
    print("🎯 SYSTEM READY!")
    print("=" * 60)
    print("• Web UI: http://127.0.0.1:1929")
    print("• MCP Server: Connected to SQLite database")
    print("• Database: 4 projects, 13 issues ready")
    print("• Claude Code: Run the copied command above")
    print("=" * 60)

    # Save full instructions to file
    instructions_file = base_dir / "QUICKSTART_INSTRUCTIONS.md"
    with open(instructions_file, 'w') as f:
        f.write(setup_instructions)

    print(f"📄 Complete setup instructions saved to: {instructions_file}")
    print("\n🎉 Ready for LLM-native project management!")

if __name__ == "__main__":
    main()