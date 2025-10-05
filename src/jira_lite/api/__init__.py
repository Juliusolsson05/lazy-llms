import json
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify
from ..config import Config
from ..repositories import pm_service, ProjectRepository, IssueRepository, TaskRepository, WorkLogRepository

def create_api_blueprint():
    """Create API blueprint with repository layer"""
    api_bp = Blueprint('api', __name__)

    def log_event_to_jsonl(event_type, data):
        """Log an event to the JSONL audit file"""
        event = {
            'timestamp_utc': datetime.utcnow().isoformat() + 'Z',
            'event_type': event_type,
            'data': data
        }

        # Log to data directory
        events_file = Path('data') / 'events.jsonl'
        with open(events_file, 'a') as f:
            f.write(json.dumps(event) + '\n')

    @api_bp.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'ok': True,
            'port': Config.DEFAULT_PORT,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'database': 'SQLite + Peewee ORM',
            'storage': 'data/jira_lite.db'
        })

    @api_bp.route('/projects/register', methods=['POST'])
    def register_project():
        """Register a new project with the PM system"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'JSON data required'}), 400

            # Check if project already exists
            existing = ProjectRepository.find_by_id(data['project_id'])
            if existing:
                return jsonify({
                    'project_id': existing.project_id,
                    'slug': existing.project_slug,
                    'dashboard_url': f"http://127.0.0.1:{Config.DEFAULT_PORT}/{existing.project_id}",
                    'message': 'Project already registered'
                })

            # Create new project
            project = ProjectRepository.create_or_update(data)

            # Log to JSONL
            log_event_to_jsonl('project_registered', project.to_dict())

            return jsonify({
                'project_id': project.project_id,
                'slug': project.project_slug,
                'dashboard_url': f"http://127.0.0.1:{Config.DEFAULT_PORT}/{project.project_id}"
            }), 201

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/issues/upsert', methods=['POST'])
    def upsert_issue():
        """Create or update an issue"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'JSON data required'}), 400

            issue = IssueRepository.create_or_update(data)

            # Log to JSONL
            log_event_to_jsonl('issue_upserted', issue.to_dict())

            return jsonify({
                'key': issue.key,
                'updated_utc': issue.updated_utc.isoformat() + 'Z'
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/tasks/upsert', methods=['POST'])
    def upsert_task():
        """Create or update a task"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'JSON data required'}), 400

            task = TaskRepository.create_or_update(data)

            # Log to JSONL
            log_event_to_jsonl('task_upserted', task.to_dict())

            return jsonify({
                'task_id': task.task_id,
                'updated_utc': task.updated_utc.isoformat() + 'Z'
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/worklog/append', methods=['POST'])
    def append_worklog():
        """Append a new worklog entry"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'JSON data required'}), 400

            worklog = WorkLogRepository.add_entry(data)

            # Log to JSONL
            log_event_to_jsonl('worklog_appended', worklog.to_dict())

            return jsonify({
                'id': worklog.id,
                'timestamp_utc': worklog.timestamp_utc.isoformat() + 'Z'
            }), 201

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/projects/<project_id>')
    def get_project(project_id):
        """Get project metadata"""
        project = ProjectRepository.find_by_id(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        return jsonify(project.to_dict())

    @api_bp.route('/projects')
    def get_projects():
        """Get all projects"""
        projects = ProjectRepository.get_all()
        return jsonify([project.to_dict() for project in projects])

    @api_bp.route('/issues')
    def get_issues():
        """Get issues with optional filtering"""
        project_id = request.args.get('project_id')
        status = request.args.get('status')
        issue_type = request.args.get('type')
        module = request.args.get('module')
        owner = request.args.get('owner')

        if project_id:
            issues = IssueRepository.find_by_project(
                project_id,
                status=status,
                type=issue_type,
                module=module,
                owner=owner
            )
        else:
            # Get all issues (with filtering)
            from ..models import Issue, Project
            query = Issue.select().join(Project)

            if status:
                query = query.where(Issue.status == status)
            if issue_type:
                query = query.where(Issue.type == issue_type)
            if module:
                query = query.where(Issue.module == module)
            if owner:
                query = query.where(Issue.owner == owner)

            issues = list(query.order_by(Issue.updated_utc.desc()))

        return jsonify([issue.to_dict() for issue in issues])

    @api_bp.route('/issues/search')
    def search_issues():
        """Full-text search across issues"""
        query = request.args.get('q', '')
        project_id = request.args.get('project_id')

        if not query:
            return jsonify({'error': 'Query parameter "q" required'}), 400

        issues = IssueRepository.search_text(query, project_id)
        return jsonify([issue.to_dict() for issue in issues])

    @api_bp.route('/issues/<issue_key>')
    def get_issue(issue_key):
        """Get single issue with full context"""
        try:
            issue_data = pm_service.get_issue_with_context(issue_key)
            return jsonify(issue_data)
        except ValueError:
            return jsonify({'error': 'Issue not found'}), 404

    @api_bp.route('/tasks')
    def get_tasks():
        """Get tasks with optional filtering"""
        project_id = request.args.get('project_id')
        issue_key = request.args.get('issue_key')
        status = request.args.get('status')
        assignee = request.args.get('assignee')

        if project_id:
            tasks = TaskRepository.find_by_project(
                project_id,
                status=status,
                assignee=assignee
            )
        elif issue_key:
            tasks = TaskRepository.find_by_issue(issue_key)
        else:
            # Get all tasks
            from ..models import Task
            query = Task.select()

            if status:
                query = query.where(Task.status == status)
            if assignee:
                query = query.where(Task.assignee == assignee)

            tasks = list(query.order_by(Task.updated_utc.desc()))

        return jsonify([task.to_dict() for task in tasks])

    @api_bp.route('/worklogs')
    def get_worklogs():
        """Get worklogs with optional filtering"""
        project_id = request.args.get('project_id')
        issue_key = request.args.get('issue_key')
        agent = request.args.get('agent')
        activity = request.args.get('activity')
        limit = int(request.args.get('limit', 100))

        if project_id:
            worklogs = WorkLogRepository.find_by_project(
                project_id,
                agent=agent,
                activity=activity,
                issue_key=issue_key,
                limit=limit
            )
        elif issue_key:
            worklogs = WorkLogRepository.find_by_issue(issue_key, limit)
        else:
            worklogs = WorkLogRepository.get_recent_activity(limit=limit)

        return jsonify([worklog.to_dict() for worklog in worklogs])

    @api_bp.route('/dashboard/<project_id>')
    def get_dashboard_data(project_id):
        """Get comprehensive dashboard data for a project"""
        try:
            dashboard_data = pm_service.get_project_dashboard(project_id)
            return jsonify(dashboard_data)
        except ValueError:
            return jsonify({'error': 'Project not found'}), 404

    # Advanced API endpoints
    @api_bp.route('/issues/<issue_key>/dependencies')
    def get_issue_dependencies(issue_key):
        """Get issue dependencies and relationships"""
        dependencies = IssueRepository.get_dependencies(issue_key)
        return jsonify(dependencies)

    @api_bp.route('/queue/<owner>')
    def get_work_queue(owner):
        """Get prioritized work queue for owner"""
        limit = int(request.args.get('limit', 20))
        issues = IssueRepository.get_my_queue(owner, limit)
        return jsonify([issue.to_dict() for issue in issues])

    @api_bp.route('/blocked')
    def get_blocked_issues():
        """Get all blocked issues"""
        project_id = request.args.get('project_id')
        issues = IssueRepository.get_blocked_issues(project_id)
        return jsonify([issue.to_dict() for issue in issues])

    @api_bp.route('/issues/<issue_key>', methods=['DELETE'])
    def delete_issue(issue_key):
        """Delete an issue and all related data"""
        try:
            issue = IssueRepository.find_by_key(issue_key)
            if not issue:
                return jsonify({'error': 'Issue not found'}), 404

            # Delete related worklogs
            from ..models import WorkLog
            WorkLog.delete().where(WorkLog.issue == issue).execute()

            # Delete related tasks
            from ..models import Task
            Task.delete().where(Task.issue == issue).execute()

            # Delete the issue
            issue.delete_instance()

            # Log to JSONL
            log_event_to_jsonl('issue_deleted', {'key': issue_key})

            return jsonify({'message': f'Issue {issue_key} deleted successfully'}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @api_bp.route('/commands/toggle', methods=['POST'])
    def toggle_command():
        """Enable or disable an MCP command"""
        try:
            data = request.get_json()
            command_name = data.get('command_name')
            enabled = data.get('enabled', True)

            if not command_name:
                return jsonify({'error': 'command_name required'}), 400

            # Read command_config.py
            config_path = Path(__file__).parent.parent.parent.parent / 'mcp' / 'src' / 'command_config.py'

            with open(config_path, 'r') as f:
                content = f.read()

            # Modify DISABLED_COMMANDS set
            if enabled:
                # Remove from disabled set
                content = content.replace(f'    "{command_name}",\n', '')
                content = content.replace(f'"{command_name}"', '')
            else:
                # Add to disabled set
                if 'DISABLED_COMMANDS = set()' in content:
                    content = content.replace(
                        'DISABLED_COMMANDS = set()',
                        f'DISABLED_COMMANDS = {{\n    "{command_name}",\n}}'
                    )
                elif f'"{command_name}"' not in content or 'DISABLED_COMMANDS' not in content:
                    # Find the DISABLED_COMMANDS set and add to it
                    import re
                    match = re.search(r'(DISABLED_COMMANDS = \{)([^}]*)(\})', content)
                    if match:
                        current_items = match.group(2)
                        if current_items.strip():
                            new_set = f'{match.group(1)}{current_items}    "{command_name}",\n{match.group(3)}'
                        else:
                            new_set = f'{match.group(1)}\n    "{command_name}",\n{match.group(3)}'
                        content = content[:match.start()] + new_set + content[match.end():]

            # Write back
            with open(config_path, 'w') as f:
                f.write(content)

            return jsonify({
                'message': f'Command {command_name} {"enabled" if enabled else "disabled"}',
                'command_name': command_name,
                'enabled': enabled,
                'restart_required': True
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return api_bp