import json
from datetime import datetime, timedelta
from .app import create_app, db
from .models import Project, Issue, Task, WorkLog

def create_mock_data():
    """Create mock data for testing the application."""

    # Create mock projects
    project1 = Project(
        project_id='pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e',
        project_slug='super-fun-project',
        absolute_path='/Users/juliusolsson/Documents/Super_fun_project',
        submodules=[
            {
                'name': 'app-frontend',
                'path': 'app/app-frontend',
                'absolute_path': '/Users/juliusolsson/Documents/Super_fun_project/app/app-frontend',
                'manage_separately': True
            },
            {
                'name': 'app-backend',
                'path': 'app/app-backend',
                'absolute_path': '/Users/juliusolsson/Documents/Super_fun_project/app/app-backend',
                'manage_separately': True
            }
        ],
        vcs={
            'git_root': '/Users/juliusolsson/Documents/Super_fun_project',
            'default_branch': 'main'
        },
        mcp={
            'pm_server_name': 'pm',
            'version': '>=1.0.0'
        }
    )

    project2 = Project(
        project_id='pn_2a8c9e5f1d2b7c3a4e6f8g9h0i1j2k3l',
        project_slug='ai-chat-app',
        absolute_path='/Users/juliusolsson/Documents/AI_Chat_App',
        submodules=[],
        vcs={
            'git_root': '/Users/juliusolsson/Documents/AI_Chat_App',
            'default_branch': 'main'
        },
        mcp={
            'pm_server_name': 'pm',
            'version': '>=1.0.0'
        }
    )

    db.session.add(project1)
    db.session.add(project2)
    db.session.commit()

    # Create mock issues
    now = datetime.utcnow()

    issue1 = Issue(
        project_id='pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e',
        key='PN-202509-001',
        external_id='pm-node-id-001',
        type='feature',
        title='User can reset password',
        status='in_progress',
        priority='P2',
        module='app-backend',
        branch_hint='feat/PN-202509-001-user-can-reset-password',
        commit_preamble='[pm PN-202509-001]',
        commit_trailer='PM: PN-202509-001',
        acceptance=[
            'Reset email sent',
            'Token expires in 30 minutes',
            'Happy path tested in CI'
        ],
        links={
            'repo': 'file:///Users/juliusolsson/Documents/Super_fun_project',
            'node_path': 'pn/PN-202509-001__/node.md'
        },
        created_utc=now - timedelta(days=2),
        updated_utc=now - timedelta(hours=1),
        owner='agent:claude-code'
    )

    issue2 = Issue(
        project_id='pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e',
        key='PN-202509-002',
        type='bug',
        title='Fix login validation error messages',
        status='review',
        priority='P1',
        module='app-frontend',
        branch_hint='fix/PN-202509-002-login-validation-errors',
        commit_preamble='[pm PN-202509-002]',
        commit_trailer='PM: PN-202509-002',
        acceptance=[
            'Error messages are user-friendly',
            'All edge cases covered',
            'Accessibility requirements met'
        ],
        links={
            'repo': 'file:///Users/juliusolsson/Documents/Super_fun_project',
            'node_path': 'pn/PN-202509-002__/node.md'
        },
        created_utc=now - timedelta(days=1),
        updated_utc=now - timedelta(minutes=30),
        owner='agent:claude-code'
    )

    issue3 = Issue(
        project_id='pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e',
        key='PN-202509-003',
        type='feature',
        title='Add user dashboard with metrics',
        status='proposed',
        priority='P3',
        module='app-frontend',
        branch_hint='feat/PN-202509-003-user-dashboard',
        commit_preamble='[pm PN-202509-003]',
        commit_trailer='PM: PN-202509-003',
        acceptance=[
            'Dashboard shows key metrics',
            'Real-time updates via WebSocket',
            'Mobile responsive design'
        ],
        links={
            'repo': 'file:///Users/juliusolsson/Documents/Super_fun_project',
            'node_path': 'pn/PN-202509-003__/node.md'
        },
        created_utc=now - timedelta(hours=6),
        updated_utc=now - timedelta(hours=6),
        owner='agent:claude-code'
    )

    issue4 = Issue(
        project_id='pn_2a8c9e5f1d2b7c3a4e6f8g9h0i1j2k3l',
        key='AI-202509-001',
        type='feature',
        title='Implement conversation memory',
        status='in_progress',
        priority='P1',
        module='core',
        branch_hint='feat/AI-202509-001-conversation-memory',
        commit_preamble='[pm AI-202509-001]',
        commit_trailer='PM: AI-202509-001',
        acceptance=[
            'Conversation context preserved',
            'Memory window configurable',
            'Performance optimized'
        ],
        links={
            'repo': 'file:///Users/juliusolsson/Documents/AI_Chat_App',
            'node_path': 'pn/AI-202509-001__/node.md'
        },
        created_utc=now - timedelta(days=3),
        updated_utc=now - timedelta(hours=2),
        owner='agent:claude-code'
    )

    db.session.add(issue1)
    db.session.add(issue2)
    db.session.add(issue3)
    db.session.add(issue4)
    db.session.commit()

    # Create mock tasks
    task1 = Task(
        project_id='pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e',
        issue_key='PN-202509-001',
        task_id='PN-202509-001-T1',
        title='Add password_reset table',
        status='done',
        assignee='agent:claude-code',
        checklist=[
            {'text': 'Create migration', 'done': True},
            {'text': 'Add API endpoint', 'done': True},
            {'text': 'Write tests', 'done': True}
        ],
        notes='Use existing email infrastructure'
    )

    task2 = Task(
        project_id='pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e',
        issue_key='PN-202509-001',
        task_id='PN-202509-001-T2',
        title='Implement email sending service',
        status='doing',
        assignee='agent:claude-code',
        checklist=[
            {'text': 'Set up email templates', 'done': True},
            {'text': 'Configure SMTP', 'done': False},
            {'text': 'Add rate limiting', 'done': False}
        ],
        notes='Consider using SendGrid for production'
    )

    task3 = Task(
        project_id='pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e',
        issue_key='PN-202509-002',
        task_id='PN-202509-002-T1',
        title='Update frontend validation components',
        status='review',
        assignee='agent:claude-code',
        checklist=[
            {'text': 'Update error message components', 'done': True},
            {'text': 'Add internationalization', 'done': True},
            {'text': 'Test accessibility', 'done': False}
        ],
        notes='Focus on screen reader compatibility'
    )

    db.session.add(task1)
    db.session.add(task2)
    db.session.add(task3)
    db.session.commit()

    # Create mock worklogs
    worklog1 = WorkLog(
        project_id='pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e',
        issue_key='PN-202509-001',
        task_id='PN-202509-001-T1',
        agent='agent:claude-code',
        timestamp_utc=now - timedelta(hours=4),
        activity='code',
        summary='Created migration and models for password reset',
        artifacts=[
            {
                'type': 'commit',
                'sha': 'a1b2c3d4',
                'subject': '[pm PN-202509-001] feat: add password reset models',
                'branch': 'feat/PN-202509-001-user-can-reset-password'
            },
            {
                'type': 'file',
                'path': 'backend/migrations/0002_password_reset.py'
            }
        ]
    )

    worklog2 = WorkLog(
        project_id='pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e',
        issue_key='PN-202509-001',
        task_id='PN-202509-001-T1',
        agent='agent:claude-code',
        timestamp_utc=now - timedelta(hours=3),
        activity='test',
        summary='Added comprehensive tests for password reset functionality',
        artifacts=[
            {
                'type': 'commit',
                'sha': 'e5f6g7h8',
                'subject': '[pm PN-202509-001] test: add password reset tests',
                'branch': 'feat/PN-202509-001-user-can-reset-password'
            },
            {
                'type': 'file',
                'path': 'backend/tests/test_password_reset.py'
            }
        ]
    )

    worklog3 = WorkLog(
        project_id='pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e',
        issue_key='PN-202509-002',
        task_id='PN-202509-002-T1',
        agent='agent:claude-code',
        timestamp_utc=now - timedelta(hours=1),
        activity='refactor',
        summary='Refactored validation error handling for better UX',
        artifacts=[
            {
                'type': 'commit',
                'sha': 'i9j0k1l2',
                'subject': '[pm PN-202509-002] refactor: improve validation errors',
                'branch': 'fix/PN-202509-002-login-validation-errors'
            },
            {
                'type': 'file',
                'path': 'frontend/src/components/ValidationError.tsx'
            }
        ]
    )

    worklog4 = WorkLog(
        project_id='pn_2a8c9e5f1d2b7c3a4e6f8g9h0i1j2k3l',
        issue_key='AI-202509-001',
        agent='agent:claude-code',
        timestamp_utc=now - timedelta(hours=2),
        activity='plan',
        summary='Analyzed conversation memory requirements and designed architecture',
        artifacts=[
            {
                'type': 'file',
                'path': 'docs/conversation-memory-design.md'
            }
        ]
    )

    db.session.add(worklog1)
    db.session.add(worklog2)
    db.session.add(worklog3)
    db.session.add(worklog4)
    db.session.commit()

    print("✅ Mock data created successfully!")
    print(f"📊 Created {Project.query.count()} projects")
    print(f"🎫 Created {Issue.query.count()} issues")
    print(f"📋 Created {Task.query.count()} tasks")
    print(f"📝 Created {WorkLog.query.count()} worklogs")

def init_database():
    """Initialize the database with tables and mock data."""
    app = create_app()

    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created")

        # Check if we already have data
        if Project.query.count() == 0:
            create_mock_data()
        else:
            print("📊 Database already contains data")

if __name__ == '__main__':
    init_database()