"""Database connection and repository layer for PM MCP Server - NO RAW SQL"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from peewee import *
from peewee import fn
from config import Config
from utils import safe_json_loads

def _safe_json(val, default):
    """Safe JSON parsing with fallback"""
    if not val:
        return default
    try:
        if isinstance(val, (dict, list)):
            return val
        return json.loads(val)
    except Exception:
        return default

def _get_issue_field_json(issue, field_name):
    """Get JSON field from issue safely"""
    return _safe_json(getattr(issue, field_name, None), {})

def _get(obj, name, default=None):
    """Safe attribute getter"""
    return getattr(obj, name, default)

# Initialize database with delayed connection
db_proxy = DatabaseProxy()

class BaseModel(Model):
    """Base model with common functionality"""
    class Meta:
        database = db_proxy

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary safely"""
        data = {}
        for field in self._meta.sorted_fields:
            value = getattr(self, field.name)
            if isinstance(value, datetime):
                data[field.name] = value.isoformat() + 'Z'
            elif hasattr(value, 'to_dict'):
                data[field.name] = value.to_dict()
            elif hasattr(value, 'id'):
                data[field.name] = str(value.id)
            else:
                data[field.name] = value
        return data

class Project(BaseModel):
    """Project model"""
    project_id = CharField(unique=True, index=True, max_length=64)
    project_slug = CharField(index=True, max_length=100)
    absolute_path = CharField(max_length=500)
    metadata = TextField(null=True)  # JSON
    created_utc = DateTimeField(index=True)
    updated_utc = DateTimeField(index=True)

    def get_metadata(self) -> Dict[str, Any]:
        """Safely parse metadata JSON"""
        if not self.metadata:
            return {}
        try:
            return json.loads(self.metadata)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def submodules(self) -> List[Dict[str, Any]]:
        return self.get_metadata().get('submodules', [])

    @property
    def vcs(self) -> Dict[str, Any]:
        return self.get_metadata().get('vcs', {})

class Issue(BaseModel):
    """Issue model with rich content"""
    project = ForeignKeyField(Project, backref='issues', on_delete='CASCADE')
    key = CharField(unique=True, index=True, max_length=50)
    title = CharField(index=True, max_length=200)
    type = CharField(index=True, max_length=20)
    status = CharField(index=True, max_length=20)
    priority = CharField(index=True, max_length=10)
    module = CharField(null=True, index=True, max_length=100)
    owner = CharField(null=True, index=True, max_length=100)
    external_id = CharField(null=True, index=True, max_length=100)

    # Rich content as JSON
    specification = TextField(null=True)
    planning = TextField(null=True)
    implementation = TextField(null=True)
    communication = TextField(null=True)
    analytics = TextField(null=True)

    created_utc = DateTimeField(index=True)
    updated_utc = DateTimeField(index=True)

    def get_json_field(self, field_name: str) -> Dict[str, Any]:
        """Safely parse JSON field"""
        field_value = getattr(self, field_name, None)
        if not field_value:
            return {}
        try:
            return json.loads(field_value)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def description(self) -> str:
        return self.get_json_field('specification').get('description', '')

    @property
    def acceptance_criteria(self) -> List[str]:
        return self.get_json_field('specification').get('acceptance_criteria', [])

    @property
    def dependencies(self) -> List[str]:
        return self.get_json_field('planning').get('dependencies', [])

    @property
    def estimated_effort(self) -> str:
        return self.get_json_field('planning').get('estimated_effort', '')

    @property
    def complexity(self) -> str:
        return self.get_json_field('planning').get('complexity', 'Medium')

    @property
    def branch_hint(self) -> str:
        return self.get_json_field('implementation').get('branch_hint', '')

    def to_rich_dict(self) -> Dict[str, Any]:
        """Convert to dict with all JSON properties expanded"""
        data = self.to_dict()
        data.update({
            'description': self.description,
            'acceptance_criteria': self.acceptance_criteria,
            'dependencies': self.dependencies,
            'estimated_effort': self.estimated_effort,
            'complexity': self.complexity,
            'branch_hint': self.branch_hint,
            'project_slug': self.project.project_slug,
            'project_path': self.project.absolute_path
        })
        return data

