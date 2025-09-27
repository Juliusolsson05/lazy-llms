# LLM-Native Project Management System

**Complete implementation of Jira-lite + MCP server for LLM agents**

A comprehensive project management system designed specifically for LLM agents as first-class citizens, with rich context, git integration, and human oversight capabilities.

## 🚀 Quick Start

**One-command setup:**
```bash
make quickstart
```

This will:
1. ✅ Install all dependencies (Flask web UI + MCP server)
2. ✅ Migrate data to SQLite database with sample projects/issues
3. ✅ Copy Claude Code integration command to clipboard
4. ✅ Start web UI at http://127.0.0.1:1929
5. ✅ Generate complete setup instructions

**Then just paste the Claude Code command from clipboard and you're ready!**

## 🎯 System Components

### **Web UI (Jira-lite)**
- **Rich Issue Management** - Create, edit, and track issues with markdown support
- **Project Dashboards** - Visual progress tracking with metrics
- **Modular Organization** - Issues organized by project modules
- **Real-time Updates** - Live activity tracking and status changes

### **MCP Server (23 Tools)**
- **Discovery Tools** - `pm_docs`, `pm_status`, `pm_list_issues`, `pm_search_issues`
- **Planning Tools** - `pm_create_issue`, `pm_estimate`, `pm_refine_issue`
- **Execution Tools** - `pm_start_work`, `pm_log_work`, `pm_update_status`
- **Git Integration** - `pm_create_branch`, `pm_commit`, `pm_push_branch`
- **Analytics Tools** - `pm_my_queue`, `pm_blocked_issues`, `pm_daily_standup`

### **Database (SQLite + Peewee)**
- **Django-style ORM** - Clean syntax, auto lazy-loading, no FK management
- **Hybrid Storage** - Structured columns + JSON fields for rich LLM content
- **Fast Queries** - Indexed columns, full-text search, relationship queries
- **Migration System** - Smooth upgrade from JSON files with backup

## 📋 Available Commands

### **Setup & Installation**
- `make quickstart` - 🚀 **Ultimate one-command setup**
- `make install-complete` - Complete installation: Web UI + MCP server
- `make install-db` - Install with SQLite database migration
- `make bootstrap` - Setup Python environment and dependencies

### **Web UI Commands**
- `make jl-run-auto` - Start Jira-lite web UI
- `make migrate-to-db` - Migrate JSON → SQLite database
- `make jl-init-db` - Initialize with mock data

### **MCP Server Commands**
- `make mcp-validate` - Validate MCP server configuration
- `make mcp-run` - Run MCP server for Claude Code
- `make mcp-run-http` - Run MCP server in HTTP mode for testing
- `make mcp-claude-config` - Show Claude Code configuration

### **Docker Commands**
- `make docker-build` - Build container image
- `make docker-run` - Start containerized system
- `make docker-stop` - Stop containers
- `make docker-logs` - View container logs

### **Development**
- `make test` - Run basic functionality tests
- `make clean` - Clean up generated files
- `make help` - Show all available commands

## 🧠 LLM Agent Workflow

### **Fresh Session Startup**
```
pm_docs                    # Understand system capabilities
pm_status --verbose        # Get comprehensive project overview
pm_my_queue               # Get prioritized work queue
pm_blocked_issues         # Check for unblocking opportunities
```

### **Creating New Work**
```
pm_create_issue --type feature --title "Add user authentication"
  --description "Comprehensive technical specification..."
  --priority P2 --module backend

pm_estimate --effort "3-5 days" --complexity High
  --reasoning "JWT implementation + security review + testing"

pm_refine_issue --aspect technical
  --suggestions "Consider OAuth for future extensibility"
```

### **Implementation Cycle**
```
pm_start_work --issue-key PROJ-001    # Status → in_progress + branch
pm_log_work --activity code --summary "Implemented JWT middleware"
  --time-spent "2h" --artifacts '[{"type":"file","path":"src/auth.py"}]'

pm_commit --message "feat: add JWT authentication middleware"
# Auto-formatted: [pm PROJ-001] feat: add JWT middleware\n\nPM: PROJ-001

pm_create_task --title "Add integration tests"
  --checklist '["Write auth tests","Test token validation"]'
```

### **Completion**
```
pm_update_status --status review --notes "Implementation complete"
pm_push_branch --create-pr --reviewers '["security-team"]'
pm_daily_standup                      # Generate progress report
```

## 🗂️ Project Structure

