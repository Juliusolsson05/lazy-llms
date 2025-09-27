import json
import uuid
from datetime import datetime
from peewee import *
from pathlib import Path

# SQLite database
DATABASE_PATH = Path(__file__).parent.parent.parent / 'data' / 'jira_lite.db'
DATABASE_PATH.parent.mkdir(exist_ok=True)
db = SqliteDatabase(str(DATABASE_PATH))

class BaseModel(Model):
    """Base model with common functionality"""
    class Meta:
        database = db

    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        data = {}
        for field in self._meta.sorted_fields:
            value = getattr(self, field.name)
            if isinstance(value, datetime):
                data[field.name] = value.isoformat() + 'Z'
            elif hasattr(value, 'to_dict'):
                data[field.name] = value.to_dict()
            elif hasattr(value, 'id'):
                data[field.name] = value.id
            else:
                data[field.name] = value
        return data

class Project(BaseModel):
    """Project model with clean Django-style relationships"""
    project_id = CharField(unique=True, index=True, max_length=64)
    project_slug = CharField(index=True, max_length=100)
    absolute_path = CharField(max_length=500)
    metadata = TextField(null=True)  # JSON string for submodules, vcs, mcp config
    created_utc = DateTimeField(default=datetime.utcnow, index=True)
    updated_utc = DateTimeField(default=datetime.utcnow)

    @property
    def submodules(self):
        """Get submodules from metadata JSON"""
        if not self.metadata:
            return []
        try:
            data = json.loads(self.metadata)
            return data.get('submodules', [])
        except (json.JSONDecodeError, TypeError):
            return []

    @property
    def vcs(self):
        """Get VCS info from metadata JSON"""
        if not self.metadata:
            return {}
        try:
            data = json.loads(self.metadata)
            return data.get('vcs', {})
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def mcp(self):
        """Get MCP config from metadata JSON"""
        if not self.metadata:
            return {}
        try:
            data = json.loads(self.metadata)
            return data.get('mcp', {})
        except (json.JSONDecodeError, TypeError):
            return {}

    def save(self, *args, **kwargs):
        self.updated_utc = datetime.utcnow()
        return super().save(*args, **kwargs)

    def to_dict(self):
        """Enhanced to_dict with metadata properties"""
        data = super().to_dict()
        data.update({
            'submodules': self.submodules,
            'vcs': self.vcs,
            'mcp': self.mcp
        })
        return data

class Issue(BaseModel):
    """Issue model with rich LLM content as JSON"""
    project = ForeignKeyField(Project, backref='issues', on_delete='CASCADE')
    key = CharField(unique=True, index=True, max_length=50)
    title = CharField(index=True, max_length=200)
    type = CharField(index=True, max_length=20)  # feature, bug, refactor, chore, spike
    status = CharField(index=True, max_length=20)  # proposed, in_progress, review, done, canceled, blocked
    priority = CharField(index=True, max_length=10)  # P1, P2, P3, P4, P5
    module = CharField(null=True, index=True, max_length=100)
    owner = CharField(null=True, index=True, max_length=100)
    external_id = CharField(null=True, index=True, max_length=100)

    # Rich LLM content as JSON strings
    specification = TextField(null=True)     # problem_statement, technical_approach, acceptance_criteria
    planning = TextField(null=True)          # dependencies, risks, stakeholders, milestones
    implementation = TextField(null=True)    # tasks, branch, commits, artifacts
    communication = TextField(null=True)     # updates, comments, notifications
    analytics = TextField(null=True)         # time_tracking, velocity, estimates

    created_utc = DateTimeField(default=datetime.utcnow, index=True)
    updated_utc = DateTimeField(default=datetime.utcnow, index=True)

    # Convenient property accessors for JSON fields
    @property
    def description(self):
        """Get description from specification JSON"""
        spec = self._get_json_field('specification')
        return spec.get('description', '')

    @property
    def acceptance(self):
        """Get acceptance criteria from specification JSON"""
        spec = self._get_json_field('specification')
        return spec.get('acceptance_criteria', [])

    @property
    def acceptance_criteria(self):
        """Alias for acceptance"""
        return self.acceptance

    @property
    def dependencies(self):
        """Get dependencies from planning JSON"""
        plan = self._get_json_field('planning')
        return plan.get('dependencies', [])

    @property
    def stakeholders(self):
        """Get stakeholders from planning JSON"""
        plan = self._get_json_field('planning')
        return plan.get('stakeholders', [])

    @property
    def estimated_effort(self):
        """Get estimated effort from planning JSON"""
        plan = self._get_json_field('planning')
        return plan.get('estimated_effort', '')

    @property
    def complexity(self):
        """Get complexity from planning JSON"""
        plan = self._get_json_field('planning')
        return plan.get('complexity', 'Medium')

    @property
    def branch_hint(self):
        """Get branch hint from implementation JSON"""
        impl = self._get_json_field('implementation')
        return impl.get('branch_hint', '')

    @property
    def commit_preamble(self):
        """Get commit preamble from implementation JSON"""
        impl = self._get_json_field('implementation')
        return impl.get('commit_preamble', '')

    @property
    def commit_trailer(self):
        """Get commit trailer from implementation JSON"""
        impl = self._get_json_field('implementation')
        return impl.get('commit_trailer', '')

    @property
    def links(self):
        """Get links from implementation JSON"""
        impl = self._get_json_field('implementation')
        return impl.get('links', {})

    @property
    def technical_approach(self):
        """Get technical approach from specification JSON"""
        spec = self._get_json_field('specification')
        return spec.get('technical_approach', '')

    @property
    def risks(self):
        """Get risks from planning JSON"""
        plan = self._get_json_field('planning')
        return plan.get('risks', [])

    @property
    def estimate_notes(self):
        """Get estimate notes from planning JSON"""
        plan = self._get_json_field('planning')
        return plan.get('estimate_notes', [])

    def _get_json_field(self, field_name):
        """Helper to safely parse JSON fields"""
        field_value = getattr(self, field_name)
        if not field_value:
            return {}
        try:
            return json.loads(field_value)
        except (json.JSONDecodeError, TypeError):
            return {}

    def save(self, *args, **kwargs):
        self.updated_utc = datetime.utcnow()
        return super().save(*args, **kwargs)

    def to_dict(self):
        """Enhanced to_dict with JSON properties"""
        data = super().to_dict()
        data.update({
            'description': self.description,
            'acceptance': self.acceptance,
            'acceptance_criteria': self.acceptance_criteria,  # Alias
            'dependencies': self.dependencies,
            'stakeholders': self.stakeholders,
            'estimated_effort': self.estimated_effort,
            'complexity': self.complexity,
            'branch_hint': self.branch_hint,
            'commit_preamble': self.commit_preamble,
            'commit_trailer': self.commit_trailer,
            'links': self.links,
            'technical_approach': self.technical_approach,
            'risks': self.risks,
            'estimate_notes': self.estimate_notes
        })
        return data

