#!/usr/bin/env python3
"""Analyze MCP command usage and provide optimization recommendations"""
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / "mcp/src"))

from database import PMDatabase, DatabaseSession

def load_command_config():
    """Load command configuration"""
    config_path = Path(__file__).parent.parent / "mcp/mcp_commands.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {"commands": {}}

def analyze_usage(days=30):
    """Analyze command usage and provide recommendations"""
    config = load_command_config()
    commands_config = config.get("commands", {})

    print(f"\n📊 MCP Command Usage Analysis (Last {days} days)")
    print("=" * 70)

    with DatabaseSession():
        stats = PMDatabase.get_command_usage_stats(days)

        if not stats:
            print("\n⚠️  No usage data found. Commands haven't been used yet or logging just started.")
            print("\nAll commands are currently enabled. Use the system to generate usage data.")
            return

        used_commands = {s['command_name'] for s in stats}
        all_commands = set(commands_config.keys())
        unused_commands = all_commands - used_commands

        print(f"\n✅ Commands Used: {len(used_commands)}")
        print(f"❌ Commands Unused: {len(unused_commands)}")
        print(f"📦 Total Commands: {len(all_commands)}")

        print(f"\n📈 Top 10 Most Used Commands:")
        print(f"{'Rank':<6} {'Command':<35} {'Count':<8} {'Category':<12} {'Last Used'}")
        print("-" * 90)

        for i, stat in enumerate(stats[:10], 1):
            cmd_name = stat['command_name']
            cmd_config = commands_config.get(cmd_name, {})
            category = cmd_config.get('category', 'unknown')
            last_used = stat.get('last_used', 'Never')
            if last_used and last_used != 'Never':
                last_used = datetime.fromisoformat(last_used.replace('Z', ''))
                last_used = last_used.strftime('%Y-%m-%d %H:%M')

            print(f"{i:<6} {cmd_name:<35} {stat['count']:<8} {category:<12} {last_used}")

        if unused_commands:
            print(f"\n\n💡 Optimization Recommendations")
            print("=" * 70)

            optional_unused = []
            recommended_unused = []

            for cmd in unused_commands:
                cmd_config = commands_config.get(cmd, {})
                category = cmd_config.get('category', 'unknown')
                if category == 'optional':
                    optional_unused.append(cmd)
                elif category == 'recommended':
                    recommended_unused.append(cmd)

            if optional_unused:
                print(f"\n🔹 Optional Commands Not Used (Safe to Disable):")
                for cmd in sorted(optional_unused):
                    print(f"   - {cmd}")

            if recommended_unused:
                print(f"\n⚠️  Recommended Commands Not Used (Consider Your Workflow):")
                for cmd in sorted(recommended_unused):
                    print(f"   - {cmd}")

            print(f"\n\n📝 To disable unused commands:")
            print(f"   Edit mcp/mcp_commands.json and set 'enabled': false for commands you don't need.")

        else:
            print(f"\n\n✅ All configured commands have been used!")
            print(f"   Your MCP setup is well-optimized for your workflow.")

        print(f"\n📊 Category Breakdown:")
        print("-" * 70)

        category_stats = {}
        for cmd_name in all_commands:
            cmd_config = commands_config.get(cmd_name, {})
            category = cmd_config.get('category', 'unknown')

            if category not in category_stats:
                category_stats[category] = {'total': 0, 'used': 0, 'enabled': 0}

            category_stats[category]['total'] += 1
            if cmd_config.get('enabled', True):
                category_stats[category]['enabled'] += 1
            if cmd_name in used_commands:
                category_stats[category]['used'] += 1

        for category in ['required', 'recommended', 'optional']:
            if category in category_stats:
                stats = category_stats[category]
                usage_pct = (stats['used'] / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f"{category.capitalize():<15} Total: {stats['total']:<3} Enabled: {stats['enabled']:<3} Used: {stats['used']:<3} ({usage_pct:.1f}%)")

        print("\n" + "=" * 70)

if __name__ == "__main__":
    days = 30
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print(f"Invalid days argument: {sys.argv[1]}")
            sys.exit(1)

    analyze_usage(days)