```
lazy-llms/
├── src/jira_lite/              # Flask web UI
│   ├── app.py                  # Main Flask application
│   ├── models.py              # Peewee ORM models
│   ├── repositories.py        # Clean query interface
│   ├── api/                   # RESTful API endpoints
│   └── templates/             # HTML templates with Tailwind CSS
├── mcp/src/                   # MCP server for LLM agents
│   ├── server.py              # Main MCP server with 23 tools
│   ├── config.py              # Configuration management
│   ├── database.py            # Database operations (no raw SQL)
│   ├── models.py              # Pydantic input/output models
│   └── utils.py               # Utilities with security and async fixes
├── data/
│   ├── jira_lite.db          # SQLite database (147KB with sample data)
│   ├── events.jsonl          # Audit trail (append-only)
│   └── backup/               # JSON file backups
├── docs/
│   └── LLM_NATIVE_PM_SPECIFICATION.md  # Complete technical specification
├── scripts/
│   └── quickstart.py         # One-command setup script
├── Dockerfile                # Container deployment
├── docker-compose.yml        # Container orchestration
└── Makefile                 # Unified command interface
```

## 🎨 Features

### **LLM-Native Design**
- **Rich Context** - Every issue contains comprehensive technical specifications
- **Reasoning Captured** - All decisions, estimates, and changes include the "why"
- **Git Integration** - Automatic branch creation, commit formatting, PR generation
- **Intelligent Workflows** - Smart prioritization and dependency analysis

### **Human-Friendly Interface**
- **Visual Dashboards** - Real-time project health and progress tracking
- **Issue Management** - Create, edit, and organize work with rich markdown
- **Module Organization** - Issues grouped by project components
- **Analytics** - Velocity metrics, burndown charts, capacity planning

### **Production-Ready Architecture**
- **SQLite + Peewee** - Django-style ORM without SQLAlchemy complexity
- **Security-First** - Git command validation, rate limiting, output sanitization
- **Docker Support** - Containerized deployment with persistent storage
- **Migration System** - Smooth upgrades with automatic backups

## 🔧 Architecture Highlights

### **Database Design**
- **Structured Columns** - Fast queries on status, priority, module, dates
- **JSON Fields** - Rich LLM content (specifications, planning, analytics)
- **Auto Relationships** - Clean `issue.project.slug`, `issue.tasks` syntax
- **No FK Management** - Peewee handles all relationship complexity

### **MCP Integration**
- **Standardized Responses** - All tools return `{success, message, data, hints}`
- **Comprehensive Validation** - Pydantic models with detailed field descriptions
- **Security Features** - Command validation, path sanitization, rate limiting
- **Rich Context** - Every tool includes helpful next steps and recommendations

### **Git Workflow**
- **Naming Conventions** - `feat/PROJ-001-user-authentication`
- **Commit Formatting** - `[pm PROJ-001] feat: add auth\n\nPM: PROJ-001`
- **Branch Management** - Automatic creation, tracking, and PR integration
- **Safety Features** - Identity setup, command validation, error handling

## 📊 Sample Data

The system comes with rich sample data:
- **4 Projects** - Various types (web app, AI system, game engine)
- **13 Issues** - Features, bugs, chores across different modules
- **7 Tasks** - Detailed breakdowns with checklists
- **16 Worklogs** - Development activity with artifacts and timing

## 🌐 Access Points

After running `make quickstart`:

- **Web Dashboard** - http://127.0.0.1:1929
- **API Endpoint** - http://127.0.0.1:1929/api
- **Rich Issue Example** - http://127.0.0.1:1929/pn_4d1e7f9a2b5c8e3f6a0d2c4e6f8a1b3d/issues/TEST-005
- **MCP Server** - Available via Claude Code after running the copied command

## 🎉 Ready for Production

This system represents a **complete, production-ready implementation** of LLM-native project management:

✅ **Web UI** - Rich, responsive interface for human oversight
✅ **MCP Server** - 23 comprehensive tools for LLM agents
✅ **Database** - SQLite with proper relationships and JSON flexibility
✅ **Git Integration** - Full workflow automation with safety
✅ **Docker Deployment** - Containerized with persistent storage
✅ **Documentation** - Complete specs and setup instructions
✅ **Security** - Proper validation, sanitization, and rate limiting
✅ **Claude Code Ready** - One-command integration

The vision of **LLM agents as first-class project managers** is now a reality!

## 📄 License

MIT

---

**Built with ❤️ for the future of AI-native development workflows**