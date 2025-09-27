# Web UI Integration Context for MCP Server Development

**For LLM agents working on the MCP server without access to the full frontend codebase**

---

## 📋 Overview

The MCP server integrates with a Flask-based web UI (Jira-lite) that provides human oversight and management capabilities. This document provides all necessary context for MCP development without requiring access to the frontend source code.

---

## 🗄️ Database Schema & Models

### **SQLite Database Structure**

The MCP server MUST work with this exact Peewee model structure:

```python
# Located at: data/jira_lite.db

class Project(BaseModel):
    project_id = CharField(unique=True, index=True, max_length=64)      # pn_abc123...
    project_slug = CharField(index=True, max_length=100)               # project-name
    absolute_path = CharField(max_length=500)                          # /path/to/project
    metadata = TextField(null=True)                                    # JSON string
    created_utc = DateTimeField(index=True)                           # datetime object
    updated_utc = DateTimeField(index=True)                           # datetime object

class Issue(BaseModel):
    project = ForeignKeyField(Project, backref='issues')              # Auto-lazy-loaded
    key = CharField(unique=True, index=True, max_length=50)           # PROJ-001
    title = CharField(index=True, max_length=200)                     # Issue title
    type = CharField(index=True, max_length=20)                       # feature|bug|refactor|chore|spike
    status = CharField(index=True, max_length=20)                     # proposed|in_progress|review|done|canceled|blocked
    priority = CharField(index=True, max_length=10)                   # P1|P2|P3|P4|P5
    module = CharField(null=True, index=True, max_length=100)         # Module/component
    owner = CharField(null=True, index=True, max_length=100)          # agent:claude-code
    external_id = CharField(null=True, index=True, max_length=100)    # Optional external ref

    # Rich LLM content as JSON TEXT fields
    specification = TextField(null=True)                              # JSON string
    planning = TextField(null=True)                                   # JSON string
    implementation = TextField(null=True)                             # JSON string
    communication = TextField(null=True)                             # JSON string
    analytics = TextField(null=True)                                 # JSON string

    created_utc = DateTimeField(index=True)                           # datetime object
    updated_utc = DateTimeField(index=True)                           # datetime object

class Task(BaseModel):
    issue = ForeignKeyField(Issue, backref='tasks')                   # Parent issue
    task_id = CharField(unique=True, index=True, max_length=100)      # PROJ-001-T1
    title = CharField(max_length=200)                                 # Task title
    status = CharField(index=True, max_length=20)                     # todo|doing|blocked|review|done
    assignee = CharField(null=True, index=True, max_length=100)       # Who's working on it
    details = TextField(null=True)                                    # JSON string
    created_utc = DateTimeField(index=True)
    updated_utc = DateTimeField(index=True)

class WorkLog(BaseModel):
    issue = ForeignKeyField(Issue, backref='worklogs')               # Parent issue
    task = ForeignKeyField(Task, backref='worklogs', null=True)      # Optional parent task
    agent = CharField(index=True, max_length=100)                    # Who did the work
    timestamp_utc = DateTimeField(index=True)                        # When
    activity = CharField(index=True, max_length=50)                  # What type of work
    summary = TextField()                                             # What was done
    artifacts = TextField(null=True)                                  # JSON string
    context = TextField(null=True)                                   # JSON string
```

### **Critical JSON Field Structures**

The web UI expects these exact JSON structures in the TEXT fields:

#### **Issue.specification (JSON)**
```json
{
  "description": "Comprehensive markdown description",
  "acceptance_criteria": ["Criterion 1", "Criterion 2"],
  "technical_approach": "Technical implementation details",
  "business_requirements": ["Requirement 1", "Requirement 2"]
}
```

#### **Issue.planning (JSON)**
```json
{
  "dependencies": ["OTHER-ISSUE-KEY"],
  "stakeholders": ["Product Team", "Security Team"],
  "estimated_effort": "2-3 days",
  "complexity": "Medium",
  "risks": ["Risk description"]
}
```

#### **Issue.implementation (JSON)**
```json
{
  "branch_hint": "feat/proj-001-feature-name",
  "commit_preamble": "[pm PROJ-001]",
  "commit_trailer": "PM: PROJ-001",
  "links": {"repo": "file:///path/to/repo"},
  "artifacts": ["file1.py", "file2.py"]
}
```

