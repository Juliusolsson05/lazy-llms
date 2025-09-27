import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database configuration
    DATA_DIR = Path.home() / '.julius_mcp' / 'jira_lite'
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Server configuration
    DEFAULT_PORT = 1928
    HOST = '127.0.0.1'

    # JSONL audit log
    EVENTS_FILE = DATA_DIR / 'events.jsonl'