# PM MCP Server - LLM-Native Project Management

A comprehensive Model Context Protocol (MCP) server providing production-ready project management tools specifically designed for LLM agents.

## 🎯 Features

- **20+ Core PM Tools**: Essential project management toolkit with room for 40+ more
- **Rich LLM Context**: Every tool designed for AI agent understanding and workflow
- **Git Integration**: Automatic branch creation, commit formatting, and PR management
- **SQLite Backend**: Connects to existing Jira-lite database with zero external dependencies
- **Intelligent Workflows**: Smart prioritization, dependency analysis, and recommendations
- **Production Ready**: Proper error handling, rate limiting, and security measures

## 🚀 Quick Start

### 1. Prerequisites

Ensure you have the main Jira-lite system running:

```bash
# From the main project directory
make install-db        # Sets up SQLite database with sample data
make jl-run-auto      # Starts web UI at http://127.0.0.1:1930
```

### 2. Install MCP Server

```bash
cd mcp/
make install
```

### 3. Test the Server

```bash
# Validate configuration
make validate

# Test in HTTP mode
make run-http
# Server runs at http://127.0.0.1:8848

# Test in stdio mode (for Claude Desktop)
make run
```

### 4. Add to Claude Desktop

```bash
make claude-add
```

Copy the displayed configuration into your `claude_desktop_config.json` file.

## 🛠️ Available Tools

### Discovery & Navigation (6 tools)
- **`pm_docs`** - Comprehensive system documentation and workflow guidance
- **`pm_status`** - Project health overview with metrics and issue distributions
- **`pm_list_issues`** - List and filter issues with intelligent sorting
- **`pm_get_issue`** - Detailed issue view with tasks, worklogs, and dependencies
- **`pm_list_projects`** - Show all available projects with statistics
- **`pm_search_issues`** - Full-text search across all issue content

### Planning & Requirements (4 tools)
- **`pm_create_issue`** - Create comprehensive issues with rich LLM specifications
- **`pm_update_issue`** - Update issue details and requirements
- **`pm_estimate`** - Add effort estimates with detailed reasoning
- **`pm_refine_issue`** - Iteratively improve requirements and specifications

### Work Execution (4 tools)
- **`pm_start_work`** - Begin work on issue (status update + optional branch creation)
- **`pm_log_work`** - Track development activity with artifacts and time
- **`pm_update_status`** - Change issue status with workflow validation
- **`pm_create_task`** - Break issues into manageable tasks with checklists

### Git Integration (3 tools)
- **`pm_create_branch`** - Create branches following naming conventions
- **`pm_commit`** - Commit with automatic PM trailers and formatting
- **`pm_push_branch`** - Push branches and optionally create PRs

### Analytics & Insights (3 tools)
- **`pm_project_dashboard`** - Comprehensive project metrics and health indicators
- **`pm_my_queue`** - Personal work queue with intelligent prioritization
- **`pm_blocked_issues`** - Find blocked work with unblocking recommendations

### Workflow & Reporting (3 tools)
- **`pm_daily_standup`** - Generate daily standup reports
- **`pm_weekly_report`** - Weekly progress summaries
- **`pm_capacity_planning`** - Team capacity and workload analysis

**Total: 23 core tools implemented** *(with 37+ additional tools planned)*

## 📋 Typical Workflow

### Morning Startup (Fresh LLM Session)
```
pm_docs                    # Understand system capabilities
pm_status --verbose        # Get comprehensive project overview
pm_my_queue               # Get prioritized personal work queue
pm_blocked_issues         # Check for unblocking opportunities
```

### Creating New Work
```
pm_create_issue
  --type feature
  --title "Add user authentication system"
  --description "Comprehensive technical specification with architecture, security considerations, and implementation phases..."
  --priority P2
  --module backend
  --acceptance-criteria "JWT tokens implemented,Login/logout working,Password hashing secure"

pm_estimate
  --issue-key PROJ-001
  --effort "3-5 days"
  --complexity High
  --reasoning "JWT implementation requires security review, database changes, and comprehensive testing"
```

### Implementation Cycle
```
pm_start_work --issue-key PROJ-001    # Status → in_progress + branch creation
pm_log_work --issue-key PROJ-001 --activity code --summary "Implemented JWT middleware" --time-spent "2h"
pm_commit --issue-key PROJ-001 --message "feat: add JWT authentication middleware"
pm_create_task --issue-key PROJ-001 --title "Add integration tests"
```

### Completion
```
pm_update_status --issue-key PROJ-001 --status review --notes "Implementation complete"
pm_push_branch --issue-key PROJ-001 --create-pr --reviewers "security-team,backend-team"
pm_daily_standup                      # Generate progress report
```

## ⚙️ Configuration

### Environment Variables

