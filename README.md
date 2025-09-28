# LLM-Native Project Management System

A project management system designed for LLM agents as first-class citizens. Track issues, log work, and manage projects with rich context - all optimized for AI workflows.

## 🚀 Quick Start (2 minutes)

### One-Command Setup
```bash
make quickstart
```

This will:
1. Install all dependencies
2. Initialize the database
3. Start the web UI at http://localhost:1929
4. Copy Claude Desktop integration command to clipboard

### Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt
cd mcp && pip install -r requirements.txt && cd ..

# 2. Initialize database
make init-db

# 3. Start services
make start  # Starts all services
```

## 🎯 Core Features

- **Rich Issue Tracking** - Issues with comprehensive specs and technical approaches
- **Work Logging** - Track development activity with artifacts and context
- **Git Integration** - Automatic branch creation and commit formatting
- **Web UI** - Visual dashboards and issue management at http://localhost:1929
- **MCP Tools** - 23 tools for LLM agents to manage projects

## 📋 Basic Usage

### Create an Issue
```bash
pm_create_issue --type feature --title "Add user auth" --description "..."
```

### Start Work
```bash
pm_start_work --issue-key LAZY-001
```

### Log Progress
```bash
pm_log_work --issue-key LAZY-001 --activity code --summary "Implemented JWT"
```

### View Status
```bash
pm_status  # Project overview
pm_list_issues  # All issues
```

## 🔧 Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pm-server": {
      "command": "python",
      "args": ["/path/to/lazy-llms/mcp/src/server.py"],
      "env": {
        "PM_DATABASE_PATH": "/path/to/lazy-llms/data/jira_lite.db"
      }
    }
  }
}
```

## 📂 Project Structure

```
lazy-llms/
├── mcp/src/              # MCP server for LLM integration
├── src/jira_lite/        # Web UI and database
├── data/                 # Database files
├── scripts/              # Utility scripts
└── docs/                 # Documentation
```

## 🛠 Available Commands

- `make quickstart` - Complete one-command setup
- `make start` - Start all services
- `make stop` - Stop all services
- `make init-db` - Initialize database
- `make clean` - Clean generated files
- `make help` - Show all commands

## 📚 Documentation

- [Full Documentation](docs/LLM_NATIVE_PM_SPECIFICATION.md)
- [Deprecated Docs](docs/deprecated/) - Old documentation for reference

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License

---

Built for AI agents, by AI agents 🤖