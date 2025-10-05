"""MCP Command Configuration - Database-backed version
Maintains backward compatibility while reading from database
"""
from typing import Dict, Optional, Set
from datetime import datetime

# Static definitions for documentation/reference
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

# Runtime configuration loaded from database
_DISABLED_COMMANDS_CACHE: Optional[Set[str]] = None
_CACHE_LOADED_AT: Optional[datetime] = None

def _load_disabled_commands() -> Set[str]:
    """Load disabled commands from database"""
    global _DISABLED_COMMANDS_CACHE, _CACHE_LOADED_AT

    try:
        from database import CommandConfig, DatabaseSession

        with DatabaseSession():
            disabled = CommandConfig.select().where(CommandConfig.enabled == False)
            _DISABLED_COMMANDS_CACHE = {config.command_name for config in disabled}
            _CACHE_LOADED_AT = datetime.utcnow()
            return _DISABLED_COMMANDS_CACHE
    except Exception as e:
        print(f"⚠️  Failed to load command config from database: {e}")
        # Fallback to empty set if database not available
        _DISABLED_COMMANDS_CACHE = set()
        return _DISABLED_COMMANDS_CACHE

def get_disabled_commands() -> Set[str]:
    """Get currently disabled commands (cached)"""
    global _DISABLED_COMMANDS_CACHE

    # Load on first access
    if _DISABLED_COMMANDS_CACHE is None:
        return _load_disabled_commands()

    return _DISABLED_COMMANDS_CACHE

def is_command_enabled(command_name: str) -> bool:
    """Check if a command is enabled"""
    disabled = get_disabled_commands()
    return command_name not in disabled

def refresh_cache():
    """Refresh the disabled commands cache from database"""
    return _load_disabled_commands()

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

def get_all_commands() -> Dict:
    """Get all commands with their metadata from database"""
    try:
        from database import CommandConfig, DatabaseSession

        with DatabaseSession():
            configs = CommandConfig.select()
            return {
                config.command_name: {
                    "category": config.category,
                    "description": config.description,
                    "enabled": config.enabled,
                    "can_disable": config.can_disable
                }
                for config in configs
            }
    except Exception:
        # Fallback to static definitions
        all_commands = {}
        disabled = get_disabled_commands()

        for cmd, desc in REQUIRED_COMMANDS.items():
            all_commands[cmd] = {
                "category": "required",
                "description": desc,
                "enabled": cmd not in disabled,
                "can_disable": False
            }

        for cmd, desc in RECOMMENDED_COMMANDS.items():
            all_commands[cmd] = {
                "category": "recommended",
                "description": desc,
                "enabled": cmd not in disabled,
                "can_disable": True
            }

        for cmd, desc in OPTIONAL_COMMANDS.items():
            all_commands[cmd] = {
                "category": "optional",
                "description": desc,
                "enabled": cmd not in disabled,
                "can_disable": True
            }

        return all_commands

def disable_command(command_name: str, disabled_by: str = "system") -> bool:
    """Disable a command in database"""
    try:
        from database import CommandConfig, DatabaseSession

        with DatabaseSession():
            config = CommandConfig.get(CommandConfig.command_name == command_name)

            if not config.can_disable:
                raise ValueError(f"Command '{command_name}' cannot be disabled (required)")

            config.enabled = False
            config.disabled_at = datetime.utcnow()
            config.disabled_by = disabled_by
            config.updated_utc = datetime.utcnow()
            config.save()

            # Refresh cache
            refresh_cache()
            return True
    except Exception as e:
        print(f"Failed to disable command: {e}")
        return False

def enable_command(command_name: str) -> bool:
    """Enable a command in database"""
    try:
        from database import CommandConfig, DatabaseSession

        with DatabaseSession():
            config = CommandConfig.get(CommandConfig.command_name == command_name)
            config.enabled = True
            config.disabled_at = None
            config.disabled_by = None
            config.updated_utc = datetime.utcnow()
            config.save()

            # Refresh cache
            refresh_cache()
            return True
    except Exception as e:
        print(f"Failed to enable command: {e}")
        return False

# Backward compatibility property for DISABLED_COMMANDS
def get_disabled_commands_legacy():
    return get_disabled_commands()

# For any legacy code that imports DISABLED_COMMANDS directly
DISABLED_COMMANDS = get_disabled_commands()