# src/jira_lite/init_db.py
"""Database initialization for Jira-lite PM system"""

from .models import (
    db, Project, Issue, Task, WorkLog,
    init_db, close_db,
)

def init_database():
    """Initialize the database with tables."""
    init_db()
    # Create tables (safe=True avoids errors if they exist)
    db.create_tables([Project, Issue, Task, WorkLog], safe=True)
    print("✅ Database initialized successfully!")

if __name__ == '__main__':
    try:
        init_database()
    finally:
        close_db()