# LLM-Native Project Management System - Complete Documentation

## Quick Start
For practical workflow examples, call `pm_workflow` after reading this documentation.

## System Overview
This PM system is designed for LLMs as first-class citizens. Unlike human-oriented tools, it expects rich documentation, automatic git integration, and continuous progress tracking. Every action creates persistent, searchable knowledge.

## Complete Tool Reference

### Discovery Tools
- **pm_docs** - Returns this complete documentation with all tool descriptions
- **pm_workflow** - Provides practical workflow patterns and usage examples  
- **pm_status** - Shows project health overview with metrics and recent activity
- **pm_list_issues** - Lists all issues with filtering by status, priority, module, owner, or type
- **pm_get_issue** - Retrieves complete issue details including tasks, worklogs, and dependencies
- **pm_search_issues** - Performs full-text search across all issue content
- **pm_list_projects** - Shows all registered projects in the system
- **pm_my_queue** - Returns personalized work queue sorted by urgency
- **pm_blocked_issues** - Lists all issues currently blocked with reasons

### Planning Tools
- **pm_create_issue** - Creates comprehensive issues with specifications and acceptance criteria
- **pm_update_issue** - Modifies existing issue fields and content
- **pm_estimate** - Adds effort estimates and complexity assessments with reasoning
- **pm_refine_issue** - Iteratively improves issue requirements and specifications
- **pm_delete_issue** - Removes an issue and all associated data with confirmation

### Execution Tools
- **pm_start_work** - Begins work on issue by updating status and optionally creating branch
- **pm_log_work** - Records development activity with time tracking and artifacts
- **pm_update_status** - Changes issue workflow state with validation
- **pm_create_task** - Breaks issues down into manageable subtasks with checklists
- **pm_update_task** - Modifies task status, assignee, or details

### Git Integration Tools
- **pm_git_status** - Shows git repository status with issue context
- **pm_create_branch** - Creates feature branch following naming conventions
- **pm_commit** - Makes commits with automatic PM trailers and formatting
- **pm_push_branch** - Pushes branch to remote and optionally creates pull request
- **pm_stash_work** - Stashes current changes with issue context

### Analytics Tools
- **pm_project_dashboard** - Displays comprehensive project metrics and health indicators
- **pm_daily_standup** - Generates daily standup report with yesterday/today/blockers
- **pm_weekly_report** - Creates weekly summary with velocity metrics
- **pm_capacity_planning** - Analyzes team capacity and workload distribution
- **pm_risk_assessment** - Identifies project risks and suggests mitigations
- **pm_dependency_graph** - Visualizes issue dependencies and blocking relationships

### Advanced Tools
- **pm_extract_requirements** - Extracts requirements from text and optionally creates issues
- **pm_generate_test_plan** - Creates comprehensive test plans from issue specifications
- **pm_security_review** - Generates security checklist based on issue content
- **pm_suggest_next_work** - Recommends next issues based on priorities and dependencies

### Administrative Tools
- **pm_init_project** - Initializes or updates project registration in the system
- **pm_register_project** - Registers project with web UI server

## Core Concepts

### Issues
Rich work items containing:
- **Specification**: Problem statement, acceptance criteria, technical approach
- **Planning**: Dependencies, risks, estimates, stakeholders
- **Implementation**: Branch hints, commit formatting, artifacts
- **Communication**: Updates, notifications, comments
- **Analytics**: Time tracking, velocity metrics

### Issue Types
- `feature` - New functionality to be added
- `bug` - Broken behavior that needs fixing
- `refactor` - Code improvement without behavior change
- `chore` - Maintenance, dependencies, tooling work
- `spike` - Research, investigation, or proof of concept

### Priority Levels
- `P1` - Critical/blocking production issues
- `P2` - High priority, needed soon
- `P3` - Normal priority (default)
- `P4` - Low priority
- `P5` - Nice to have

### Workflow States
- `proposed` - Not yet started
- `in_progress` - Active development
- `blocked` - Waiting on dependencies
- `review` - Ready for code review
- `done` - Complete and merged
- `canceled` - Won't be completed
- `archived` - Hidden from normal views

### Activity Types (for pm_log_work)
- `planning` - Architecture and design decisions
- `code` - Implementation work
- `test` - Writing or running tests
- `debug` - Bug investigation and fixes
- `research` - Learning and exploration
- `review` - Code or documentation review
- `refactor` - Code cleanup and optimization
- `document` - Documentation writing
- `deploy` - Deployment activities
- `blocked` - Encountering blockers

## Data Model

### Project
```
- project_id: Unique identifier
- project_slug: Human-readable name
- absolute_path: Repository location
- metadata: Submodules, VCS info, MCP config
```

