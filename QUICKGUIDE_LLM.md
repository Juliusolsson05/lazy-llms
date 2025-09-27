# LLM Project Management Quick Guide

## What is the PM System?

This is an **LLM-Native Project Management System** built with MCP (Model Context Protocol) tools. It allows LLMs to create, track, and manage development work just like human developers do with Jira or Linear.

## Core Philosophy: Document Everything

**CRITICAL**: When developing, ALWAYS think about reporting and documenting your progress from the PM perspective. Every significant action should be tracked.

## Essential Commands

### Discovery & Planning
- `pm_status` - Get project overview and metrics
- `pm_list_issues` - See all issues (filter by status, priority, module)
- `pm_get_issue --issue-key PROJ-XXX-001` - Get detailed issue info
- `pm_my_queue` - Get personalized work queue

### Creating Work
- `pm_create_issue` - Create new issues with rich specifications
- `pm_create_task --issue-key PROJ-XXX-001` - Break down issues into tasks
- `pm_estimate --issue-key PROJ-XXX-001` - Add effort estimates

### Executing Work
- `pm_start_work --issue-key PROJ-XXX-001` - Begin working on an issue
- `pm_log_work --issue-key PROJ-XXX-001 --activity code --summary "..."` - Document progress
- `pm_update_status --issue-key PROJ-XXX-001 --status done` - Update issue status

### Git Integration
- `pm_create_branch --issue-key PROJ-XXX-001` - Create feature branch
- `pm_commit --issue-key PROJ-XXX-001 --message "..."` - Commit with PM trailers

## Workflow Patterns

### 1. Starting New Work
```
1. pm_status                              # Understand current state
2. pm_my_queue                           # See what's prioritized for you
3. pm_get_issue --issue-key PROJ-XXX-001 # Get full context
4. pm_start_work --issue-key PROJ-XXX-001 # Mark as in progress
5. [do the work]
6. pm_log_work --issue-key PROJ-XXX-001 --activity code --summary "Implemented feature X"
```

### 2. Discovering Issues
```
1. pm_list_issues --status proposed      # See what needs to be done
2. pm_search_issues --query "frontend"   # Find specific topics
3. pm_blocked_issues                     # Find things you can unblock
```

### 3. Creating New Issues
```
1. pm_create_issue --type feature --title "..." --description "..."
2. pm_estimate --issue-key PROJ-XXX-001 --effort "2-3 hours" --complexity Medium
3. pm_create_task --issue-key PROJ-XXX-001 --title "Implement component"
```

## Issue Types & When to Use

- **feature**: New functionality
- **bug**: Fixing broken behavior
- **refactor**: Code improvement without behavior change
- **chore**: Maintenance, cleanup, tooling
- **spike**: Research or investigation

## Status Workflow

Issues flow through these states:
- **proposed** → **in_progress** → **review** → **done**
- Can also go to **blocked** or **canceled**
- Workflow validation prevents invalid transitions

## Activity Types for Logging

- **planning**: Design, architecture decisions
- **code**: Implementation work
- **test**: Writing or running tests
- **debug**: Troubleshooting and fixing issues
- **research**: Investigation, learning
- **review**: Code review, documentation review
- **refactor**: Code cleanup and improvement

## Best Practices for LLMs

### Always Document Progress
```
pm_log_work --issue-key PROJ-XXX-001 \
  --activity code \
  --summary "Fixed authentication bug in user login flow" \
  --time-spent "45m"
```

### Break Down Complex Work
Don't create massive issues. Use tasks:
```
pm_create_task --issue-key PROJ-XXX-001 --title "Design API endpoints"
pm_create_task --issue-key PROJ-XXX-001 --title "Implement user model"
pm_create_task --issue-key PROJ-XXX-001 --title "Add authentication middleware"
```

### Use Descriptive Issue Titles
- ❌ "Fix bug"
- ✅ "Fix authentication timeout causing user logout loops"

### Include Context in Work Logs
- What you did
- Why you did it
- Any decisions made
- Blockers encountered

### Update Status Regularly
```
pm_update_status --issue-key PROJ-XXX-001 --status review --notes "Ready for testing"
pm_update_status --issue-key PROJ-XXX-001 --status done --notes "All tests passing"
```

## Issue Structure

Every issue should have:
- **Clear title** describing the work
- **Detailed description** with business context
- **Acceptance criteria** - specific, measurable outcomes
- **Technical approach** - how you plan to implement
- **Estimates** - effort and complexity
- **Dependencies** - what must be done first

## Example: Creating a Well-Structured Issue

```
pm_create_issue \
  --type feature \
  --title "Add user dashboard with activity metrics" \
  --description "Users need a personal dashboard showing their recent activity, issue counts, and productivity metrics. This will help users understand their work patterns and stay organized." \
  --acceptance-criteria "Dashboard shows last 7 days of activity" \
  --acceptance-criteria "Displays issue counts by status" \
  --acceptance-criteria "Mobile responsive design" \
  --technical-approach "Create new dashboard component, add metrics API endpoint, use Chart.js for visualizations" \
  --priority P2 \
  --estimated-effort "1-2 days" \
  --complexity Medium
```

## Quick Commands Reference

| Command | Purpose |
|---------|---------|
| `pm_status` | Project overview |
| `pm_list_issues` | Browse issues |
| `pm_create_issue` | New issue |
| `pm_start_work` | Begin work |
| `pm_log_work` | Document progress |
| `pm_update_status` | Change issue status |
| `pm_my_queue` | Personal work queue |
| `pm_daily_standup` | Progress report |

## Remember

1. **Document as you go** - Don't wait until the end
2. **Be specific** - "Fixed bug" tells us nothing
3. **Update status** - Keep the team informed
4. **Break down work** - Use issues and tasks appropriately
5. **Think PM-first** - Before coding, create the issue

The PM system is designed to work seamlessly with development. Use it continuously, not as an afterthought.