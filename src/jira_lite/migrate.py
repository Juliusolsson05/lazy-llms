#!/usr/bin/env python3
"""
Migration script to move data from JSON files to SQLite + Peewee ORM

This script migrates existing JSON data to the new Peewee-based SQLite database.
It safely handles the transition from flat JSON storage to relational database.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from .models import init_db, Project, Issue, Task, WorkLog, db
from .repositories import ProjectRepository, IssueRepository, TaskRepository, WorkLogRepository

def load_json_file(file_path: str, default=None):
    """Safely load JSON file with fallback"""
    if default is None:
        default = []

    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"⚠️  Could not load {file_path}: {e}")
        return default

def migrate_projects():
    """Migrate projects from JSON to SQLite"""
    print("📊 Migrating projects...")

    # Only look for local JSON files
    json_files = [
        'data/projects.json'
    ]

    projects_data = []
    for json_file in json_files:
        expanded_path = os.path.expanduser(json_file)
        if os.path.exists(expanded_path):
            data = load_json_file(expanded_path)
            if data:
                projects_data.extend(data)
                print(f"   📁 Loaded {len(data)} projects from {json_file}")

    if not projects_data:
        print("   ⚠️  No project data found to migrate")
        return

    migrated_count = 0
    for project_data in projects_data:
        try:
            # Create metadata JSON
            metadata = {
                'submodules': project_data.get('submodules', []),
                'vcs': project_data.get('vcs', {}),
                'mcp': project_data.get('mcp', {}),
                'created_utc': project_data.get('created_utc')
            }

            # Use repository to create/update
            project = ProjectRepository.create_or_update({
                'project_id': project_data['project_id'],
                'project_slug': project_data['project_slug'],
                'absolute_path': project_data['absolute_path'],
                'submodules': metadata['submodules'],
                'vcs': metadata['vcs'],
                'mcp': metadata['mcp']
            })

            migrated_count += 1
            print(f"   ✅ Migrated project: {project.project_slug}")

        except Exception as e:
            print(f"   ❌ Failed to migrate project {project_data.get('project_slug', 'unknown')}: {e}")

    print(f"   📊 Successfully migrated {migrated_count} projects")

def migrate_issues():
    """Migrate issues from JSON to SQLite"""
    print("🎫 Migrating issues...")

    # Only look for local JSON files
    json_files = [
        'data/issues.json'
    ]

    issues_data = []
    for json_file in json_files:
        expanded_path = os.path.expanduser(json_file)
        if os.path.exists(expanded_path):
            data = load_json_file(expanded_path)
            if data:
                issues_data.extend(data)
                print(f"   📁 Loaded {len(data)} issues from {json_file}")

    if not issues_data:
        print("   ⚠️  No issue data found to migrate")
        return

    migrated_count = 0
    for issue_data in issues_data:
        try:
            # Convert old format to new format
            migrated_issue_data = {
                'project_id': issue_data['project_id'],
                'key': issue_data['key'],
                'title': issue_data['title'],
                'type': issue_data['type'],
                'status': issue_data['status'],
                'priority': issue_data['priority'],
                'module': issue_data.get('module'),
                'owner': issue_data.get('owner'),
                'external_id': issue_data.get('external_id'),

                # Rich content
                'description': issue_data.get('description', ''),
                'acceptance': issue_data.get('acceptance', []),
                'dependencies': issue_data.get('dependencies', []),
                'stakeholders': issue_data.get('stakeholders', []),
                'estimated_effort': issue_data.get('estimated_effort', ''),
                'complexity': issue_data.get('complexity', 'Medium'),
                'branch_hint': issue_data.get('branch_hint', ''),
                'commit_preamble': issue_data.get('commit_preamble', ''),
                'commit_trailer': issue_data.get('commit_trailer', ''),
                'links': issue_data.get('links', {})
            }

            # Create using repository
            issue = IssueRepository.create_or_update(migrated_issue_data)
            migrated_count += 1
            print(f"   ✅ Migrated issue: {issue.key} - {issue.title}")

        except Exception as e:
            print(f"   ❌ Failed to migrate issue {issue_data.get('key', 'unknown')}: {e}")

    print(f"   📊 Successfully migrated {migrated_count} issues")

def migrate_tasks():
    """Migrate tasks from JSON to SQLite"""
    print("📋 Migrating tasks...")

    # Only look for local JSON files
    json_files = [
        'data/tasks.json'
    ]

    tasks_data = []
    for json_file in json_files:
        expanded_path = os.path.expanduser(json_file)
        if os.path.exists(expanded_path):
            data = load_json_file(expanded_path)
            if data:
                tasks_data.extend(data)
                print(f"   📁 Loaded {len(data)} tasks from {json_file}")

    if not tasks_data:
        print("   ⚠️  No task data found to migrate")
        return

    migrated_count = 0
    for task_data in tasks_data:
        try:
            # Convert old format to new format
            migrated_task_data = {
                'task_id': task_data['task_id'],
                'issue_key': task_data['issue_key'],
                'title': task_data['title'],
                'status': task_data['status'],
                'assignee': task_data.get('assignee'),
                'checklist': task_data.get('checklist', []),
                'notes': task_data.get('notes', ''),
                'time_estimate': task_data.get('time_estimate', '')
            }

            # Create using repository
            task = TaskRepository.create_or_update(migrated_task_data)
            migrated_count += 1
            print(f"   ✅ Migrated task: {task.task_id} - {task.title}")

        except Exception as e:
            print(f"   ❌ Failed to migrate task {task_data.get('task_id', 'unknown')}: {e}")

    print(f"   📊 Successfully migrated {migrated_count} tasks")

def migrate_worklogs():
    """Migrate worklogs from JSON to SQLite"""
    print("📝 Migrating worklogs...")

    # Only look for local JSON files
    json_files = [
        'data/worklogs.json'
    ]

    worklogs_data = []
    for json_file in json_files:
        expanded_path = os.path.expanduser(json_file)
        if os.path.exists(expanded_path):
            data = load_json_file(expanded_path)
            if data:
                worklogs_data.extend(data)
                print(f"   📁 Loaded {len(data)} worklogs from {json_file}")

    if not worklogs_data:
        print("   ⚠️  No worklog data found to migrate")
        return

    migrated_count = 0
    for worklog_data in worklogs_data:
        try:
            # Convert old format to new format
            migrated_worklog_data = {
                'issue_key': worklog_data['issue_key'],
                'task_id': worklog_data.get('task_id'),
                'agent': worklog_data['agent'],
                'activity': worklog_data['activity'],
                'summary': worklog_data['summary'],
                'artifacts': worklog_data.get('artifacts', []),
                'context': worklog_data.get('context', {})
            }

            # Parse timestamp if string
            if 'timestamp_utc' in worklog_data:
                timestamp_str = worklog_data['timestamp_utc']
                if isinstance(timestamp_str, str):
                    # Remove Z and parse
                    timestamp_str = timestamp_str.rstrip('Z')
                    migrated_worklog_data['timestamp_utc'] = datetime.fromisoformat(timestamp_str)

            # Create using repository
            worklog = WorkLogRepository.add_entry(migrated_worklog_data)
            migrated_count += 1
            print(f"   ✅ Migrated worklog: {worklog.agent} - {worklog.summary[:50]}...")

        except Exception as e:
            print(f"   ❌ Failed to migrate worklog: {e}")

    print(f"   📊 Successfully migrated {migrated_count} worklogs")

def backup_json_files():
    """Backup existing JSON files before migration"""
    print("💾 Creating backup of existing JSON files...")

    backup_dir = Path('data/backup')
    backup_dir.mkdir(exist_ok=True)

    json_files = ['data/projects.json', 'data/issues.json', 'data/tasks.json', 'data/worklogs.json']

    for json_file in json_files:
        if os.path.exists(json_file):
            backup_file = backup_dir / f"{Path(json_file).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.system(f"cp {json_file} {backup_file}")
            print(f"   💾 Backed up {json_file} to {backup_file}")

def verify_migration():
    """Verify migration was successful"""
    print("🔍 Verifying migration...")

    projects_count = Project.select().count()
    issues_count = Issue.select().count()
    tasks_count = Task.select().count()
    worklogs_count = WorkLog.select().count()

    print(f"   📊 Database contains:")
    print(f"      Projects: {projects_count}")
    print(f"      Issues: {issues_count}")
    print(f"      Tasks: {tasks_count}")
    print(f"      Worklogs: {worklogs_count}")

    # Test relationships
    if issues_count > 0:
        sample_issue = Issue.select().first()
        print(f"   🔗 Sample relationships:")
        print(f"      Issue {sample_issue.key} belongs to project: {sample_issue.project.project_slug}")
        print(f"      Issue has {len(list(sample_issue.tasks))} tasks")
        print(f"      Issue has {len(list(sample_issue.worklogs))} worklogs")

def run_migration():
    """Run complete migration process"""
    print("🚀 Starting migration from JSON to SQLite + Peewee...")
    print("=" * 60)

    # Initialize database and tables
    print("🗄️  Initializing SQLite database...")
    init_db()
    print("   ✅ Database initialized")

    # Backup existing files
    backup_json_files()

    # Run migrations in order (dependencies matter!)
    try:
        with db.atomic():  # Use transaction for safety
            migrate_projects()
            migrate_issues()
            migrate_tasks()
            migrate_worklogs()

        print("=" * 60)
        print("✅ Migration completed successfully!")

        verify_migration()

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("💾 Original JSON files preserved in data/backup/")
        raise

    finally:
        db.close()

if __name__ == '__main__':
    run_migration()