class Task(BaseModel):
    """Task model"""
    issue = ForeignKeyField(Issue, backref='tasks', on_delete='CASCADE')
    task_id = CharField(unique=True, index=True, max_length=100)
    title = CharField(max_length=200)
    status = CharField(index=True, max_length=20)
    assignee = CharField(null=True, index=True, max_length=100)
    details = TextField(null=True)  # JSON
    created_utc = DateTimeField(index=True)
    updated_utc = DateTimeField(index=True)

    def get_details(self) -> Dict[str, Any]:
        """Safely parse details JSON"""
        if not self.details:
            return {}
        try:
            return json.loads(self.details)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def checklist(self) -> List[Dict[str, Any]]:
        return self.get_details().get('checklist', [])

    @property
    def notes(self) -> str:
        return self.get_details().get('notes', '')

class WorkLog(BaseModel):
    """WorkLog model"""
    issue = ForeignKeyField(Issue, backref='worklogs', on_delete='CASCADE')
    task = ForeignKeyField(Task, backref='worklogs', on_delete='SET NULL', null=True)
    agent = CharField(index=True, max_length=100)
    timestamp_utc = DateTimeField(index=True)
    activity = CharField(index=True, max_length=50)
    summary = TextField()
    artifacts = TextField(null=True)  # JSON
    context = TextField(null=True)  # JSON

    def get_artifacts(self) -> List[Dict[str, Any]]:
        """Safely parse artifacts JSON"""
        if not self.artifacts:
            return []
        try:
            return json.loads(self.artifacts)
        except (json.JSONDecodeError, TypeError):
            return []

    def get_context(self) -> Dict[str, Any]:
        """Safely parse context JSON"""
        if not self.context:
            return {}
        try:
            return json.loads(self.context)
        except (json.JSONDecodeError, TypeError):
            return {}

class CommandUsage(BaseModel):
    """CommandUsage model for tracking MCP command usage"""
    command_name = CharField(index=True, max_length=100)
    timestamp_utc = DateTimeField(index=True)
    project_id = CharField(null=True, index=True, max_length=64)

class CommandConfig(BaseModel):
    """Command configuration for MCP tools"""
    command_name = CharField(primary_key=True, max_length=100)
    category = CharField(max_length=20)  # required/recommended/optional
    description = TextField()
    enabled = BooleanField(default=True)
    can_disable = BooleanField(default=True)  # False for critical commands
    disabled_at = DateTimeField(null=True)
    disabled_by = CharField(null=True, max_length=100)
    created_utc = DateTimeField(default=datetime.utcnow)
    updated_utc = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = 'command_configs'

