import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import uuid

class JSONStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.projects_file = self.data_dir / "projects.json"
        self.issues_file = self.data_dir / "issues.json"
        self.tasks_file = self.data_dir / "tasks.json"
        self.worklogs_file = self.data_dir / "worklogs.json"

        # Initialize files if they don't exist
        self._ensure_file_exists(self.projects_file, [])
        self._ensure_file_exists(self.issues_file, [])
        self._ensure_file_exists(self.tasks_file, [])
        self._ensure_file_exists(self.worklogs_file, [])

    def _ensure_file_exists(self, file_path: Path, default_content):
        if not file_path.exists():
            with open(file_path, 'w') as f:
                json.dump(default_content, f, indent=2)

    def _load_json(self, file_path: Path) -> List[Dict]:
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_json(self, file_path: Path, data: List[Dict]):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    # Projects
    def get_projects(self) -> List[Dict]:
        return self._load_json(self.projects_file)

    def get_project_by_id(self, project_id: str) -> Optional[Dict]:
        projects = self.get_projects()
        return next((p for p in projects if p['project_id'] == project_id), None)

    def add_project(self, project_data: Dict) -> Dict:
        projects = self.get_projects()

        # Check if project already exists
        existing = next((p for p in projects if p['project_id'] == project_data['project_id']), None)
        if existing:
            return existing

        # Add timestamp if not present
        if 'created_utc' not in project_data:
            project_data['created_utc'] = datetime.utcnow().isoformat() + 'Z'

        projects.append(project_data)
        self._save_json(self.projects_file, projects)
        return project_data

    # Issues
    def get_issues(self, project_id: str = None, status: str = None, issue_type: str = None,
                   module: str = None, owner: str = None) -> List[Dict]:
        issues = self._load_json(self.issues_file)

        if project_id:
            issues = [i for i in issues if i.get('project_id') == project_id]
        if status:
            issues = [i for i in issues if i.get('status') == status]
        if issue_type:
            issues = [i for i in issues if i.get('type') == issue_type]
        if module:
            issues = [i for i in issues if i.get('module') == module]
        if owner:
            issues = [i for i in issues if i.get('owner') == owner]

        return issues

    def get_issue_by_key(self, key: str) -> Optional[Dict]:
        issues = self._load_json(self.issues_file)
        return next((i for i in issues if i['key'] == key), None)

    def upsert_issue(self, issue_data: Dict) -> Dict:
        issues = self._load_json(self.issues_file)

        # Find existing issue by key or external_id
        existing_index = -1
        if 'key' in issue_data:
            for i, issue in enumerate(issues):
                if issue.get('key') == issue_data['key'] and issue.get('project_id') == issue_data.get('project_id'):
                    existing_index = i
                    break
        elif 'external_id' in issue_data:
            for i, issue in enumerate(issues):
                if issue.get('external_id') == issue_data['external_id']:
                    existing_index = i
                    break

        # Add timestamps
        now = datetime.utcnow().isoformat() + 'Z'
        if existing_index >= 0:
            # Update existing
            issue_data['updated_utc'] = now
            if 'created_utc' not in issue_data:
                issue_data['created_utc'] = issues[existing_index].get('created_utc', now)
            issues[existing_index] = issue_data
        else:
            # Create new
            issue_data['created_utc'] = now
            issue_data['updated_utc'] = now
            issues.append(issue_data)

        self._save_json(self.issues_file, issues)
        return issue_data

    # Tasks
    def get_tasks(self, project_id: str = None, issue_key: str = None, status: str = None) -> List[Dict]:
        tasks = self._load_json(self.tasks_file)

        if project_id:
            tasks = [t for t in tasks if t.get('project_id') == project_id]
        if issue_key:
            tasks = [t for t in tasks if t.get('issue_key') == issue_key]
        if status:
            tasks = [t for t in tasks if t.get('status') == status]

        return tasks

    def upsert_task(self, task_data: Dict) -> Dict:
        tasks = self._load_json(self.tasks_file)

        # Find existing task
        existing_index = -1
        for i, task in enumerate(tasks):
            if task.get('task_id') == task_data.get('task_id'):
                existing_index = i
                break

        # Add timestamps
        now = datetime.utcnow().isoformat() + 'Z'
        if existing_index >= 0:
            # Update existing
            task_data['updated_utc'] = now
            if 'created_utc' not in task_data:
                task_data['created_utc'] = tasks[existing_index].get('created_utc', now)
            tasks[existing_index] = task_data
        else:
            # Create new
            task_data['created_utc'] = now
            task_data['updated_utc'] = now
            tasks.append(task_data)

        self._save_json(self.tasks_file, tasks)
        return task_data

    # WorkLogs
    def get_worklogs(self, project_id: str = None, issue_key: str = None, task_id: str = None,
                     agent: str = None, activity: str = None) -> List[Dict]:
        worklogs = self._load_json(self.worklogs_file)

        if project_id:
            worklogs = [w for w in worklogs if w.get('project_id') == project_id]
        if issue_key:
            worklogs = [w for w in worklogs if w.get('issue_key') == issue_key]
        if task_id:
            worklogs = [w for w in worklogs if w.get('task_id') == task_id]
        if agent:
            worklogs = [w for w in worklogs if w.get('agent') == agent]
        if activity:
            worklogs = [w for w in worklogs if w.get('activity') == activity]

        # Sort by timestamp (most recent first)
        worklogs.sort(key=lambda x: x.get('timestamp_utc', ''), reverse=True)
        return worklogs

    def add_worklog(self, worklog_data: Dict) -> Dict:
        worklogs = self._load_json(self.worklogs_file)

        # Add timestamp if not present
        if 'timestamp_utc' not in worklog_data:
            worklog_data['timestamp_utc'] = datetime.utcnow().isoformat() + 'Z'

        # Add unique ID
        worklog_data['id'] = str(uuid.uuid4())

        worklogs.append(worklog_data)
        self._save_json(self.worklogs_file, worklogs)
        return worklog_data