- **`PM_DATABASE_PATH`** - Path to SQLite database (required)
- **`PM_DEFAULT_PROJECT_ID`** - Default project ID to avoid specifying each time
- **`PM_DEFAULT_OWNER`** - Default issue owner (default: "agent:claude-code")
- **`GIT_USER_NAME`** - Git commit author name (default: "Claude Code Agent")
- **`GIT_USER_EMAIL`** - Git commit author email (default: "noreply@anthropic.com")

### Example Configuration

```bash
export PM_DATABASE_PATH="/path/to/lazy-llms/data/jira_lite.db"
export PM_DEFAULT_PROJECT_ID="pn_4d1e7f9a2b5c8e3f6a0d2c4e6f8a1b3d"
export PM_DEFAULT_OWNER="agent:claude-code"
export GIT_USER_NAME="Claude AI Assistant"
export GIT_USER_EMAIL="claude@anthropic.com"
```

## 🔧 Architecture

### Key Design Decisions

1. **Sync Tools**: Uses synchronous functions to avoid async/blocking complexity
2. **Peewee ORM**: Django-style syntax without SQLAlchemy foreign key management
3. **Standardized Responses**: All tools return `{success, message, data, hints, timestamp}`
4. **Security First**: Git command validation, path sanitization, rate limiting
5. **Error Resilient**: Graceful degradation and helpful error messages

### Database Integration

```python
# Clean Peewee queries - no raw SQL
with DatabaseSession():
    issue = PMDatabase.get_issue('PROJ-001')        # Single issue
    issues = PMDatabase.get_issues(status='active') # Filtered list
    relations = PMDatabase.get_issue_with_relations('PROJ-001')  # With tasks/worklogs
```

### Git Safety Features

- **Command Validation**: Only allowed git commands can be executed
- **Path Sanitization**: Prevents directory traversal attacks
- **Rate Limiting**: Prevents git command spam (20 ops/minute)
- **Output Sanitization**: Removes sensitive paths from error messages
- **Identity Setup**: Automatic git user configuration

## 🧪 Testing

### Basic Functionality Test

```bash
make test
```

### Manual Testing

```bash
# Start in HTTP mode for testing
make run-http

# Test with curl (server runs on http://127.0.0.1:8848)
curl -X POST http://127.0.0.1:8848/tools/pm_status \
  -H "Content-Type: application/json" \
  -d '{"project_id": null, "verbose": true}'
```

### Integration with Claude Desktop

1. Run `make claude-add` to get configuration
2. Add to your `claude_desktop_config.json`
3. Restart Claude Desktop
4. Test with commands like `pm_docs` and `pm_status`

## 🐛 Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Check database exists and is readable
ls -la ../data/jira_lite.db

# Validate configuration
make validate

# Rebuild database if needed
cd .. && make migrate-to-db
```

**Git Operation Failures**
```bash
# Check if directory is a git repository
git status

# Verify git identity
git config user.name
git config user.email
```

**Import Errors**
```bash
# Reinstall dependencies
make clean && make bootstrap
```

### Debug Mode

Set environment variable for detailed logging:
```bash
export PM_DEBUG=1
make run
```

## 🔮 Planned Enhancements

### Additional Tools (37 more planned)

**Extended Planning**
- `pm_split_issue` - Break large issues into smaller ones
- `pm_link_issues` - Create dependency relationships
- `pm_assign_issue` - Change ownership with notifications
- `pm_prioritize_issue` - Update priority with business justification

**Advanced Git Integration**
- `pm_git_status` - Enhanced git status with issue context
- `pm_switch_branch` - Switch to issue branch
- `pm_merge_status` - Check merge readiness
- `pm_stash_work` - Stash with issue context

**Enhanced Analytics**
- `pm_velocity` - Detailed velocity analysis
- `pm_burndown` - Sprint/milestone burndown charts
- `pm_risk_assessment` - Project risk analysis
- `pm_dependency_graph` - Visual dependency mapping

**Workflow Automation**
- `pm_suggest_next_work` - AI-driven work recommendations
- `pm_identify_blockers` - Systematic blocker analysis
- `pm_optimize_workflow` - Process improvement suggestions

### Advanced Features
- **Requirements Extraction**: Auto-create issues from documents
- **Test Plan Generation**: Auto-generate test cases from acceptance criteria
- **Security Review**: Automated security checklist generation
- **Performance Impact**: Analyze performance implications

## 📄 License

MIT

---

## 🤝 Contributing

This MCP server is designed to be extended. To add new tools:

1. Add Pydantic model to `src/models.py`
2. Implement tool function in `src/server.py`
3. Follow the standardized response format
4. Add comprehensive descriptions for LLM understanding
5. Include helpful hints for next steps

The foundation is solid - ready for the full 60+ tool implementation!