class PMDatabase:
    """Database operations wrapper with proper Peewee usage - NO RAW SQL"""

    _db_initialized = False

    # ---------- Converters (models -> dicts) ----------
    @staticmethod
    def _project_to_dict(p: Project) -> Dict[str, Any]:
        """Convert Project model to dict"""
        meta = safe_json_loads(getattr(p, "metadata", None))
        return {
            "project_id": p.project_id,
            "project_slug": p.project_slug,
            "absolute_path": p.absolute_path,
            "metadata": meta,
            "created_utc": p.created_utc.isoformat() + "Z" if isinstance(p.created_utc, datetime) else None,
            "updated_utc": p.updated_utc.isoformat() + "Z" if isinstance(p.updated_utc, datetime) else None,
        }

    @staticmethod
    def _issue_to_dict(i: Issue) -> Dict[str, Any]:
        """Convert Issue model to dict"""
        spec = safe_json_loads(getattr(i, "specification", None))
        plan = safe_json_loads(getattr(i, "planning", None))
        impl = safe_json_loads(getattr(i, "implementation", None))
        comm = safe_json_loads(getattr(i, "communication", None))
        anal = safe_json_loads(getattr(i, "analytics", None))
        return {
            "key": i.key,
            "title": i.title,
            "type": i.type,
            "status": i.status,
            "priority": i.priority,
            "module": i.module,
            "owner": i.owner,
            "project_id": getattr(i.project, "project_id", None),
            "description": spec.get("description", ""),
            "acceptance_criteria": spec.get("acceptance_criteria", []),
            "technical_approach": spec.get("technical_approach", ""),
            "dependencies": plan.get("dependencies", []),
            "estimated_effort": plan.get("estimated_effort"),
            "complexity": plan.get("complexity"),
            "branch_hint": impl.get("branch_hint"),
            "commit_preamble": impl.get("commit_preamble"),
            "commit_trailer": impl.get("commit_trailer"),
            "links": impl.get("links") or {},
            "created_utc": i.created_utc.isoformat() + "Z" if isinstance(i.created_utc, datetime) else None,
            "updated_utc": i.updated_utc.isoformat() + "Z" if isinstance(i.updated_utc, datetime) else None,
        }

    @staticmethod
    def _worklog_to_dict(w: WorkLog) -> Dict[str, Any]:
        """Convert WorkLog model to dict"""
        artifacts = []
        ctx = {}
        try:
            artifacts = json.loads(w.artifacts) if w.artifacts else []
        except Exception:
            artifacts = []
        try:
            ctx = json.loads(w.context) if w.context else {}
        except Exception:
            ctx = {}
        return {
            "issue_key": getattr(w.issue, "key", None),
            "task_id": getattr(getattr(w, "task", None), "task_id", None),
            "agent": w.agent,
            "activity": w.activity,
            "summary": w.summary,
            "artifacts": artifacts,
            "context": ctx,
            "timestamp_utc": w.timestamp_utc.isoformat() + "Z" if isinstance(w.timestamp_utc, datetime) else None,
        }

    @classmethod
    def initialize(cls):
        """Initialize database connection"""
        if cls._db_initialized:
            return

        # Create database path if needed
        db_path = Config.get_database_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        database = SqliteDatabase(str(db_path))
        db_proxy.initialize(database)

        # Create tables if needed
        database.create_tables([Project, Issue, Task, WorkLog, CommandUsage, CommandConfig], safe=True)
        cls._db_initialized = True

    @classmethod
    def connect(cls):
        """Connect to database"""
        if not cls._db_initialized:
            cls.initialize()
        if db_proxy.is_closed():
            db_proxy.connect()

    @classmethod
    def close(cls):
        """Close database connection"""
        if not db_proxy.is_closed():
            db_proxy.close()

    @classmethod
    def get_project(cls, project_id: str) -> Optional[Project]:
        """Get project by ID - returns Peewee model"""
        if not project_id:
            return None
        try:
            return Project.get(Project.project_id == project_id)
        except DoesNotExist:
            return None

    @classmethod
    def get_all_projects(cls) -> List[Project]:
        """Get all projects - returns list of Peewee models"""
        return list(Project.select().order_by(Project.project_slug))

    @classmethod
    def get_issue(cls, issue_key: str) -> Optional[Issue]:
        """Get issue by key - returns Peewee model"""
        if not issue_key:
            return None
        try:
            return Issue.get(Issue.key == issue_key)
        except DoesNotExist:
            return None

    @classmethod
    def get_issue_scoped(cls, project_id: str, issue_key: str) -> Optional[Issue]:
        """Fetch an issue by key but only if it belongs to project_id."""
        if not project_id or not issue_key:
            return None
        try:
            issue = Issue.get(Issue.key == issue_key)
            # Verify it belongs to the right project
            if issue.project.project_id != project_id:
                return None
            return issue
        except DoesNotExist:
            return None

    @classmethod
    def find_issues(cls, project_id: str, **filters) -> List[Issue]:
        """Find issues with filters - returns Peewee models"""
        if not project_id:
            return []
        query = (Issue.select()
                .join(Project)
                .where(Project.project_id == project_id))

        status = filters.get('status')
        priority = filters.get('priority')
        module = filters.get('module')
        search = filters.get('q') or filters.get('query')

        # Exclude archived issues by default unless explicitly requested
        if not status:
            query = query.where(Issue.status != 'archived')
        if status:
            query = query.where(Issue.status == status)
        if priority:
            query = query.where(Issue.priority == priority)
        if module:
            query = query.where(Issue.module == module)
        if search:
            query = query.where(
                (Issue.title.contains(search)) |
                (Issue.specification.contains(search)) |
                (Issue.planning.contains(search))
            )
        return list(query.order_by(Issue.updated_utc.desc()))

    @classmethod
    def find_archived_issues(cls, project_id: str, **filters) -> List[Issue]:
        """Find archived issues with filters - returns Peewee models"""
        if not project_id:
            return []
        query = (Issue.select()
                .join(Project)
                .where((Project.project_id == project_id) & (Issue.status == 'archived')))

        priority = filters.get('priority')
        module = filters.get('module')
        issue_type = filters.get('type')
        search_keyword = filters.get('search_keyword')
        date_from = filters.get('date_from')
        date_to = filters.get('date_to')

        if priority:
            query = query.where(Issue.priority == priority)
        if module:
            query = query.where(Issue.module == module)
        if issue_type:
            query = query.where(Issue.type == issue_type)
        if search_keyword:
            query = query.where(
                (Issue.title.contains(search_keyword)) |
                (Issue.specification.contains(search_keyword))
            )
        if date_from:
            query = query.where(Issue.updated_utc >= date_from)
        if date_to:
            query = query.where(Issue.updated_utc <= date_to)

        return list(query.order_by(Issue.updated_utc.desc()))

    @classmethod
    def get_archived_issue(cls, project_id: str, issue_key: str) -> Optional[Issue]:
        """Get a specific archived issue by key"""
        try:
            if project_id:
                return Issue.select().join(Project).where(
                    (Project.project_id == project_id) &
                    (Issue.key == issue_key) &
                    (Issue.status == 'archived')
                ).first()
            else:
                return Issue.select().where(
                    (Issue.key == issue_key) &
                    (Issue.status == 'archived')
                ).first()
        except Exception:
            return None

    @classmethod
    def get_issue_with_relations(cls, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get issue with tasks and worklogs using Peewee relationships"""
        try:
            issue = Issue.get(Issue.key == issue_key)

            # Use Peewee relationships - no raw SQL!
            tasks = []
            for task in issue.tasks:  # Auto lazy-loaded backref
                task_data = task.to_dict()
                task_data.update({
                    'checklist': task.checklist,
                    'notes': task.notes
                })
                tasks.append(task_data)

            worklogs = []
            for worklog in issue.worklogs.order_by(WorkLog.timestamp_utc.desc()).limit(20):  # Auto lazy-loaded
                worklog_data = worklog.to_dict()
                worklog_data.update({
                    'artifacts': worklog.get_artifacts(),
                    'context': worklog.get_context()
                })
                worklogs.append(worklog_data)

            return {
                'issue': issue.to_rich_dict(),
                'tasks': tasks,
                'worklogs': worklogs,
                'project': {
                    'project_id': issue.project.project_id,
                    'project_slug': issue.project.project_slug,
                    'absolute_path': issue.project.absolute_path
                }
            }
        except DoesNotExist:
            return None

    @classmethod
    def search_issues(cls, query_text: str, project_id: Optional[str] = None, limit: int = 20, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Full-text search using Peewee queries"""
        # Build search conditions
        search_conditions = (
            Issue.title.contains(query_text) |
            Issue.specification.contains(query_text) |
            Issue.planning.contains(query_text) |
            Issue.implementation.contains(query_text)
        )

        query = Issue.select().where(search_conditions)

        # Exclude archived unless explicitly included
        if not include_archived:
            query = query.where(Issue.status != 'archived')

        if project_id:
            query = query.join(Project).where(Project.project_id == project_id)

        query = query.order_by(Issue.updated_utc.desc()).limit(limit)
        return [issue.to_rich_dict() for issue in query]

    @classmethod
    def create_issue(cls, input_model) -> Issue:
        """Create issue from input model - returns Peewee model"""
        project = cls.get_project(input_model.project_id)
        if project is None:
            raise ValueError("Invalid or missing project_id")

        now = datetime.utcnow()

        # Generate issue key
        issue_key = cls.generate_issue_key(project.project_slug)

        spec = {
            "description": input_model.description,
            "acceptance_criteria": getattr(input_model, 'acceptance_criteria', []) or [],
            "technical_approach": getattr(input_model, "technical_approach", "") or ""
        }
        planning = {
            "dependencies": getattr(input_model, 'dependencies', []) or [],
            "stakeholders": getattr(input_model, "stakeholders", []) or [],
            "estimated_effort": getattr(input_model, "estimated_effort", None),
            "complexity": getattr(input_model, "complexity", "Medium"),
            "risks": getattr(input_model, "risks", []) or []
        }
        implementation = {
            "branch_hint": getattr(input_model, "branch_hint", None),
            "commit_preamble": f"[pm {issue_key}]",
            "commit_trailer": f"PM: {issue_key}",
        }

        return Issue.create(
            project=project,
            key=issue_key,
            title=input_model.title,
            type=input_model.type,
            status="proposed",
            priority=getattr(input_model, 'priority', 'P3') or "P3",
            module=getattr(input_model, "module", None),
            owner=getattr(input_model, "owner", None),
            specification=json.dumps(spec),
            planning=json.dumps(planning),
            implementation=json.dumps(implementation),
            created_utc=now,
            updated_utc=now,
        )

    @classmethod
    def create_or_update_task(cls, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update task using Peewee models"""
        # Find issue
        try:
            issue = Issue.get(Issue.key == task_data['issue_key'])
        except DoesNotExist:
            raise ValueError(f"Issue {task_data['issue_key']} not found")

        # Prepare details JSON
        details = json.dumps({
            'checklist': task_data.get('checklist', []),
            'notes': task_data.get('notes', ''),
            'time_estimate': task_data.get('time_estimate', '')
        })

        try:
            # Update existing task
            task = Task.get(Task.task_id == task_data['task_id'])
            task.title = task_data.get('title', task.title)
            task.status = task_data.get('status', task.status)
            task.assignee = task_data.get('assignee', task.assignee)
            task.details = details
            task.updated_utc = datetime.utcnow()
            task.save()
        except DoesNotExist:
            # Create new task
            task = Task.create(
                issue=issue,
                task_id=task_data['task_id'],
                title=task_data['title'],
                status=task_data.get('status', 'todo'),
                assignee=task_data.get('assignee'),
                details=details,
                created_utc=datetime.utcnow(),
                updated_utc=datetime.utcnow()
            )

        result = task.to_dict()
        result.update({
            'checklist': task.checklist,
            'notes': task.notes,
            'issue_key': issue.key
        })
        return result

    @classmethod
    def get_my_queue(cls, project_id: str, owner: Optional[str] = None, limit: int = 20) -> List[Issue]:
        """Get work queue - returns Peewee models"""
        if not project_id:
            return []
        query = (Issue.select()
                .join(Project)
                .where(Project.project_id == project_id))
        if owner:
            query = query.where(Issue.owner == owner)
        query = (query.where(Issue.status.in_(['proposed', 'in_progress']))
                .order_by(Issue.priority.asc(), Issue.updated_utc.desc())
                .limit(limit))
        return list(query)

    @classmethod
    def get_blocked_issues(cls, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get blocked issues using Peewee query"""
        query = Issue.select().where(Issue.status == 'blocked')

        if project_id:
            query = query.join(Project).where(Project.project_id == project_id)

        return [issue.to_rich_dict() for issue in query.order_by(Issue.updated_utc.desc())]

    @classmethod
    def get_recent_worklogs(cls, issue_key: Optional[str] = None,
                           project_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent worklogs using Peewee relationships"""
        query = WorkLog.select()

        if issue_key:
            query = query.join(Issue).where(Issue.key == issue_key)
        elif project_id:
            query = query.join(Issue).join(Project).where(Project.project_id == project_id)

        worklogs = query.order_by(WorkLog.timestamp_utc.desc()).limit(limit)

        result = []
        for worklog in worklogs:
            data = worklog.to_dict()
            data.update({
                'artifacts': worklog.get_artifacts(),
                'context': worklog.get_context(),
                'issue_key': worklog.issue.key
            })
            result.append(data)
        return result

    @classmethod
    def update_issue_planning_estimate(cls, issue, effort: str, complexity: Optional[str], reasoning: Optional[str]):
        """Update issue planning with estimates"""
        planning = _get_issue_field_json(issue, 'planning')
        planning["estimated_effort"] = effort
        if complexity:
            planning["complexity"] = complexity
        if reasoning:
            notes = planning.get("estimate_notes", [])
            notes.append({
                "timestamp_utc": datetime.utcnow().isoformat() + "Z",
                "reasoning": reasoning
            })
            planning["estimate_notes"] = notes
        issue.planning = json.dumps(planning)
        issue.updated_utc = datetime.utcnow()
        issue.save()
        return issue

    @classmethod
    def create_task(cls, issue, title: str, assignee: Optional[str], details: Optional[Dict[str, Any]]):
        """Create task with auto-generated ID"""
        # FIX: use .count() instead of fn.COUNT()
        existing = Task.select().where(Task.issue == issue).count() or 0
        task_id = f"{issue.key}-T{existing + 1}"
        t = Task.create(
            issue=issue,
            task_id=task_id,
            title=title,
            status="todo",
            assignee=assignee,
            details=json.dumps(details or {}),
            created_utc=datetime.utcnow(),
            updated_utc=datetime.utcnow(),
        )
        return t

    @classmethod
    def get_task(cls, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        try:
            return Task.get(Task.task_id == task_id)
        except DoesNotExist:
            return None

    @classmethod
    def update_task(cls, task, title=None, status=None, assignee=None, details=None):
        """Update task fields"""
        if title is not None:
            task.title = title
        if status is not None:
            task.status = status
        if assignee is not None:
            task.assignee = assignee
        if details is not None:
            task.details = json.dumps(details)
        task.updated_utc = datetime.utcnow()
        task.save()
        return task

    @classmethod
    def get_issues(cls, project_id: Optional[str] = None,
                   owner: Optional[str] = None,
                   status: Optional[str] = None,
                   priority: Optional[str] = None,
                   module: Optional[str] = None,
                   limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Return issues as rich dicts, optionally filtered.
        This is a dict-returning convenience wrapper used by server.py.
        """
        query = Issue.select()
        if project_id:
            query = query.join(Project).where(Project.project_id == project_id)
        if owner:
            query = query.where(Issue.owner == owner)
        # Exclude archived issues by default unless explicitly filtered by status
        if not status:
            query = query.where(Issue.status != 'archived')
        if status:
            query = query.where(Issue.status == status)
        if priority:
            query = query.where(Issue.priority == priority)
        if module:
            query = query.where(Issue.module == module)
        query = query.order_by(Issue.updated_utc.desc()).limit(limit)
        return [i.to_rich_dict() for i in query]

    @classmethod
    def create_or_update_issue(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a single issue by key with incoming dict fields, mirroring IssueRepository logic.
        Returns a rich dict.
        """
        if "key" not in data:
            raise ValueError("create_or_update_issue requires 'key'")
        issue = cls.get_issue(data["key"])
        now = datetime.utcnow()

        # Prepare JSON fields
        spec = _safe_json(getattr(issue, "specification", None), {}) if issue else {}
        plan = _safe_json(getattr(issue, "planning", None), {}) if issue else {}
        impl = _safe_json(getattr(issue, "implementation", None), {}) if issue else {}

        # Merge incoming values
        if "description" in data or "acceptance_criteria" in data or "technical_approach" in data:
            spec.update({
                "description": data.get("description", spec.get("description", "")),
                "acceptance_criteria": data.get("acceptance_criteria", spec.get("acceptance_criteria", [])),
                "technical_approach": data.get("technical_approach", spec.get("technical_approach", "")),
            })

        if any(k in data for k in ("dependencies", "stakeholders", "estimated_effort", "complexity", "risks")):
            plan.update({
                "dependencies": data.get("dependencies", plan.get("dependencies", [])),
                "stakeholders": data.get("stakeholders", plan.get("stakeholders", [])),
                "estimated_effort": data.get("estimated_effort", plan.get("estimated_effort", None)),
                "complexity": data.get("complexity", plan.get("complexity", "Medium")),
                "risks": data.get("risks", plan.get("risks", [])),
            })

        if any(k in data for k in ("branch_hint", "commit_preamble", "commit_trailer", "links")):
            impl.update({
                "branch_hint": data.get("branch_hint", impl.get("branch_hint", None)),
                "commit_preamble": data.get("commit_preamble", impl.get("commit_preamble", None)),
                "commit_trailer": data.get("commit_trailer", impl.get("commit_trailer", None)),
                "links": data.get("links", impl.get("links", {})) or {},
            })

        if issue:
            # Update scalar fields
            for f in ("title", "type", "status", "priority", "module", "owner", "external_id"):
                if f in data and data[f] is not None:
                    setattr(issue, f, data[f])
            issue.specification = json.dumps(spec)
            issue.planning = json.dumps(plan)
            issue.implementation = json.dumps(impl)
            issue.updated_utc = now
            issue.save()
        else:
            # Need a project to create a new one
            project_id = data.get("project_id")
            project = cls.get_project(project_id) if project_id else None
            if not project:
                raise ValueError("Project not found for issue creation")
            issue = Issue.create(
                project=project,
                key=data["key"],
                title=data["title"],
                type=data["type"],
                status=data.get("status", "proposed"),
                priority=data.get("priority", "P3"),
                module=data.get("module"),
                owner=data.get("owner"),
                external_id=data.get("external_id"),
                specification=json.dumps(spec),
                planning=json.dumps(plan),
                implementation=json.dumps(impl),
                created_utc=now,
                updated_utc=now,
            )

        return issue.to_rich_dict()

    @classmethod
    def add_worklog(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convenience wrapper expected by server.py.
        Creates a WorkLog from dict and returns a dict.
        """
        issue = cls.get_issue(data["issue_key"])
        if not issue:
            raise ValueError(f"Issue not found: {data['issue_key']}")

        task = None
        if data.get("task_id"):
            task = cls.get_task(data["task_id"])

        wl = WorkLog.create(
            issue=issue,
            task=task,
            agent=data.get("agent", "agent:claude-code"),
            timestamp_utc=datetime.utcnow(),
            activity=data["activity"],
            summary=data["summary"],
            artifacts=json.dumps(data.get("artifacts") or []),
            context=json.dumps(data.get("context") or {}),
        )
        return wl.to_dict()

    @classmethod
    def append_worklog(cls, issue, agent: str, activity: str, summary: str,
                      artifacts: Optional[List[Dict[str, Any]]], context: Optional[Dict[str, Any]],
                      task=None):
        """Add worklog entry"""
        wl = WorkLog.create(
            issue=issue,
            task=task,
            agent=agent,
            timestamp_utc=datetime.utcnow(),
            activity=activity,
            summary=summary,
            artifacts=json.dumps(artifacts or []),
            context=json.dumps(context or {}),
        )
        return wl

    @classmethod
    def project_metrics(cls, project, include_submodule_breakdown=False):
        """Calculate project metrics with optional submodule breakdown"""
        issues = list(project.issues)
        status_counts = {}
        priority_counts = {}
        module_counts = {}
        submodule_metrics = {}

        for i in issues:
            status_counts[i.status] = status_counts.get(i.status, 0) + 1
            priority_counts[i.priority] = priority_counts.get(i.priority, 0) + 1
            if i.module:
                module_counts[i.module] = module_counts.get(i.module, 0) + 1

                # If this module is a submodule, track detailed metrics
                if include_submodule_breakdown:
                    if i.module not in submodule_metrics:
                        submodule_metrics[i.module] = {
                            "total": 0,
                            "by_status": {},
                            "by_priority": {},
                            "by_type": {},
                            "in_progress_count": 0,
                            "blocked_count": 0,
                            "completion_rate": 0.0
                        }
                    sub = submodule_metrics[i.module]
                    sub["total"] += 1
                    sub["by_status"][i.status] = sub["by_status"].get(i.status, 0) + 1
                    sub["by_priority"][i.priority] = sub["by_priority"].get(i.priority, 0) + 1
                    sub["by_type"][i.type] = sub["by_type"].get(i.type, 0) + 1
                    if i.status == "in_progress":
                        sub["in_progress_count"] += 1
                    elif i.status == "blocked":
                        sub["blocked_count"] += 1

        # Calculate completion rates for submodules
        if include_submodule_breakdown:
            for module_name, metrics in submodule_metrics.items():
                done_count = metrics["by_status"].get("done", 0) + metrics["by_status"].get("archived", 0)
                if metrics["total"] > 0:
                    metrics["completion_rate"] = round(done_count / metrics["total"] * 100, 1)

        recent_work = (WorkLog
                      .select()
                      .join(Issue)
                      .where(Issue.project == project)
                      .order_by(WorkLog.timestamp_utc.desc())
                      .limit(20))
        recent = []
        for w in recent_work:
            recent.append({
                "issue_key": w.issue.key,
                "task_id": w.task.task_id if w.task else None,
                "agent": w.agent,
                "activity": w.activity,
                "summary": w.summary,
                "timestamp_utc": w.timestamp_utc.isoformat() + "Z",
            })

        result = {
            "counts": {
                "total": len(issues),
                "by_status": status_counts,
                "by_priority": priority_counts,
                "by_module": module_counts,
            },
            "recent_work": recent,
        }

        if include_submodule_breakdown and submodule_metrics:
            result["submodule_metrics"] = submodule_metrics

        return result

    @classmethod
    def owner_capacity(cls, project):
        """Get capacity by owner"""
        rows = (Issue
               .select(Issue.owner, fn.COUNT(Issue.id).alias('count'))
               .where(Issue.project == project)
               .group_by(Issue.owner))
        result = []
        for r in rows:
            result.append({"owner": r.owner, "issue_count": r.count})
        return result

    @classmethod
    def log_command_usage(cls, command_name: str, project_id: Optional[str] = None):
        """Log MCP command usage for analytics"""
        try:
            CommandUsage.create(
                command_name=command_name,
                timestamp_utc=datetime.utcnow(),
                project_id=project_id
            )
        except Exception:
            pass

    @classmethod
    def get_command_usage_stats(cls, days: int = 30) -> List[Dict[str, Any]]:
        """Get command usage statistics for the last N days"""
        cutoff = datetime.utcnow() - timedelta(days=days)

        usage = (CommandUsage
                .select(CommandUsage.command_name,
                       fn.COUNT(CommandUsage.id).alias('count'),
                       fn.MAX(CommandUsage.timestamp_utc).alias('last_used'))
                .where(CommandUsage.timestamp_utc >= cutoff)
                .group_by(CommandUsage.command_name)
                .order_by(fn.COUNT(CommandUsage.id).desc()))

        results = []
        for u in usage:
            results.append({
                'command_name': u.command_name,
                'count': u.count,
                'last_used': u.last_used.isoformat() + 'Z' if u.last_used else None
            })
        return results

    @classmethod
    def generate_issue_key(cls, project_slug: str) -> str:
        """Generate unique issue key with proper collision handling"""
        # Get max issue number for this project to avoid races
        prefix = project_slug.upper()[:4].replace('-', '')
        if not prefix:
            prefix = "PROJ"

        # Use date-based format
        date_part = datetime.now().strftime("%Y%m")

        # Find max number for this month to avoid collisions
        pattern = f"{prefix}-{date_part}-%"
        existing = (Issue.select()
                   .where(Issue.key.startswith(f"{prefix}-{date_part}-"))
                   .order_by(Issue.key.desc())
                   .limit(1))

        max_num = 0
        for issue in existing:
            try:
                parts = issue.key.split('-')
                if len(parts) >= 3:
                    max_num = max(max_num, int(parts[2]))
            except (ValueError, IndexError):
                pass

        return f"{prefix}-{date_part}-{max_num + 1:03d}"

# Context manager for database operations
class DatabaseSession:
    """Context manager for database operations"""
    def __enter__(self):
        PMDatabase.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        PMDatabase.close()