#### **Project.metadata (JSON)**
```json
{
  "submodules": [
    {
      "name": "backend",
      "path": "src/backend",
      "absolute_path": "/full/path/to/src/backend",
      "manage_separately": true
    }
  ],
  "vcs": {
    "git_root": "/path/to/project",
    "default_branch": "main"
  },
  "mcp": {
    "pm_server_name": "pm",
    "version": ">=1.0.0"
  }
}
```

---

## 🌐 Web UI Integration Points

### **Flask API Endpoints the MCP Server Must Support**

The web UI makes these API calls that the MCP server should be compatible with:

```python
# Project registration
POST /api/projects/register
{
  "project_id": "pn_abc123...",
  "project_slug": "project-name",
  "absolute_path": "/path/to/project",
  "submodules": [...],
  "vcs": {...},
  "mcp": {...}
}

# Issue operations
POST /api/issues/upsert
{
  "project_id": "pn_abc123...",
  "key": "PROJ-001",
  "title": "Issue title",
  "type": "feature",
  "status": "proposed",
  "priority": "P3",
  "module": "backend",
  "description": "Rich markdown content",
  "acceptance_criteria": ["Criterion 1"],
  "branch_hint": "feat/proj-001-name"
}

# Work logging
POST /api/worklog/append
{
  "issue_key": "PROJ-001",
  "agent": "agent:claude-code",
  "activity": "code",
  "summary": "Work description",
  "artifacts": [{"type": "file", "path": "src/main.py"}]
}
```

### **Expected Data Flow**

1. **MCP Tools** → **SQLite Database** → **Web UI** displays changes
2. **Web UI Forms** → **SQLite Database** → **MCP Tools** can query updates
3. **Audit Events** → **JSONL File** → **Web UI** can show activity timeline

---

## 🎨 Web UI Display Requirements

### **Issue Display Expectations**

The web UI renders issues expecting these fields to be populated:

```python
# Required for dashboard display
issue.key              # Displayed in tables
issue.title            # Main display text
issue.status           # Status badges (proposed|in_progress|review|done|blocked)
issue.priority         # Priority badges (P1|P2|P3|P4|P5)
issue.type             # Type badges (feature|bug|refactor|chore|spike)
issue.module           # Module grouping
issue.updated_utc      # "Last updated" timestamps

# Required for detail pages
issue.description      # Rendered as markdown
issue.acceptance_criteria  # Displayed as checklist
issue.branch_hint      # Git integration info
issue.dependencies     # Related issues list
issue.estimated_effort # Planning information
```

### **Rich Content Rendering**

The web UI renders markdown content from these fields:
- `issue.description` → Full markdown rendering with syntax highlighting
- `issue.technical_approach` → Technical specification display
- Task checklists → Interactive checkbox displays
- Worklog summaries → Activity timeline

### **Status Flow Logic**

The web UI implements this status workflow:
```
proposed → in_progress → review → done
    ↓           ↓           ↓
 canceled    blocked    blocked
```

### **Module Organization**

Issues are grouped by module in the web UI:
```python
# From project.submodules
for submodule in project.submodules:
    module_issues = issues.filter(module=submodule.name)
    # Display in separate cards/swimlanes
```

---

## 🔄 Bidirectional Sync Requirements

### **MCP → Web UI**

When MCP tools modify data, the web UI should immediately reflect:

1. **Issue Creation** → Appears in project dashboard
2. **Status Changes** → Updates dashboard counters and badges
3. **Work Logging** → Shows in activity timelines
4. **Task Creation** → Displays in issue detail pages

### **Web UI → MCP**

When humans modify data via web forms, MCP tools should see:

1. **Issue Edits** → `pm_get_issue` returns updated content
2. **New Issues** → `pm_list_issues` includes web-created issues
3. **Status Updates** → `pm_status` reflects current state
4. **Manual Work Logs** → `pm_daily_standup` includes all activity

### **Shared Database Contract**

Both systems work through the same SQLite database, so:
- **No caching** - Always read fresh data from database
- **Proper transactions** - Use database transactions for multi-step operations
- **Consistent formatting** - JSON fields must match expected structure
- **Timestamp handling** - Use proper datetime objects, not strings

