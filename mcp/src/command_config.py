"""MCP Command Configuration
Categorizes all MCP commands into required/recommended/optional tiers.
"""

REQUIRED_COMMANDS = {
    "pm_docs": "Get comprehensive PM system documentation",
    "pm_status": "Get comprehensive project status including metrics",
    "pm_list_issues": "List and filter project issues",
    "pm_get_issue": "Get comprehensive issue details",
    "pm_create_issue": "Create a comprehensive issue with rich documentation",
    "pm_start_work": "Start work on an issue - updates status and creates branch",
    "pm_log_work": "Log development activity with artifacts and context",
    "pm_update_status": "Update issue status with workflow validation",
}

RECOMMENDED_COMMANDS = {
    "pm_workflow": "Get methodology and best practices for PM-driven development",
    "pm_search_issues": "Full-text search across all issue content",
    "pm_list_projects": "List all available projects in the system",
    "pm_create_branch": "Create a git branch for an issue",
    "pm_commit": "Create a git commit with PM trailers",
    "pm_my_queue": "Get personalized work queue with intelligent prioritization",
    "pm_create_task": "Create a task within an issue for work breakdown",
    "pm_update_task": "Update task status, title, assignee, or details",
}

OPTIONAL_COMMANDS = {
    "pm_list_archived_issues": "List archived/completed issues with filtering",
    "pm_get_archived_issue": "Retrieve comprehensive details of an archived issue",
    "pm_delete_issue": "Delete an issue with all associated data",
    "pm_blocked_issues": "Find and analyze blocked issues",
    "pm_daily_standup": "Generate daily standup report",
    "pm_init_project": "Initialize a new project for PM tracking",
    "pm_register_project": "Register project with Jira-lite web UI server",
    "pm_add_submodule": "Add a new submodule to an existing project",
    "pm_remove_submodule": "Remove a submodule from a project",
    "pm_list_submodules": "List all submodules in a project",
    "pm_estimate": "Add effort and complexity estimates to an issue",
    "pm_git_status": "Enhanced git status with issue context",
    "pm_push_branch": "Push current branch to remote",
    "pm_project_dashboard": "Get comprehensive project dashboard with metrics",
    "pm_reminder": "Get helpful reminders about using the PM system",
}

DISABLED_COMMANDS = {
    "pm_commit",
    "pm_create_branch",
    "pm_daily_standup",
    "pm_delete_issue",
    "pm_get_archived_issue",
    "pm_git_status",
    "pm_project_dashboard",
    "pm_push_branch",
    "pm_remove_submodule",
}

def is_command_enabled(command_name: str) -> bool:
    """Check if a command is enabled"""
    return command_name not in DISABLED_COMMANDS

def get_command_category(command_name: str) -> str:
    """Get the category of a command"""
    if command_name in REQUIRED_COMMANDS:
        return "required"
    elif command_name in RECOMMENDED_COMMANDS:
        return "recommended"
    elif command_name in OPTIONAL_COMMANDS:
        return "optional"
    return "unknown"

def get_command_description(command_name: str) -> str:
    """Get the description of a command"""
    for commands in [REQUIRED_COMMANDS, RECOMMENDED_COMMANDS, OPTIONAL_COMMANDS]:
        if command_name in commands:
            return commands[command_name]
    return ""

def get_all_commands():
    """Get all commands with their metadata"""
    all_commands = {}

    for cmd, desc in REQUIRED_COMMANDS.items():
        all_commands[cmd] = {
            "category": "required",
            "description": desc,
            "enabled": cmd not in DISABLED_COMMANDS
        }

    for cmd, desc in RECOMMENDED_COMMANDS.items():
        all_commands[cmd] = {
            "category": "recommended",
            "description": desc,
            "enabled": cmd not in DISABLED_COMMANDS
        }

    for cmd, desc in OPTIONAL_COMMANDS.items():
        all_commands[cmd] = {
            "category": "optional",
            "description": desc,
            "enabled": cmd not in DISABLED_COMMANDS
        }

    return all_commands

def disable_command(command_name: str):
    """Disable a command"""
    DISABLED_COMMANDS.add(command_name)

def enable_command(command_name: str):
    """Enable a command"""
    DISABLED_COMMANDS.discard(command_name)
