from datetime import datetime, timedelta
from .storage import JSONStorage

def create_mock_data():
    """Create mock data and save it to JSON files."""
    storage = JSONStorage()

    # Create mock projects
    project1_data = {
        "project_id": "pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e",
        "project_slug": "super-fun-project",
        "absolute_path": "/Users/juliusolsson/Documents/Super_fun_project",
        "submodules": [
            {
                "name": "app-frontend",
                "path": "app/app-frontend",
                "absolute_path": "/Users/juliusolsson/Documents/Super_fun_project/app/app-frontend",
                "manage_separately": True
            },
            {
                "name": "app-backend",
                "path": "app/app-backend",
                "absolute_path": "/Users/juliusolsson/Documents/Super_fun_project/app/app-backend",
                "manage_separately": True
            }
        ],
        "vcs": {
            "git_root": "/Users/juliusolsson/Documents/Super_fun_project",
            "default_branch": "main"
        },
        "mcp": {
            "pm_server_name": "pm",
            "version": ">=1.0.0"
        }
    }

    project2_data = {
        "project_id": "pn_2a8c9e5f1d2b7c3a4e6f8g9h0i1j2k3l",
        "project_slug": "ai-chat-app",
        "absolute_path": "/Users/juliusolsson/Documents/AI_Chat_App",
        "submodules": [],
        "vcs": {
            "git_root": "/Users/juliusolsson/Documents/AI_Chat_App",
            "default_branch": "main"
        },
        "mcp": {
            "pm_server_name": "pm",
            "version": ">=1.0.0"
        }
    }

    project3_data = {
        "project_id": "pn_3e2f4a6b8c0d9e1f2a3b4c5d6e7f8g9h",
        "project_slug": "mobile-game-engine",
        "absolute_path": "/Users/juliusolsson/Documents/Mobile_Game_Engine",
        "submodules": [
            {
                "name": "core-engine",
                "path": "engine/core",
                "absolute_path": "/Users/juliusolsson/Documents/Mobile_Game_Engine/engine/core",
                "manage_separately": True
            },
            {
                "name": "graphics-renderer",
                "path": "engine/graphics",
                "absolute_path": "/Users/juliusolsson/Documents/Mobile_Game_Engine/engine/graphics",
                "manage_separately": True
            },
            {
                "name": "audio-system",
                "path": "engine/audio",
                "absolute_path": "/Users/juliusolsson/Documents/Mobile_Game_Engine/engine/audio",
                "manage_separately": True
            }
        ],
        "vcs": {
            "git_root": "/Users/juliusolsson/Documents/Mobile_Game_Engine",
            "default_branch": "develop"
        },
        "mcp": {
            "pm_server_name": "pm",
            "version": ">=1.0.0"
        }
    }

    storage.add_project(project1_data)
    storage.add_project(project2_data)
    storage.add_project(project3_data)

    # Create mock issues
    now = datetime.utcnow()

    issues_data = [
        {
            "project_id": "pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e",
            "key": "PN-202509-001",
            "external_id": "pm-node-id-001",
            "type": "feature",
            "title": "User can reset password",
            "status": "in_progress",
            "priority": "P2",
            "module": "app-backend",
            "branch_hint": "feat/PN-202509-001-user-can-reset-password",
            "commit_preamble": "[pm PN-202509-001]",
            "commit_trailer": "PM: PN-202509-001",
            "acceptance": [
                "Reset email sent",
                "Token expires in 30 minutes",
                "Happy path tested in CI"
            ],
            "links": {
                "repo": "file:///Users/juliusolsson/Documents/Super_fun_project",
                "node_path": "pn/PN-202509-001__/node.md"
            },
            "created_utc": (now - timedelta(days=2)).isoformat() + 'Z',
            "updated_utc": (now - timedelta(hours=1)).isoformat() + 'Z',
            "owner": "agent:claude-code"
        },
        {
            "project_id": "pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e",
            "key": "PN-202509-002",
            "type": "bug",
            "title": "Fix login validation error messages",
            "status": "review",
            "priority": "P1",
            "module": "app-frontend",
            "branch_hint": "fix/PN-202509-002-login-validation-errors",
            "commit_preamble": "[pm PN-202509-002]",
            "commit_trailer": "PM: PN-202509-002",
            "acceptance": [
                "Error messages are user-friendly",
                "All edge cases covered",
                "Accessibility requirements met"
            ],
            "links": {
                "repo": "file:///Users/juliusolsson/Documents/Super_fun_project",
                "node_path": "pn/PN-202509-002__/node.md"
            },
            "created_utc": (now - timedelta(days=1)).isoformat() + 'Z',
            "updated_utc": (now - timedelta(minutes=30)).isoformat() + 'Z',
            "owner": "agent:claude-code"
        },
        {
            "project_id": "pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e",
            "key": "PN-202509-003",
            "type": "feature",
            "title": "Add user dashboard with metrics",
            "status": "proposed",
            "priority": "P3",
            "module": "app-frontend",
            "branch_hint": "feat/PN-202509-003-user-dashboard",
            "commit_preamble": "[pm PN-202509-003]",
            "commit_trailer": "PM: PN-202509-003",
            "acceptance": [
                "Dashboard shows key metrics",
                "Real-time updates via WebSocket",
                "Mobile responsive design"
            ],
            "links": {
                "repo": "file:///Users/juliusolsson/Documents/Super_fun_project",
                "node_path": "pn/PN-202509-003__/node.md"
            },
            "created_utc": (now - timedelta(hours=6)).isoformat() + 'Z',
            "updated_utc": (now - timedelta(hours=6)).isoformat() + 'Z',
            "owner": "agent:claude-code"
        },
        {
            "project_id": "pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e",
            "key": "PN-202509-004",
            "type": "chore",
            "title": "Update CI/CD pipeline for faster builds",
            "status": "done",
            "priority": "P4",
            "module": "app-backend",
            "branch_hint": "chore/PN-202509-004-ci-cd-optimization",
            "commit_preamble": "[pm PN-202509-004]",
            "commit_trailer": "PM: PN-202509-004",
            "acceptance": [
                "Build time reduced by 50%",
                "Docker layer caching implemented",
                "Parallel test execution enabled"
            ],
            "links": {
                "repo": "file:///Users/juliusolsson/Documents/Super_fun_project",
                "node_path": "pn/PN-202509-004__/node.md"
            },
            "created_utc": (now - timedelta(days=5)).isoformat() + 'Z',
            "updated_utc": (now - timedelta(days=1)).isoformat() + 'Z',
            "owner": "agent:claude-code"
        },
        {
            "project_id": "pn_2a8c9e5f1d2b7c3a4e6f8g9h0i1j2k3l",
            "key": "AI-202509-001",
            "type": "feature",
            "title": "Implement conversation memory",
            "status": "in_progress",
            "priority": "P1",
            "module": "core",
            "branch_hint": "feat/AI-202509-001-conversation-memory",
            "commit_preamble": "[pm AI-202509-001]",
            "commit_trailer": "PM: AI-202509-001",
            "acceptance": [
                "Conversation context preserved",
                "Memory window configurable",
                "Performance optimized"
            ],
            "links": {
                "repo": "file:///Users/juliusolsson/Documents/AI_Chat_App",
                "node_path": "pn/AI-202509-001__/node.md"
            },
            "created_utc": (now - timedelta(days=3)).isoformat() + 'Z',
            "updated_utc": (now - timedelta(hours=2)).isoformat() + 'Z',
            "owner": "agent:claude-code"
        },
        {
            "project_id": "pn_2a8c9e5f1d2b7c3a4e6f8g9h0i1j2k3l",
            "key": "AI-202509-002",
            "type": "bug",
            "title": "Fix memory leak in chat session cleanup",
            "status": "review",
            "priority": "P2",
            "module": "core",
            "branch_hint": "fix/AI-202509-002-memory-leak",
            "commit_preamble": "[pm AI-202509-002]",
            "commit_trailer": "PM: AI-202509-002",
            "acceptance": [
                "Memory usage stable over long sessions",
                "Cleanup function properly called",
                "No orphaned objects in memory"
            ],
            "links": {
                "repo": "file:///Users/juliusolsson/Documents/AI_Chat_App",
                "node_path": "pn/AI-202509-002__/node.md"
            },
            "created_utc": (now - timedelta(hours=8)).isoformat() + 'Z',
            "updated_utc": (now - timedelta(hours=1)).isoformat() + 'Z',
            "owner": "agent:claude-code"
        },
        {
            "project_id": "pn_3e2f4a6b8c0d9e1f2a3b4c5d6e7f8g9h",
            "key": "MGE-202509-001",
            "type": "feature",
            "title": "Implement basic physics engine",
            "status": "in_progress",
            "priority": "P1",
            "module": "core-engine",
            "branch_hint": "feat/MGE-202509-001-physics-engine",
            "commit_preamble": "[pm MGE-202509-001]",
            "commit_trailer": "PM: MGE-202509-001",
            "acceptance": [
                "Collision detection working",
                "Gravity simulation implemented",
                "60 FPS performance maintained"
            ],
            "links": {
                "repo": "file:///Users/juliusolsson/Documents/Mobile_Game_Engine",
                "node_path": "pn/MGE-202509-001__/node.md"
            },
            "created_utc": (now - timedelta(days=4)).isoformat() + 'Z',
            "updated_utc": (now - timedelta(hours=3)).isoformat() + 'Z',
            "owner": "agent:claude-code"
        },
        {
            "project_id": "pn_3e2f4a6b8c0d9e1f2a3b4c5d6e7f8g9h",
            "key": "MGE-202509-002",
            "type": "feature",
            "title": "Add shader compilation system",
            "status": "proposed",
            "priority": "P2",
            "module": "graphics-renderer",
            "branch_hint": "feat/MGE-202509-002-shader-system",
            "commit_preamble": "[pm MGE-202509-002]",
            "commit_trailer": "PM: MGE-202509-002",
            "acceptance": [
                "GLSL shaders compile correctly",
                "Hot reload during development",
                "Error reporting for shader issues"
            ],
            "links": {
                "repo": "file:///Users/juliusolsson/Documents/Mobile_Game_Engine",
                "node_path": "pn/MGE-202509-002__/node.md"
            },
            "created_utc": (now - timedelta(hours=4)).isoformat() + 'Z',
            "updated_utc": (now - timedelta(hours=4)).isoformat() + 'Z',
            "owner": "agent:claude-code"
        }
    ]

    for issue_data in issues_data:
        storage.upsert_issue(issue_data)

    # Create mock tasks
    tasks_data = [
        {
            "project_id": "pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e",
            "issue_key": "PN-202509-001",
            "task_id": "PN-202509-001-T1",
            "title": "Add password_reset table",
            "status": "done",
            "assignee": "agent:claude-code",
            "checklist": [
                {"text": "Create migration", "done": True},
                {"text": "Add API endpoint", "done": True},
                {"text": "Write tests", "done": True}
            ],
            "notes": "Use existing email infrastructure"
        },
        {
            "project_id": "pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e",
            "issue_key": "PN-202509-001",
            "task_id": "PN-202509-001-T2",
            "title": "Implement email sending service",
            "status": "doing",
            "assignee": "agent:claude-code",
            "checklist": [
                {"text": "Set up email templates", "done": True},
                {"text": "Configure SMTP", "done": False},
                {"text": "Add rate limiting", "done": False}
            ],
            "notes": "Consider using SendGrid for production"
        },
        {
            "project_id": "pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e",
            "issue_key": "PN-202509-002",
            "task_id": "PN-202509-002-T1",
            "title": "Update frontend validation components",
            "status": "review",
            "assignee": "agent:claude-code",
            "checklist": [
                {"text": "Update error message components", "done": True},
                {"text": "Add internationalization", "done": True},
                {"text": "Test accessibility", "done": False}
            ],
            "notes": "Focus on screen reader compatibility"
        },
        {
            "project_id": "pn_2a8c9e5f1d2b7c3a4e6f8g9h0i1j2k3l",
            "issue_key": "AI-202509-001",
            "task_id": "AI-202509-001-T1",
            "title": "Design memory architecture",
            "status": "done",
            "assignee": "agent:claude-code",
            "checklist": [
                {"text": "Research existing solutions", "done": True},
                {"text": "Design data structures", "done": True},
                {"text": "Plan memory management", "done": True}
            ],
            "notes": "Consider LRU cache for efficiency"
        },
        {
            "project_id": "pn_2a8c9e5f1d2b7c3a4e6f8g9h0i1j2k3l",
            "issue_key": "AI-202509-001",
            "task_id": "AI-202509-001-T2",
            "title": "Implement conversation storage",
            "status": "doing",
            "assignee": "agent:claude-code",
            "checklist": [
                {"text": "Create storage interface", "done": True},
                {"text": "Implement in-memory store", "done": True},
                {"text": "Add persistence layer", "done": False}
            ],
            "notes": "Start with in-memory, add Redis later"
        }
    ]

    for task_data in tasks_data:
        storage.upsert_task(task_data)

    # Create mock worklogs
    worklogs_data = [
        {
            "project_id": "pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e",
            "issue_key": "PN-202509-001",
            "task_id": "PN-202509-001-T1",
            "agent": "agent:claude-code",
            "timestamp_utc": (now - timedelta(hours=4)).isoformat() + 'Z',
            "activity": "code",
            "summary": "Created migration and models for password reset",
            "artifacts": [
                {
                    "type": "commit",
                    "sha": "a1b2c3d4",
                    "subject": "[pm PN-202509-001] feat: add password reset models",
                    "branch": "feat/PN-202509-001-user-can-reset-password"
                },
                {
                    "type": "file",
                    "path": "backend/migrations/0002_password_reset.py"
                }
            ]
        },
        {
            "project_id": "pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e",
            "issue_key": "PN-202509-001",
            "task_id": "PN-202509-001-T1",
            "agent": "agent:claude-code",
            "timestamp_utc": (now - timedelta(hours=3)).isoformat() + 'Z',
            "activity": "test",
            "summary": "Added comprehensive tests for password reset functionality",
            "artifacts": [
                {
                    "type": "commit",
                    "sha": "e5f6g7h8",
                    "subject": "[pm PN-202509-001] test: add password reset tests",
                    "branch": "feat/PN-202509-001-user-can-reset-password"
                },
                {
                    "type": "file",
                    "path": "backend/tests/test_password_reset.py"
                }
            ]
        },
        {
            "project_id": "pn_1f6d7c94b9c4418ea3b92d3d8a2c4f6e",
            "issue_key": "PN-202509-002",
            "task_id": "PN-202509-002-T1",
            "agent": "agent:claude-code",
            "timestamp_utc": (now - timedelta(hours=1)).isoformat() + 'Z',
            "activity": "refactor",
            "summary": "Refactored validation error handling for better UX",
            "artifacts": [
                {
                    "type": "commit",
                    "sha": "i9j0k1l2",
                    "subject": "[pm PN-202509-002] refactor: improve validation errors",
                    "branch": "fix/PN-202509-002-login-validation-errors"
                },
                {
                    "type": "file",
                    "path": "frontend/src/components/ValidationError.tsx"
                }
            ]
        },
        {
            "project_id": "pn_2a8c9e5f1d2b7c3a4e6f8g9h0i1j2k3l",
            "issue_key": "AI-202509-001",
            "agent": "agent:claude-code",
            "timestamp_utc": (now - timedelta(hours=2)).isoformat() + 'Z',
            "activity": "plan",
            "summary": "Analyzed conversation memory requirements and designed architecture",
            "artifacts": [
                {
                    "type": "file",
                    "path": "docs/conversation-memory-design.md"
                }
            ]
        },
        {
            "project_id": "pn_3e2f4a6b8c0d9e1f2a3b4c5d6e7f8g9h",
            "issue_key": "MGE-202509-001",
            "agent": "agent:claude-code",
            "timestamp_utc": (now - timedelta(hours=3)).isoformat() + 'Z',
            "activity": "code",
            "summary": "Implemented basic collision detection algorithms",
            "artifacts": [
                {
                    "type": "commit",
                    "sha": "m1n2o3p4",
                    "subject": "[pm MGE-202509-001] feat: add collision detection",
                    "branch": "feat/MGE-202509-001-physics-engine"
                },
                {
                    "type": "file",
                    "path": "engine/core/physics/collision.cpp"
                }
            ]
        },
        {
            "project_id": "pn_3e2f4a6b8c0d9e1f2a3b4c5d6e7f8g9h",
            "issue_key": "MGE-202509-001",
            "agent": "agent:claude-code",
            "timestamp_utc": (now - timedelta(minutes=30)).isoformat() + 'Z',
            "activity": "test",
            "summary": "Added unit tests for physics calculations",
            "artifacts": [
                {
                    "type": "commit",
                    "sha": "q4r5s6t7",
                    "subject": "[pm MGE-202509-001] test: add physics unit tests",
                    "branch": "feat/MGE-202509-001-physics-engine"
                },
                {
                    "type": "file",
                    "path": "tests/physics/test_collision.cpp"
                }
            ]
        }
    ]

    for worklog_data in worklogs_data:
        storage.add_worklog(worklog_data)

    print("✅ Mock data created successfully!")
    print(f"📊 Created {len(storage.get_projects())} projects")
    print(f"🎫 Created {len(storage.get_issues())} issues")
    print(f"📋 Created {len(storage.get_tasks())} tasks")
    print(f"📝 Created {len(storage.get_worklogs())} worklogs")

if __name__ == '__main__':
    create_mock_data()