---

## 🎯 MCP Tool Requirements

### **Data Format Expectations**

MCP tools must return data that the web UI can consume:

```python
# Issue data format expected by web UI
{
  "key": "PROJ-001",
  "title": "Issue title",
  "status": "in_progress",           # Must be valid status
  "priority": "P2",                 # Must be P1-P5
  "type": "feature",                # Must be valid type
  "module": "backend",              # Must match project modules
  "description": "Markdown content", # Rich content for rendering
  "acceptance_criteria": ["List"],   # For checklist display
  "branch_hint": "feat/proj-001-name", # For git integration display
  "created_utc": "2025-09-27T07:00:00Z",  # ISO format strings
  "updated_utc": "2025-09-27T07:00:00Z"   # ISO format strings
}
```

### **Error Handling Standards**

MCP tools should return errors in this format for web UI compatibility:

```python
{
  "success": false,
  "message": "Human-readable error message",
  "data": {"error_details": "..."},
  "hints": ["Suggestion 1", "Suggestion 2"]
}
```

### **Required Tool Behaviors**

For web UI integration, these tools MUST work properly:

1. **`pm_init_project`** - Web UI needs projects to exist
2. **`pm_create_issue`** - Web UI displays created issues
3. **`pm_update_issue`** - Web UI needs to sync changes
4. **`pm_log_work`** - Web UI shows work activity
5. **`pm_get_issue`** - Web UI needs detailed issue data

---

## 🔧 Technical Integration Notes

### **Database Connection Sharing**

Both MCP server and web UI use the same SQLite file:
- **File location:** `data/jira_lite.db`
- **Connection handling:** Peewee with auto-connect/disconnect
- **Concurrent access:** SQLite handles multiple readers, single writer
- **Transactions:** Use `with db.atomic():` for multi-operation changes

### **Peewee ORM Usage**

The web UI uses this exact Peewee syntax - MCP server should match:

```python
# Getting data (what web UI does)
project = Project.get(Project.project_id == project_id)
issues = list(project.issues.where(Issue.status == 'in_progress'))
tasks = list(issue.tasks)  # Auto lazy-loaded backref
worklogs = list(issue.worklogs.order_by(WorkLog.timestamp_utc.desc()))

# Creating data (what MCP tools should do)
issue = Issue.create(
    project=project,
    key=issue_key,
    title=title,
    type=type,
    specification=json.dumps(spec_data),
    planning=json.dumps(planning_data)
)

# Updating data
issue.status = 'in_progress'
issue.updated_utc = datetime.utcnow()
issue.save()
```

### **JSON Field Parsing**

The web UI expects consistent JSON parsing - MCP tools should use:

```python
def get_json_field(model_instance, field_name):
    """Safe JSON field parsing"""
    field_value = getattr(model_instance, field_name, None)
    if not field_value:
        return {}
    try:
        return json.loads(field_value)
    except (json.JSONDecodeError, TypeError):
        return {}

# Usage
spec = get_json_field(issue, 'specification')
description = spec.get('description', '')
acceptance = spec.get('acceptance_criteria', [])
```

### **Timestamp Handling**

**Critical:** Web UI templates expect datetime objects, not strings:

```python
# CORRECT - Use datetime objects
issue.created_utc = datetime.utcnow()  # Peewee DateTimeField
issue.updated_utc = datetime.utcnow()

# WRONG - Don't use ISO strings in database
issue.created_utc = "2025-09-27T07:00:00Z"  # Will cause template errors
```

Templates use: `{{ issue.created_utc.strftime('%Y-%m-%d') }}`

---

## 🎨 Web UI Feature Expectations

### **Project Dashboard Display**

Web UI shows project cards with:
- **Project name** and **project_id** preview
- **Submodule count** from `metadata.submodules`
- **Issue counts** by status (calculated from database)
- **Created date** formatted from `created_utc`

### **Issue Detail Pages**

Web UI renders comprehensive issue pages with:
- **Markdown content** from `specification.description`
- **Acceptance criteria** as bulleted checklist
- **Git integration** info (branch_hint, commit_preamble)
- **Related tasks** from `issue.tasks` backref
- **Work timeline** from `issue.worklogs` backref
- **Module organization** by `issue.module`