### Issue
```
- key: Unique identifier (PROJ-YYYYMM-XXX)
- title: Brief description
- type: Issue category
- status: Workflow state
- priority: Urgency level
- specification: JSON with description, acceptance criteria
- planning: JSON with dependencies, estimates, risks
- implementation: JSON with git integration details
```

### Task
```
- task_id: Unique identifier
- title: Task description
- status: todo/doing/blocked/review/done
- details: JSON with checklist, notes, estimates
```

### WorkLog
```
- activity: Type of work performed
- summary: Detailed description
- artifacts: JSON list of related files/commits
- context: JSON with time spent, blockers, decisions
- timestamp_utc: When work occurred
```

## Required Fields

### Creating Issues (pm_create_issue)
**Required:**
- `type` - Issue type (feature/bug/refactor/chore/spike)
- `title` - Clear, specific title (5-200 characters)
- `description` - Comprehensive description (minimum 20 characters)

**Recommended:**
- `priority` - P1-P5 (defaults to P3)
- `acceptance_criteria` - List of measurable outcomes
- `technical_approach` - Implementation strategy
- `estimated_effort` - Time estimate (e.g., "2-3 days")
- `complexity` - Low/Medium/High/Very High

### Logging Work (pm_log_work)
**Required:**
- `issue_key` - Issue to log against
- `activity` - Type of activity
- `summary` - What was done (minimum 10 characters)

**Recommended:**
- `time_spent` - Duration (e.g., "2h", "30m")
- `artifacts` - List of files/commits/documents
- `blockers` - Any impediments encountered
- `decisions` - Technical decisions made

## System Architecture

### Components
1. **MCP Server** (`mcp/src/server.py`) - Provides tools to LLMs via stdio/HTTP
2. **Web UI** (`src/jira_lite/app.py`) - Dashboard at http://127.0.0.1:1928
3. **Database** (`data/jira_lite.db`) - SQLite with Peewee ORM
4. **API** (`/api/*`) - RESTful endpoints for data access

### Project Scope Resolution
The system automatically detects project context via:
1. `PM_DEFAULT_PROJECT_ID` environment variable
2. Current working directory matching registered project path
3. First available project as fallback

Most commands auto-detect scope but accept `--project-id` override.

## Best Practices

### Issue Creation
- Write descriptions assuming no prior context
- Include both business value and technical approach
- List specific, testable acceptance criteria
- Estimate effort realistically with reasoning
- Identify dependencies explicitly

### Work Logging
- Log progress every 30-60 minutes
- Include technical decisions and learnings
- Reference specific files and commits
- Track actual time spent, not estimates
- Document blockers immediately

### Status Management
- Update status within 5 minutes of state change
- Include notes explaining status changes
- Set blocker reasons when blocking
- Move to review before done
- Use canceled instead of deleting issues

### Git Integration
- Always use pm_commit for consistent formatting
- Create branches via pm_create_branch
- Include issue key in all commits
- Push regularly to avoid conflicts

## Environment Variables
- `PM_DATABASE_PATH` - Path to SQLite database
- `PM_DEFAULT_PROJECT_ID` - Default project for operations
- `PM_DEFAULT_OWNER` - Default issue assignee
- `GIT_USER_NAME` - Git commit author name
- `GIT_USER_EMAIL` - Git commit author email

## Error Recovery
When commands fail:
1. Check error message for specific guidance
2. Verify project exists with `pm_list_projects`
3. Ensure issue exists with `pm_get_issue`
4. Check dependencies with `pm_blocked_issues`
5. Verify git state with `pm_git_status`

## Time Format Examples
- `30m` - 30 minutes
- `1h` - 1 hour
- `2h30m` - 2.5 hours
- `1d` - 8 hours (one workday)
- `1.5d` - 12 hours

## Artifact Types
For pm_log_work artifacts:
- `{"type": "file", "path": "src/main.py"}`
- `{"type": "test", "path": "tests/test_main.py"}`
- `{"type": "commit", "hash": "abc123"}`
- `{"type": "pr", "url": "https://github.com/..."}`
- `{"type": "document", "path": "docs/api.md"}`

## Success Indicators
You're using the system effectively when:
- Every code change has an associated issue
- Work logs appear every 30-60 minutes
- Issues contain comprehensive specifications
- Dependencies are properly tracked
- Status accurately reflects reality
- Git commits include PM trailers

## System Limits
- Max 100 issues per list query
- Max 50 worklogs per query
- Issue key format: PROJ-YYYYMM-XXX
- Title max length: 200 characters
- Description min length: 20 characters

## Web UI Access
- Dashboard: http://127.0.0.1:1928
- View all projects and issues
- Visual kanban board
- Archived issues view
- Create and edit through web interface

## Getting Help
- Call `pm_workflow` for practical examples
- Use `pm_status` to understand current state  
- Check `pm_list_issues` to browse existing work
- Web UI provides visual overview

Remember: This system is your persistent memory. The more detail you provide, the more valuable it becomes for future work.