class Task(BaseModel):
    """Task model for issue breakdown"""
    issue = ForeignKeyField(Issue, backref='tasks', on_delete='CASCADE')
    task_id = CharField(unique=True, index=True, max_length=100)
    title = CharField(max_length=200)
    status = CharField(index=True, max_length=20)  # todo, doing, blocked, review, done
    assignee = CharField(null=True, index=True, max_length=100)
    details = TextField(null=True)  # JSON string for checklist, notes, time estimates
    created_utc = DateTimeField(default=datetime.utcnow, index=True)
    updated_utc = DateTimeField(default=datetime.utcnow, index=True)

    @property
    def checklist(self):
        """Get checklist from details JSON"""
        details = self._get_json_field('details')
        return details.get('checklist', [])

    @property
    def notes(self):
        """Get notes from details JSON"""
        details = self._get_json_field('details')
        return details.get('notes', '')

    @property
    def time_estimate(self):
        """Get time estimate from details JSON"""
        details = self._get_json_field('details')
        return details.get('time_estimate', '')

    def _get_json_field(self, field_name):
        """Helper to safely parse JSON fields"""
        field_value = getattr(self, field_name)
        if not field_value:
            return {}
        try:
            return json.loads(field_value)
        except (json.JSONDecodeError, TypeError):
            return {}

    def save(self, *args, **kwargs):
        self.updated_utc = datetime.utcnow()
        return super().save(*args, **kwargs)

    def to_dict(self):
        """Enhanced to_dict with JSON properties"""
        data = super().to_dict()
        data.update({
            'checklist': self.checklist,
            'notes': self.notes,
            'time_estimate': self.time_estimate
        })
        return data

class WorkLog(BaseModel):
    """WorkLog model for tracking development activity"""
    issue = ForeignKeyField(Issue, backref='worklogs', on_delete='CASCADE')
    task = ForeignKeyField(Task, backref='worklogs', on_delete='SET NULL', null=True)
    agent = CharField(index=True, max_length=100)
    timestamp_utc = DateTimeField(default=datetime.utcnow, index=True)
    activity = CharField(index=True, max_length=50)  # code, design, review, test, planning, blocked
    summary = TextField()
    artifacts = TextField(null=True)  # JSON string for commits, files, links
    context = TextField(null=True)    # JSON string for blockers, decisions, learnings

    @property
    def artifacts_list(self):
        """Get artifacts list from JSON"""
        return self._get_json_list('artifacts')

    @property
    def context_data(self):
        """Get context data from JSON"""
        return self._get_json_dict('context')

    @property
    def time_spent(self):
        """Get time spent from context"""
        context = self.context_data
        return context.get('time_spent', '')

    @property
    def blockers(self):
        """Get blockers from context"""
        context = self.context_data
        return context.get('blockers', '')

    @property
    def decisions(self):
        """Get decisions from context"""
        context = self.context_data
        return context.get('decisions', '')

    def _get_json_list(self, field_name):
        """Helper to safely parse JSON list fields"""
        val = getattr(self, field_name)
        if not val:
            return []
        try:
            data = json.loads(val)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _get_json_dict(self, field_name):
        """Helper to safely parse JSON dict fields"""
        val = getattr(self, field_name)
        if not val:
            return {}
        try:
            data = json.loads(val)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def to_dict(self):
        """Enhanced to_dict with JSON properties"""
        data = super().to_dict()
        data.update({
            'artifacts': self.artifacts_list,
            'context': self.context_data,
            'time_spent': self.time_spent,
            'blockers': self.blockers,
            'decisions': self.decisions
        })
        return data

# Database initialization
def init_db():
    """Initialize database and create tables"""
    db.connect(reuse_if_open=True)
    db.create_tables([Project, Issue, Task, WorkLog], safe=True)
    return db

def close_db():
    """Close database connection"""
    if not db.is_closed():
        db.close()

# Context manager for database operations
class DatabaseManager:
    def __enter__(self):
        init_db()
        return db

    def __exit__(self, exc_type, exc_val, exc_tb):
        close_db()

# Auto-initialize when imported
if __name__ != '__main__':
    init_db()