### **Dashboard Metrics**

Web UI calculates these metrics from database:
```python
# Status distribution
status_counts = {}
for issue in issues:
    status_counts[issue.status] = status_counts.get(issue.status, 0) + 1

# Priority breakdown
priority_counts = {}
for issue in issues:
    priority_counts[issue.priority] = priority_counts.get(issue.priority, 0) + 1

# Module grouping
module_issues = {}
for issue in issues:
    if issue.module:
        module_issues.setdefault(issue.module, []).append(issue)
```

---

## 🔗 API Integration Points

### **Registration Endpoint**

The web UI provides `/api/projects/register` that expects:

```python
POST /api/projects/register
Content-Type: application/json

{
  "project_id": "pn_abc123...",
  "project_slug": "project-name",
  "absolute_path": "/path/to/project",
  "submodules": [
    {
      "name": "backend",
      "path": "src/backend",
      "absolute_path": "/full/path/to/src/backend",
      "manage_separately": true
    }
  ],
  "vcs": {
    "git_root": "/path/to/project",
    "default_branch": "main"
  },
  "mcp": {
    "pm_server_name": "pm",
    "version": ">=1.0.0"
  }
}

# Response
{
  "project_id": "pn_abc123...",
  "slug": "project-name",
  "dashboard_url": "http://127.0.0.1:1929/pn_abc123..."
}
```

### **Web UI Form Integration**

When humans create/edit issues via web forms, data is saved in this format:

```python
# Issue creation from web form
issue_data = {
    'type': form_data['type'],                    # Select dropdown
    'title': form_data['title'],                  # Text input
    'priority': form_data['priority'],            # Select dropdown
    'module': form_data['module'],                # Select from project submodules
    'description': form_data['description'],      # Large textarea with markdown
    'acceptance': form_data['acceptance'].split('\n'),  # Textarea → list
    'owner': form_data['owner'],                  # Text input
    'estimated_effort': form_data['estimated_effort'],  # Text input
    'complexity': form_data['complexity']         # Select dropdown
}
```

### **Markdown Rendering Pipeline**

The web UI uses this markdown pipeline:

```python
# In templates
{{ render_markdown(issue.description) }}  # Converts markdown → safe HTML

# Python function
def render_markdown(text):
    html = markdown.markdown(text, extensions=['fenced_code', 'tables'])
    clean_html = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
    return Markup(clean_html)
```

**MCP tools should provide markdown-formatted content** for proper web display.

---

## 🚦 Workflow Integration

### **Status Flow Management**

The web UI enforces this status workflow:

```python
VALID_TRANSITIONS = {
    'proposed': ['in_progress', 'canceled'],
    'in_progress': ['review', 'blocked', 'canceled'],
    'review': ['done', 'in_progress', 'blocked'],
    'blocked': ['in_progress', 'canceled'],
    'done': ['in_progress'],      # Allow reopening
    'canceled': ['proposed']      # Allow revival
}
```

**MCP status update tools must validate transitions.**

### **Git Integration Display**

Web UI shows git information from these fields:
- `issue.branch_hint` → "Suggested branch name"
- `issue.commit_preamble` → "Commit prefix: [pm PROJ-001]"
- `issue.commit_trailer` → "Commit trailer: PM: PROJ-001"

**MCP git tools should populate these fields.**

### **Activity Timeline**

Web UI builds activity timelines from:
```python
# Recent activity query
recent_worklogs = (WorkLog.select()
                   .join(Issue)
                   .where(Issue.project == project)
                   .order_by(WorkLog.timestamp_utc.desc())
                   .limit(20))

# Displayed as
for worklog in recent_worklogs:
    activity_type = worklog.activity     # code|test|plan|etc
    summary = worklog.summary           # Human-readable description
    agent = worklog.agent              # Who did the work
    artifacts = json.loads(worklog.artifacts or '[]')  # Files/commits
```

---

## 📊 Expected MCP Tool Behaviors

### **Project Initialization**

`pm_init_project` should create database records that web UI can display:

