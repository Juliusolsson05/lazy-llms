#!/usr/bin/env python3
"""
Migrate command configuration from Python file to database
Run once to populate initial CommandConfig table
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "mcp/src"))

from database import PMDatabase, DatabaseSession, CommandConfig
from command_config import (
    REQUIRED_COMMANDS, RECOMMENDED_COMMANDS, OPTIONAL_COMMANDS
)

def migrate_command_config():
    """Migrate command configuration to database"""
    print("🚀 Starting command config migration...")
    print("=" * 50)

    PMDatabase.initialize()

    with DatabaseSession():
        migrated = 0
        updated = 0

        # Get current disabled commands from file
        try:
            from command_config import DISABLED_COMMANDS
            disabled_set = DISABLED_COMMANDS if isinstance(DISABLED_COMMANDS, set) else set()
        except:
            disabled_set = set()

        print(f"📊 Found {len(disabled_set)} disabled commands in Python file")

        # Migrate all commands
        all_commands = [
            (REQUIRED_COMMANDS, 'required', False),  # can_disable=False for required
            (RECOMMENDED_COMMANDS, 'recommended', True),
            (OPTIONAL_COMMANDS, 'optional', True)
        ]

        for commands_dict, category, can_disable in all_commands:
            for cmd_name, description in commands_dict.items():
                try:
                    # Try to get existing config
                    config = CommandConfig.get(
                        CommandConfig.command_name == cmd_name
                    )
                    print(f"  ✓ {cmd_name} already exists - updating")

                    # Update existing
                    config.category = category
                    config.description = description
                    config.can_disable = can_disable
                    config.enabled = cmd_name not in disabled_set
                    config.updated_utc = datetime.utcnow()
                    config.save()
                    updated += 1

                except:
                    # Create new entry
                    is_disabled = cmd_name in disabled_set
                    config = CommandConfig.create(
                        command_name=cmd_name,
                        category=category,
                        description=description,
                        enabled=not is_disabled,
                        can_disable=can_disable,
                        disabled_at=datetime.utcnow() if is_disabled else None,
                        disabled_by='migration' if is_disabled else None
                    )
                    migrated += 1
                    status = "DISABLED" if is_disabled else "enabled"
                    print(f"  + Migrated {cmd_name} ({category}) - {status}")

        print("\n" + "=" * 50)
        print(f"✅ Migration complete:")
        print(f"   📦 {migrated} new commands migrated")
        print(f"   🔄 {updated} existing commands updated")

        # Show summary
        total = CommandConfig.select().count()
        enabled = CommandConfig.select().where(CommandConfig.enabled == True).count()
        disabled = total - enabled
        required = CommandConfig.select().where(CommandConfig.category == 'required').count()

        print(f"\n📊 Database Summary:")
        print(f"   Total commands: {total}")
        print(f"   Enabled: {enabled}")
        print(f"   Disabled: {disabled}")
        print(f"   Required commands: {required}")

        if disabled > 0:
            print(f"\n🔇 Disabled commands:")
            disabled_configs = CommandConfig.select().where(CommandConfig.enabled == False)
            for config in disabled_configs:
                print(f"   - {config.command_name} ({config.category})")

if __name__ == '__main__':
    migrate_command_config()