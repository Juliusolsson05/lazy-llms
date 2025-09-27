import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from peewee import DoesNotExist, IntegrityError

from .models import Project, Issue, Task, WorkLog, db

class ProjectRepository:
    """Clean repository interface for Project operations"""

    @staticmethod
    def get_all() -> List[Project]:
        """Get all projects ordered by slug"""
        return list(Project.select().order_by(Project.project_slug))

    @staticmethod
    def find_by_id(project_id: str) -> Optional[Project]:
        """Find project by project_id"""
        try:
            return Project.get(Project.project_id == project_id)
        except DoesNotExist:
            return None

    @staticmethod
    def find_by_slug(slug: str) -> Optional[Project]:
        """Find project by slug"""
        try:
            return Project.get(Project.project_slug == slug)
        except DoesNotExist:
            return None

    @staticmethod
    def create_or_update(project_data: Dict[str, Any]) -> Project:
        """Create new project or update existing"""
        try:
            # Try to find existing project
            project = Project.get(Project.project_id == project_data['project_id'])

            # Update existing project
            project.project_slug = project_data.get('project_slug', project.project_slug)
            project.absolute_path = project_data.get('absolute_path', project.absolute_path)

            # Update metadata
            metadata = {
                'submodules': project_data.get('submodules', []),
                'vcs': project_data.get('vcs', {}),
                'mcp': project_data.get('mcp', {})
            }
            project.metadata = json.dumps(metadata)
            project.save()

        except DoesNotExist:
            # Create new project
            metadata = {
                'submodules': project_data.get('submodules', []),
                'vcs': project_data.get('vcs', {}),
                'mcp': project_data.get('mcp', {})
            }

            project = Project.create(
                project_id=project_data['project_id'],
                project_slug=project_data['project_slug'],
                absolute_path=project_data['absolute_path'],
                metadata=json.dumps(metadata)
            )

        return project

