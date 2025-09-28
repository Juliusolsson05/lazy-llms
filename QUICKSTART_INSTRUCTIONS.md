# LLM-Native PM System Setup Complete!

## 1. Claude Code MCP Integration
Run this command to add the PM server to Claude Code:

claude mcp add pm -- "/Users/juliusolsson/Desktop/Development/lazy-llms/mcp/venv/bin/python" "/Users/juliusolsson/Desktop/Development/lazy-llms/mcp/src/server.py" --transport stdio

## 2. Environment Setup (Optional)
Add this to your shell profile for permanent configuration:

export PM_DATABASE_PATH="/Users/juliusolsson/Desktop/Development/lazy-llms/data/jira_lite.db"

## 3. Web UI Access
- Dashboard: http://127.0.0.1:1928
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

Database: /Users/juliusolsson/Desktop/Development/lazy-llms/data/jira_lite.db
Project: lazy-llms-test with real PM tracking
