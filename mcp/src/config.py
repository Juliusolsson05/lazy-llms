"""Configuration for PM MCP Server with proper first-run handling"""
import os
from pathlib import Path
from typing import Optional

class Config:
    """Server configuration with proper initialization"""

    # Database - delay initialization to avoid import-time failures
    _database_path: Optional[Path] = None

    @classmethod
    def get_database_path(cls) -> Path:
        """Get database path with fallback logic"""
        if cls._database_path is not None:
            return cls._database_path

        # Try environment variable first
        env_path = os.getenv("PM_DATABASE_PATH")
        if env_path:
            cls._database_path = Path(env_path)
            return cls._database_path

        # Try default location
        default_path = Path.home() / ".julius_mcp" / "jira_lite" / "jira.db"
        if default_path.exists():
            cls._database_path = default_path
            return cls._database_path

        # Try relative path from main project
        relative_path = Path(__file__).parent.parent.parent / "data" / "jira_lite.db"
        if relative_path.exists():
            cls._database_path = relative_path
            return cls._database_path

        # Return default anyway - will be created if needed
        cls._database_path = default_path
        return cls._database_path

    @classmethod
    def set_database_path(cls, path: str):
        """Set database path explicitly"""
        cls._database_path = Path(path)

    # Server settings
    DEFAULT_PORT = int(os.getenv("MCP_SERVER_PORT", "8848"))
    DEFAULT_HOST = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
    DEFAULT_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")

    # Project defaults
    DEFAULT_PROJECT_ID: Optional[str] = os.getenv("PM_DEFAULT_PROJECT_ID")
    DEFAULT_OWNER = os.getenv("PM_DEFAULT_OWNER", "agent:claude-code")

    @staticmethod
    def get_default_project_id() -> Optional[str]:
        """Get default project ID from environment"""
        return os.environ.get("PM_DEFAULT_PROJECT_ID")

    # Git settings
    GIT_USER_NAME = os.getenv("GIT_USER_NAME", "Claude Code Agent")
    GIT_USER_EMAIL = os.getenv("GIT_USER_EMAIL", "noreply@anthropic.com")

    # Limits
    MAX_ISSUES_PER_LIST = int(os.getenv("PM_MAX_ISSUES", "100"))
    MAX_WORKLOGS_PER_LIST = int(os.getenv("PM_MAX_WORKLOGS", "50"))
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

    # Security settings
    ALLOWED_GIT_COMMANDS = {
        "status", "log", "branch", "checkout", "add", "commit",
        "push", "pull", "fetch", "merge", "stash", "diff", "show"
    }

    @classmethod
    def validate(cls, strict: bool = False) -> tuple[bool, list[str]]:
        """
        Validate configuration with better error handling
        Returns (is_valid, warnings/errors)
        """
        warnings = []
        errors = []

        # Check database
        db_path = cls.get_database_path()
        if not db_path.exists():
            if strict:
                errors.append(f"Database not found at {db_path}")
            else:
                warnings.append(f"Database not found at {db_path} - will be created if needed")
        else:
            # Check if database is readable
            try:
                with open(db_path, 'rb') as f:
                    f.read(16)  # Read SQLite header
            except Exception as e:
                errors.append(f"Cannot read database at {db_path}: {e}")

        # Check git configuration
        if not cls.GIT_USER_EMAIL:
            warnings.append("GIT_USER_EMAIL not set - using default")

        # Check project defaults
        if not cls.DEFAULT_PROJECT_ID:
            warnings.append("PM_DEFAULT_PROJECT_ID not set - will use first available project")

        is_valid = len(errors) == 0
        return is_valid, warnings + errors

    @classmethod
    def get_summary(cls) -> dict:
        """Get configuration summary for debugging"""
        return {
            "database_path": str(cls.get_database_path()),
            "database_exists": cls.get_database_path().exists(),
            "default_project": cls.DEFAULT_PROJECT_ID,
            "default_owner": cls.DEFAULT_OWNER,
            "git_user": f"{cls.GIT_USER_NAME} <{cls.GIT_USER_EMAIL}>",
            "server": {
                "host": cls.DEFAULT_HOST,
                "port": cls.DEFAULT_PORT,
                "transport": cls.DEFAULT_TRANSPORT
            }
        }