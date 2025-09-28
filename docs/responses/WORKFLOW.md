# PM-Driven Development Workflow Guide

## START HERE
Call `pm_docs` first to get the complete list of all available tools and system documentation. This workflow guide focuses on practical usage patterns.

## Core Workflow Philosophy
**Document as you work, not after.** Every significant action should be tracked in real-time. Think of the PM system as your external memory that persists across sessions.

## Essential Daily Workflow

### Morning Startup Sequence
```
1. pm_list_issues --status in_progress
   → See what's currently being worked on
   
2. pm_list_issues --status proposed --priority P1
   → Check high-priority items waiting to start
   
3. pm_list_issues --status blocked  
   → Identify blockers that might be resolved
```

### Before Writing Any Code
```
1. pm_list_issues --module [relevant-module]
   → Find existing issues in the area you're working
   
2. If no relevant issue exists:
   pm_create_issue --type feature --title "..." --description "..."
   
3. pm_get_issue --issue-key PROJ-XXX-001
   → Get full context before starting
   
4. pm_start_work --issue-key PROJ-XXX-001
   → Updates status to in_progress, optionally creates branch
```

### During Development (Every 30-60 Minutes)
```
pm_log_work \
  --issue-key PROJ-XXX-001 \
  --activity code \
  --summary "Implemented user authentication middleware with JWT tokens" \
  --time-spent "45m" \
  --artifacts '[{"type":"file","path":"src/auth/middleware.py"}]'
```

### When You Make Commits
```
pm_commit \
  --issue-key PROJ-XXX-001 \
  --message "feat: add JWT authentication middleware"
  
# This automatically formats as:
# [pm PROJ-XXX-001] feat: add JWT authentication middleware
# 
# PM: PROJ-XXX-001
```

### When Work is Complete
```
pm_update_status \
  --issue-key PROJ-XXX-001 \
  --status review \
  --notes "Implementation complete, all tests passing"
```

## Detailed Workflow Examples

### WORKFLOW 1: Fixing a Bug
```
# 1. Find the bug issue or create it
pm_list_issues --type bug --status proposed
# OR create new:
pm_create_issue \
  --type bug \
  --title "User logout fails with 500 error" \
  --description "When users click logout, the session isn't properly cleared and returns 500. Stack trace shows KeyError in session middleware." \
  --priority P2

# 2. Start work
pm_start_work --issue-key PROJ-XXX-002 --create-branch true

# 3. Investigation phase
pm_log_work \
  --issue-key PROJ-XXX-002 \
  --activity debug \
  --summary "Traced error to session.clear() being called on None object when session already expired" \
  --time-spent "30m"

# 4. Implementation
pm_log_work \
  --issue-key PROJ-XXX-002 \
  --activity code \
  --summary "Added null check before session.clear(), added test for expired sessions" \
  --time-spent "1h" \
  --artifacts '[{"type":"file","path":"src/auth/logout.py"},{"type":"test","path":"tests/test_logout.py"}]'

# 5. Commit the fix
pm_commit \
  --issue-key PROJ-XXX-002 \
  --message "fix: handle expired sessions in logout flow"

# 6. Complete
pm_update_status --issue-key PROJ-XXX-002 --status done
```

### WORKFLOW 2: Building a Feature
```
# 1. Create comprehensive issue
pm_create_issue \
  --type feature \
  --title "Add email notification system" \
  --description "Users need email notifications for important events. Implement using SendGrid API with template support." \
  --priority P2 \
  --acceptance-criteria '["Email sent on password reset","Email sent on new device login","Users can opt-out"]'

# 2. Add estimate
pm_estimate \
  --issue-key PROJ-XXX-003 \
  --effort "2-3 days" \
  --complexity High \
  --reasoning "Need to integrate SendGrid, create templates, add user preferences"

# 3. Start and plan
pm_start_work --issue-key PROJ-XXX-003

pm_log_work \
  --issue-key PROJ-XXX-003 \
  --activity planning \
  --summary "Designed email service architecture with queue for reliability" \
  --time-spent "1h"

# 4. Implement in phases
pm_log_work \
  --issue-key PROJ-XXX-003 \
  --activity code \
  --summary "Created email service class with SendGrid integration" \
  --time-spent "2h" \
  --artifacts '[{"type":"file","path":"src/services/email.py"}]'

pm_log_work \
  --issue-key PROJ-XXX-003 \
  --activity code \
  --summary "Added email templates for password reset and new device" \
  --time-spent "1h30m"

# 5. Test
pm_log_work \
  --issue-key PROJ-XXX-003 \
  --activity test \
  --summary "Added integration tests for email service, mocked SendGrid API" \
  --time-spent "1h"

# 6. Ready for review
pm_update_status --issue-key PROJ-XXX-003 --status review
```