class IssueRepository:
    """Clean repository interface for Issue operations"""

    @staticmethod
    def find_by_key(key: str) -> Optional[Issue]:
        """Find issue by unique key"""
        try:
            return Issue.get(Issue.key == key)
        except DoesNotExist:
            return None

    @staticmethod
    def find_by_project(project_id: str, **filters) -> List[Issue]:
        """Find issues by project with optional filtering"""
        query = (Issue
                .select()
                .join(Project)
                .where(Project.project_id == project_id))

        # Apply filters
        if filters.get('status'):
            query = query.where(Issue.status == filters['status'])
        if filters.get('priority'):
            query = query.where(Issue.priority == filters['priority'])
        if filters.get('module'):
            query = query.where(Issue.module == filters['module'])
        if filters.get('owner'):
            query = query.where(Issue.owner == filters['owner'])
        if filters.get('type'):
            query = query.where(Issue.type == filters['type'])

        return list(query.order_by(Issue.updated_utc.desc()))

    @staticmethod
    def search_text(search_query: str, project_id: str = None) -> List[Issue]:
        """Full-text search across issue content"""
        # Build search conditions
        search_conditions = (
            Issue.title.contains(search_query) |
            Issue.specification.contains(search_query) |
            Issue.planning.contains(search_query) |
            Issue.implementation.contains(search_query)
        )

        query = Issue.select().where(search_conditions)

        if project_id:
            query = query.join(Project).where(Project.project_id == project_id)

        return list(query.order_by(Issue.updated_utc.desc()))

    @staticmethod
    def get_my_queue(owner: str, limit: int = 20) -> List[Issue]:
        """Get prioritized work queue for specific owner"""
        return list(
            Issue.select()
            .where(
                (Issue.owner == owner) &
                (Issue.status.in_(['proposed', 'in_progress']))
            )
            .order_by(
                Issue.priority.asc(),  # P1 first
                Issue.updated_utc.desc()
            )
            .limit(limit)
        )

    @staticmethod
    def get_blocked_issues(project_id: str = None) -> List[Issue]:
        """Get all blocked issues"""
        query = Issue.select().where(Issue.status == 'blocked')

        if project_id:
            query = query.join(Project).where(Project.project_id == project_id)

        return list(query.order_by(Issue.updated_utc.desc()))

    @staticmethod
    def get_dependencies(issue_key: str) -> Dict[str, List[str]]:
        """Get issue dependencies and things it blocks"""
        issue = IssueRepository.find_by_key(issue_key)
        if not issue:
            return {"depends_on": [], "blocks": []}

        depends_on = issue.dependencies

        # Find issues that depend on this one
        blocks = []
        for other_issue in Issue.select():
            if issue_key in other_issue.dependencies:
                blocks.append(other_issue.key)

        return {
            "depends_on": depends_on,
            "blocks": blocks
        }

    @staticmethod
    def create_or_update(issue_data: Dict[str, Any]) -> Issue:
        """Create new issue or update existing by key"""

        # Prepare structured data
        structured_fields = {
            'key': issue_data['key'],
            'title': issue_data['title'],
            'type': issue_data['type'],
            'status': issue_data.get('status', 'proposed'),
            'priority': issue_data.get('priority', 'P3'),
            'module': issue_data.get('module'),
            'owner': issue_data.get('owner'),
            'external_id': issue_data.get('external_id')
        }

        # Prepare JSON fields
        specification = {
            'description': issue_data.get('description', ''),
            'acceptance_criteria': issue_data.get('acceptance', []),
            'technical_approach': issue_data.get('technical_approach', ''),
            'business_requirements': issue_data.get('business_requirements', [])
        }

        planning = {
            'dependencies': issue_data.get('dependencies', []),
            'stakeholders': issue_data.get('stakeholders', []),
            'estimated_effort': issue_data.get('estimated_effort', ''),
            'complexity': issue_data.get('complexity', 'Medium'),
            'risks': issue_data.get('risks', [])
        }

        implementation = {
            'branch_hint': issue_data.get('branch_hint', ''),
            'commit_preamble': issue_data.get('commit_preamble', ''),
            'commit_trailer': issue_data.get('commit_trailer', ''),
            'links': issue_data.get('links', {}),
            'artifacts': issue_data.get('artifacts', [])
        }

        try:
            # Find existing issue
            issue = Issue.get(Issue.key == issue_data['key'])

            # Update existing
            for key, value in structured_fields.items():
                if value is not None:
                    setattr(issue, key, value)

            issue.specification = json.dumps(specification)
            issue.planning = json.dumps(planning)
            issue.implementation = json.dumps(implementation)
            issue.save()

        except DoesNotExist:
            # Create new issue - need to find project first
            project = None
            if 'project_id' in issue_data:
                project = ProjectRepository.find_by_id(issue_data['project_id'])

            if not project:
                raise ValueError(f"Project not found: {issue_data.get('project_id')}")

            issue = Issue.create(
                project=project,
                specification=json.dumps(specification),
                planning=json.dumps(planning),
                implementation=json.dumps(implementation),
                **structured_fields
            )

        return issue