```python
# Create Project record
project = Project.create(
    project_id=f"pn_{hash}",
    project_slug=directory_name,
    absolute_path=str(project_path),
    metadata=json.dumps({
        'submodules': detected_modules,
        'vcs': git_info,
        'mcp': mcp_config
    }),
    created_utc=datetime.utcnow(),
    updated_utc=datetime.utcnow()
)
```

### **Issue Creation**

`pm_create_issue` should create rich issues that web UI can render:

```python
# Create Issue record
issue = Issue.create(
    project=project,
    key=generated_key,
    title=input_title,
    type=input_type,
    status='proposed',
    priority=input_priority,
    module=input_module,
    owner='agent:claude-code',
    specification=json.dumps({
        'description': markdown_description,
        'acceptance_criteria': criteria_list,
        'technical_approach': technical_details
    }),
    planning=json.dumps({
        'estimated_effort': effort_estimate,
        'complexity': complexity_level,
        'stakeholders': stakeholder_list
    }),
    implementation=json.dumps({
        'branch_hint': f"feat/{key.lower()}-{slug}",
        'commit_preamble': f"[pm {key}]",
        'commit_trailer': f"PM: {key}"
    }),
    created_utc=datetime.utcnow(),
    updated_utc=datetime.utcnow()
)
```

### **Work Logging**

`pm_log_work` should create worklog entries for web timeline:

```python
worklog = WorkLog.create(
    issue=issue,
    task=task_if_specified,
    agent='agent:claude-code',
    activity=activity_type,        # code|test|plan|review|etc
    summary=work_description,      # Human-readable summary
    artifacts=json.dumps([         # Files, commits, links
        {"type": "file", "path": "src/main.py"},
        {"type": "commit", "sha": "abc123", "message": "..."}
    ]),
    context=json.dumps({           # Additional context
        "time_spent": "2h",
        "blockers": "None",
        "decisions": "Chose approach X over Y"
    }),
    timestamp_utc=datetime.utcnow()
)
```

---

## ⚠️ Critical Constraints

### **Database Schema Immutability**

**DO NOT CHANGE** the database schema - the web UI depends on these exact field names and types. If you need new fields, add them as JSON within existing TEXT fields.

### **Relationship Integrity**

Maintain these foreign key relationships:
- `Issue.project` → `Project`
- `Task.issue` → `Issue`
- `WorkLog.issue` → `Issue`
- `WorkLog.task` → `Task` (optional)

### **JSON Field Consistency**

Always use the documented JSON structures. The web UI templates expect specific field names and will break if they change.

### **Datetime vs String Handling**

- **Database:** Store as datetime objects (Peewee DateTimeField)
- **API responses:** Convert to ISO strings with 'Z' suffix
- **Templates:** Expect datetime objects for `.strftime()` calls

---

## 🧪 Testing Integration

### **Verify Web UI Compatibility**

After implementing MCP tools, verify:

1. **Create issue via MCP** → **Check web UI shows it**
2. **Update status via MCP** → **Check dashboard counters update**
3. **Log work via MCP** → **Check activity timeline**
4. **Create via web UI** → **Check MCP tools can query it**

### **Database Verification**

Use these queries to verify MCP tools are creating proper data:

```sql
-- Check project structure
SELECT project_id, project_slug,
       json_extract(metadata, '$.submodules') as modules
FROM project;

-- Check issue data
SELECT key, title, status,
       json_extract(specification, '$.description') as desc
FROM issue;

-- Check relationships
SELECT i.key, i.title, count(t.id) as task_count, count(w.id) as worklog_count
FROM issue i
LEFT JOIN task t ON t.issue_id = i.id
LEFT JOIN worklog w ON w.issue_id = i.id
GROUP BY i.key;
```

---

## 🎉 Success Criteria

The MCP server integration is successful when:

✅ **Project initialization** creates records web UI can display
✅ **Issue creation** via MCP appears in web dashboard
✅ **Work logging** via MCP shows in web activity timeline
✅ **Status updates** via MCP reflect in web UI badges/counters
✅ **Git integration** populates branch/commit fields web UI displays
✅ **Rich content** (markdown descriptions) renders properly in web UI
✅ **Error handling** provides helpful messages for both MCP and web users

This context should be sufficient for MCP development without requiring access to the full Flask frontend codebase.