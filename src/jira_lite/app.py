import socket
import click
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template, abort, redirect, url_for, flash
from flask_cors import CORS

from .config import Config
from .models import init_db, close_db, db
from .repositories import pm_service, ProjectRepository, IssueRepository, TaskRepository, WorkLogRepository
from .utils import render_markdown, extract_summary, format_date, format_datetime

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)

    # Initialize database
    init_db()

    # Database connection management
    @app.before_request
    def before_request():
        db.connect(reuse_if_open=True)

    @app.teardown_request
    def teardown_request(exception):
        if not db.is_closed():
            db.close()

    # Register API blueprint
    from .api import create_api_blueprint
    api_bp = create_api_blueprint()
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def index():
        """Main page showing all projects"""
        projects = ProjectRepository.get_all()
        return render_template('index.html', projects=projects)

    @app.route('/<project_id>')
    def dashboard(project_id):
        """Project dashboard with issues overview"""
        try:
            dashboard_data = pm_service.get_project_dashboard(project_id)
            return render_template('dashboard.html',
                                 project=dashboard_data['project'],
                                 issues=dashboard_data['issues'])
        except ValueError:
            abort(404)

    @app.route('/<project_id>/kanban')
    def kanban(project_id):
        """Kanban board view with drag-and-drop interface"""
        try:
            dashboard_data = pm_service.get_project_dashboard(project_id)
            return render_template('kanban.html',
                                 project=dashboard_data['project'],
                                 issues=dashboard_data['issues'])
        except ValueError:
            abort(404)

    @app.route('/<project_id>/issues/<issue_key>')
    def issue_detail(project_id, issue_key):
        """Detailed issue view with full LLM-generated content"""
        try:
            issue_data = pm_service.get_issue_with_context(issue_key)

            # Verify project matches
            if issue_data['project']['project_id'] != project_id:
                abort(404)

            return render_template('issue_detail.html',
                                 project=issue_data['project'],
                                 issue=issue_data['issue'],
                                 tasks=issue_data['tasks'],
                                 worklogs=issue_data['worklogs'],
                                 dependencies=issue_data['dependencies'],
                                 render_markdown=render_markdown)
        except ValueError:
            abort(404)

    @app.route('/<project_id>/issues/new', methods=['GET', 'POST'])
    def create_issue(project_id):
        """Create new issue with comprehensive form"""
        project = ProjectRepository.find_by_id(project_id)
        if not project:
            abort(404)

        if request.method == 'POST':
            try:
                # Collect form data
                issue_data = {
                    'type': request.form['type'],
                    'title': request.form['title'],
                    'priority': request.form['priority'],
                    'module': request.form.get('module') or None,
                    'description': request.form['description'],
                    'acceptance': [line.strip() for line in request.form['acceptance'].split('\n') if line.strip()],
                    'owner': request.form.get('owner', 'agent:claude-code'),
                    'estimated_effort': request.form.get('estimated_effort', ''),
                    'complexity': request.form.get('complexity', 'Medium'),
                    'stakeholders': [s.strip() for s in request.form.get('stakeholders', '').split(',') if s.strip()]
                }

                # Create issue using service
                issue = pm_service.create_comprehensive_issue(project_id, issue_data)

                flash(f'Issue {issue.key} created successfully!', 'success')
                return redirect(url_for('issue_detail', project_id=project_id, issue_key=issue.key))

            except Exception as e:
                flash(f'Error creating issue: {str(e)}', 'error')

        return render_template('issue_form.html', project=project.to_dict(), issue=None, action='Create')

    @app.route('/<project_id>/issues/<issue_key>/edit', methods=['GET', 'POST'])
    def edit_issue(project_id, issue_key):
        """Edit existing issue"""
        issue = IssueRepository.find_by_key(issue_key)
        if not issue or issue.project.project_id != project_id:
            abort(404)

        project = issue.project

        if request.method == 'POST':
            try:
                # Update issue data
                issue_data = {
                    'key': issue_key,  # Keep existing key
                    'type': request.form['type'],
                    'title': request.form['title'],
                    'status': request.form['status'],
                    'priority': request.form['priority'],
                    'module': request.form.get('module') or None,
                    'description': request.form['description'],
                    'acceptance': [line.strip() for line in request.form['acceptance'].split('\n') if line.strip()],
                    'owner': request.form.get('owner', issue.owner),
                    'estimated_effort': request.form.get('estimated_effort', ''),
                    'complexity': request.form.get('complexity', 'Medium'),
                    'stakeholders': [s.strip() for s in request.form.get('stakeholders', '').split(',') if s.strip()]
                }

                # Update using repository
                updated_issue = IssueRepository.create_or_update(issue_data)

                flash(f'Issue {issue_key} updated successfully!', 'success')
                return redirect(url_for('issue_detail', project_id=project_id, issue_key=issue_key))

            except Exception as e:
                flash(f'Error updating issue: {str(e)}', 'error')

        return render_template('issue_form.html',
                             project=project.to_dict(),
                             issue=issue.to_dict(),
                             action='Edit')

    # Add Jinja2 filters
    app.jinja_env.filters['extract_summary'] = extract_summary
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['format_datetime'] = format_datetime

    return app

def find_free_port(preferred_port=None):
    """Find a free port, preferring the specified port if available."""
    if preferred_port:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1', preferred_port))
            sock.close()
            return preferred_port
        except OSError:
            pass
        finally:
            sock.close()

    # Find any free port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

@click.command()
@click.option('--port', default=Config.DEFAULT_PORT, help='Port to run on')
@click.option('--auto', is_flag=True, help='Auto-find free port if preferred is taken')
@click.option('--host', default='127.0.0.1', help='Host to bind to')
def run_server(port, auto, host):
    """Run the Jira-lite server with Peewee + SQLite."""
    app = create_app()

    if auto:
        port = find_free_port(port)

    print(f"🚀 Jira-lite running at http://{host}:{port}")
    print(f"📊 Dashboard: http://{host}:{port}")
    print(f"🔗 API: http://{host}:{port}/api")
    print(f"🗄️  Database: {app.config.get('DATABASE_PATH', 'data/jira_lite.db')}")

    try:
        app.run(host=host, port=port, debug=True)
    finally:
        close_db()

if __name__ == '__main__':
    run_server()