class TaskRepository:
    """Clean repository interface for Task operations"""

    @staticmethod
    def find_by_id(task_id: str) -> Optional[Task]:
        """Find task by task_id"""
        try:
            return Task.get(Task.task_id == task_id)
        except DoesNotExist:
            return None

    @staticmethod
    def find_by_issue(issue_key: str) -> List[Task]:
        """Find all tasks for an issue"""
        return list(
            Task.select()
            .join(Issue)
            .where(Issue.key == issue_key)
            .order_by(Task.created_utc.asc())
        )

    @staticmethod
    def find_by_project(project_id: str, **filters) -> List[Task]:
        """Find tasks by project with optional filtering"""
        query = (Task
                .select()
                .join(Issue)
                .join(Project)
                .where(Project.project_id == project_id))

        if filters.get('status'):
            query = query.where(Task.status == filters['status'])
        if filters.get('assignee'):
            query = query.where(Task.assignee == filters['assignee'])

        return list(query.order_by(Task.updated_utc.desc()))

    @staticmethod
    def create_or_update(task_data: Dict[str, Any]) -> Task:
        """Create new task or update existing"""

        # Prepare details JSON
        details = {
            'checklist': task_data.get('checklist', []),
            'notes': task_data.get('notes', ''),
            'time_estimate': task_data.get('time_estimate', '')
        }

        try:
            # Find existing task
            task = Task.get(Task.task_id == task_data['task_id'])

            # Update existing
            task.title = task_data.get('title', task.title)
            task.status = task_data.get('status', task.status)
            task.assignee = task_data.get('assignee', task.assignee)
            task.details = json.dumps(details)
            task.save()

        except DoesNotExist:
            # Create new task - find issue first
            issue = IssueRepository.find_by_key(task_data['issue_key'])
            if not issue:
                raise ValueError(f"Issue not found: {task_data.get('issue_key')}")

            task = Task.create(
                issue=issue,
                task_id=task_data['task_id'],
                title=task_data['title'],
                status=task_data.get('status', 'todo'),
                assignee=task_data.get('assignee'),
                details=json.dumps(details)
            )

        return task

class WorkLogRepository:
    """Clean repository interface for WorkLog operations"""

    @staticmethod
    def find_by_issue(issue_key: str, limit: int = 50) -> List[WorkLog]:
        """Find worklogs for an issue"""
        return list(
            WorkLog.select()
            .join(Issue)
            .where(Issue.key == issue_key)
            .order_by(WorkLog.timestamp_utc.desc())
            .limit(limit)
        )

    @staticmethod
    def find_by_project(project_id: str, **filters) -> List[WorkLog]:
        """Find worklogs by project with optional filtering"""
        query = (WorkLog
                .select()
                .join(Issue)
                .join(Project)
                .where(Project.project_id == project_id))

        if filters.get('agent'):
            query = query.where(WorkLog.agent == filters['agent'])
        if filters.get('activity'):
            query = query.where(WorkLog.activity == filters['activity'])
        if filters.get('issue_key'):
            query = query.where(Issue.key == filters['issue_key'])

        limit = filters.get('limit', 100)
        return list(query.order_by(WorkLog.timestamp_utc.desc()).limit(limit))

    @staticmethod
    def add_entry(worklog_data: Dict[str, Any]) -> WorkLog:
        """Add new worklog entry"""

        # Find issue
        issue = IssueRepository.find_by_key(worklog_data['issue_key'])
        if not issue:
            raise ValueError(f"Issue not found: {worklog_data.get('issue_key')}")

        # Find task (optional)
        task = None
        if worklog_data.get('task_id'):
            task = TaskRepository.find_by_id(worklog_data['task_id'])

        # Prepare artifacts and context
        artifacts = json.dumps(worklog_data.get('artifacts', []))
        context = json.dumps(worklog_data.get('context', {}))

        worklog = WorkLog.create(
            issue=issue,
            task=task,
            agent=worklog_data['agent'],
            activity=worklog_data['activity'],
            summary=worklog_data['summary'],
            artifacts=artifacts,
            context=context,
            timestamp_utc=worklog_data.get('timestamp_utc', datetime.utcnow())
        )

        return worklog

    @staticmethod
    def get_recent_activity(project_id: str = None, limit: int = 20) -> List[WorkLog]:
        """Get recent activity across projects"""
        query = WorkLog.select().join(Issue).join(Project)

        if project_id:
            query = query.where(Project.project_id == project_id)

        return list(query.order_by(WorkLog.timestamp_utc.desc()).limit(limit))