### WORKFLOW 3: Research and Investigation
```
# 1. Create spike issue
pm_create_issue \
  --type spike \
  --title "Evaluate caching strategies for API responses" \
  --description "Current API response times are slow. Research caching options." \
  --priority P3

# 2. Document research
pm_log_work \
  --issue-key PROJ-XXX-004 \
  --activity research \
  --summary "Compared Redis vs Memcached. Redis offers more data structures and persistence." \
  --time-spent "2h"

pm_log_work \
  --issue-key PROJ-XXX-004 \
  --activity research \
  --summary "Benchmarked both solutions. Redis: 50k ops/sec, Memcached: 55k ops/sec" \
  --time-spent "3h" \
  --artifacts '[{"type":"document","path":"docs/cache-benchmark.md"}]'

# 3. Document conclusion
pm_update_status \
  --issue-key PROJ-XXX-004 \
  --status done \
  --notes "Recommendation: Use Redis for flexibility despite slight performance difference"
```

### WORKFLOW 4: Handling Blockers
```
# 1. Hit a blocker during work
pm_update_status \
  --issue-key PROJ-XXX-005 \
  --status blocked \
  --blocker-reason "Cannot proceed without database migration from issue PROJ-XXX-004"

# 2. Document the blocker
pm_log_work \
  --issue-key PROJ-XXX-005 \
  --activity blocked \
  --summary "Waiting for database schema changes. Used time to document API design." \
  --time-spent "30m"

# 3. When unblocked
pm_update_status \
  --issue-key PROJ-XXX-005 \
  --status in_progress \
  --notes "Database migration complete, resuming work"
```

## The 10 Most Critical Tools

### 1. `pm_list_issues`
Browse all issues with filters. Use this constantly to understand work state.
```
pm_list_issues --status proposed --priority P1
pm_list_issues --module frontend
pm_list_issues --owner "agent:claude-code"
```

### 2. `pm_get_issue`
Get complete issue details including tasks, worklogs, and dependencies.
```
pm_get_issue --issue-key PROJ-XXX-001
```

### 3. `pm_create_issue`
Create new work items with rich specifications.
```
pm_create_issue --type feature --title "..." --description "..." --priority P2
```

### 4. `pm_start_work`
Begin work on an issue (updates status, optionally creates git branch).
```
pm_start_work --issue-key PROJ-XXX-001 --create-branch true
```

### 5. `pm_log_work`
Document progress with time tracking and artifacts.
```
pm_log_work --issue-key PROJ-XXX-001 --activity code --summary "..." --time-spent "2h"
```

### 6. `pm_update_status`
Change issue workflow state.
```
pm_update_status --issue-key PROJ-XXX-001 --status review
```

### 7. `pm_commit`
Create git commits with automatic PM formatting.
```
pm_commit --issue-key PROJ-XXX-001 --message "feat: add new feature"
```

### 8. `pm_estimate`
Add effort and complexity estimates to issues.
```
pm_estimate --issue-key PROJ-XXX-001 --effort "1-2 days" --complexity Medium
```

### 9. `pm_create_task`
Break down issues into manageable subtasks.
```
pm_create_task --issue-key PROJ-XXX-001 --title "Implement API endpoint"
```

### 10. `pm_update_issue`
Modify existing issue details.
```
pm_update_issue --issue-key PROJ-XXX-001 --priority P1 --notes "Escalated by customer"
```

## Activity Types for pm_log_work
- `planning` - Design, architecture decisions
- `code` - Writing implementation
- `test` - Writing or running tests  
- `debug` - Investigating bugs
- `research` - Learning, exploration
- `review` - Code or documentation review
- `refactor` - Code improvement
- `blocked` - Waiting on dependencies

## Time Tracking Guidelines
- Use actual time spent, not estimates
- Round to nearest 15 minutes
- Examples: "30m", "1h", "2h30m", "1d" (8 hours)

## Critical Success Patterns

### Pattern: Always Get Context First
```
WRONG: Jump straight into coding
RIGHT: pm_list_issues → pm_get_issue → understand context → pm_start_work
```

### Pattern: Log Decisions, Not Just Actions
```
WRONG: pm_log_work --summary "Fixed bug"
RIGHT: pm_log_work --summary "Fixed race condition by adding mutex lock around shared state"
```

### Pattern: Update Status Immediately
```
When state changes, update within 5 minutes:
- Started work → in_progress
- Stuck → blocked  
- Ready for review → review
- Complete → done
```

## Remember
- Check pm_list_issues frequently to stay oriented
- Log work every 30-60 minutes minimum
- Include technical details in all summaries
- Update status as soon as it changes
- Use artifacts to link work to concrete outputs

For complete tool documentation and system details, use `pm_docs`.