class PMService:
    """High-level service combining repositories for complex operations"""

    def __init__(self):
        self.projects = ProjectRepository()
        self.issues = IssueRepository()
        self.tasks = TaskRepository()
        self.worklogs = WorkLogRepository()

    def get_project_dashboard(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive project dashboard data"""
        project = self.projects.find_by_id(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        issues = self.issues.find_by_project(project_id)
        recent_worklogs = self.worklogs.find_by_project(project_id, limit=10)

        # Calculate stats
        issue_stats = {}
        for issue in issues:
            status = issue.status
            issue_stats[status] = issue_stats.get(status, 0) + 1

        return {
            'project': project.to_dict(),
            'issues': [issue.to_dict() for issue in issues],
            'recent_worklogs': [wl.to_dict() for wl in recent_worklogs],
            'stats': {
                'issue_counts': issue_stats,
                'total_issues': len(issues)
            }
        }

    def get_issue_with_context(self, issue_key: str) -> Dict[str, Any]:
        """Get issue with all related tasks and worklogs"""
        issue = self.issues.find_by_key(issue_key)
        if not issue:
            raise ValueError(f"Issue not found: {issue_key}")

        tasks = self.tasks.find_by_issue(issue_key)
        worklogs = self.worklogs.find_by_issue(issue_key)
        dependencies = self.issues.get_dependencies(issue_key)

        return {
            'issue': issue.to_dict(),
            'project': issue.project.to_dict(),
            'tasks': [task.to_dict() for task in tasks],
            'worklogs': [wl.to_dict() for wl in worklogs],
            'dependencies': dependencies
        }

    def create_comprehensive_issue(self, project_id: str, issue_data: Dict[str, Any]) -> Issue:
        """Create issue with full LLM-generated content"""

        # Generate issue key if not provided
        if 'key' not in issue_data:
            project = self.projects.find_by_id(project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            # Get existing issue count for this project
            existing_count = Issue.select().join(Project).where(Project.project_id == project_id).count()
            project_prefix = project.project_slug.upper().replace('-', '')[:4]
            issue_data['key'] = f"{project_prefix}-{existing_count + 1:03d}"

        # Auto-generate git integration fields
        if 'branch_hint' not in issue_data:
            title_slug = issue_data['title'].lower().replace(' ', '-').replace('_', '-')[:40]
            issue_data['branch_hint'] = f"{issue_data['type']}/{issue_data['key'].lower()}-{title_slug}"

        if 'commit_preamble' not in issue_data:
            issue_data['commit_preamble'] = f"[pm {issue_data['key']}]"

        if 'commit_trailer' not in issue_data:
            issue_data['commit_trailer'] = f"PM: {issue_data['key']}"

        # Add project_id for repository method
        issue_data['project_id'] = project_id

        return self.issues.create_or_update(issue_data)

    def update_issue_status(self, issue_key: str, new_status: str, notes: str = '', notify: bool = True) -> Issue:
        """Update issue status with proper workflow validation"""
        issue = self.issues.find_by_key(issue_key)
        if not issue:
            raise ValueError(f"Issue not found: {issue_key}")

        old_status = issue.status

        # Update status
        issue.status = new_status
        issue.save()

        # Log the status change
        self.worklogs.add_entry({
            'issue_key': issue_key,
            'agent': 'system:status-change',
            'activity': 'status_change',
            'summary': f"Status changed from {old_status} to {new_status}",
            'context': {
                'old_status': old_status,
                'new_status': new_status,
                'notes': notes,
                'notify_stakeholders': notify
            }
        })

        return issue

    def log_development_work(self, issue_key: str, agent: str, activity: str,
                           summary: str, artifacts: List[Dict] = None,
                           context: Dict = None) -> WorkLog:
        """Log development work with rich context"""

        worklog_data = {
            'issue_key': issue_key,
            'agent': agent,
            'activity': activity,
            'summary': summary,
            'artifacts': artifacts or [],
            'context': context or {}
        }

        return self.worklogs.add_entry(worklog_data)

# Global service instance
pm_service = PMService()