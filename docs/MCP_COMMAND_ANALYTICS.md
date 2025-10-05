# MCP Command Analytics Platform

The PM system includes a powerful analytics platform to help you optimize your MCP server configuration by tracking command usage and providing recommendations.

## Overview

The analytics platform consists of three main components:

1. **Usage Tracking**: Automatic logging of every MCP command execution
2. **Configuration Management**: Categorize and enable/disable commands based on your workflow
3. **Analytics Tool**: Analyze usage patterns and get optimization recommendations

## Features

### Command Categorization

All MCP commands are categorized into three tiers:

- **Required**: Essential commands needed for basic PM functionality (e.g., `pm_create_issue`, `pm_list_issues`, `pm_status`)
- **Recommended**: Very useful commands for common workflows (e.g., `pm_commit`, `pm_create_branch`, `pm_search_issues`)
- **Optional**: Nice-to-have commands for specialized workflows (e.g., `pm_daily_standup`, `pm_blocked_issues`, `pm_add_submodule`)

### Usage Logging

Every time a command is executed, the system logs:
- Command name
- Timestamp
- Project ID (if applicable)

**Note**: Only minimal data is logged - no sensitive information or command parameters are stored.

### Command Filtering

You can disable unused commands by editing the configuration file. Disabled commands will:
- Return an error message if called
- Not clutter the LLM's tool list
- Reduce cognitive overhead for the AI agent

## Usage

### View Command Usage Analytics

Run the analytics tool to see which commands you're actually using:

```bash
make optimize
```

Or analyze a different time period (e.g., last 7 days):

```bash
python3 scripts/analyze_command_usage.py 7
```

### Sample Output

```
📊 MCP Command Usage Analysis (Last 30 days)
======================================================================

✅ Commands Used: 15
❌ Commands Unused: 16
📦 Total Commands: 31

📈 Top 10 Most Used Commands:
Rank   Command                             Count    Category      Last Used
------------------------------------------------------------------------------------------
1      pm_list_issues                      45       required      2025-10-05 11:15
2      pm_create_issue                     12       required      2025-10-05 10:30
3      pm_start_work                       11       required      2025-10-05 09:45
4      pm_log_work                         28       required      2025-10-04 16:20
...

💡 Optimization Recommendations
======================================================================

🔹 Optional Commands Not Used (Safe to Disable):
   - pm_blocked_issues
   - pm_daily_standup
   - pm_add_submodule
   - pm_remove_submodule

⚠️  Recommended Commands Not Used (Consider Your Workflow):
   - pm_commit
   - pm_create_branch

📝 To disable unused commands:
   Edit mcp/mcp_commands.json and set 'enabled': false for commands you don't need.
```

### Disable Unused Commands

1. Edit `mcp/mcp_commands.json`
2. Set `"enabled": false` for commands you don't use:

```json
{
  "commands": {
    "pm_daily_standup": {
      "category": "optional",
      "enabled": false,
      "description": "Generate daily standup report"
    }
  }
}
```

3. Restart your MCP server (restart Claude Desktop)

Disabled commands will return an error if called, helping you identify if they're unexpectedly needed.

## Configuration File

The configuration file is located at `mcp/mcp_commands.json`.

### Structure

```json
{
  "commands": {
    "pm_example_command": {
      "category": "optional",
      "enabled": true,
      "description": "Example command description"
    }
  },
  "metadata": {
    "version": "1.0.0",
    "last_updated": "2025-10-05",
    "description": "MCP command configuration for PM server"
  }
}
```

### Fields

- `category`: One of "required", "recommended", or "optional"
- `enabled`: Boolean flag to enable/disable the command
- `description`: Human-readable description of what the command does

## Best Practices

1. **Start with everything enabled**: Let the system track your natural usage patterns
2. **Analyze after 1-2 weeks**: Run `make optimize` after you've used the system enough to establish patterns
3. **Be conservative**: Only disable "optional" commands initially
4. **Review "recommended" carefully**: These commands might be useful in situations you haven't encountered yet
5. **Never disable "required" commands**: These are essential for basic functionality
6. **Re-enable if needed**: If you disable a command and find you need it, just set `"enabled": true` and restart

## Database

Usage data is stored in the `CommandUsage` table with the following schema:

```sql
CREATE TABLE commandusage (
    id INTEGER PRIMARY KEY,
    command_name VARCHAR(100),
    timestamp_utc DATETIME,
    project_id VARCHAR(64)
);
```

The table is indexed on `command_name`, `timestamp_utc`, and `project_id` for fast analytics queries.

## Privacy

The analytics system only logs:
- Command names
- Timestamps
- Project IDs

**No sensitive data is logged**, including:
- Command parameters
- Issue content
- User data
- File paths
- Code or artifacts

## Troubleshooting

### No usage data found

If you see "No usage data found", it means:
- Commands haven't been used yet (just started using the system)
- Usage logging just started (old commands weren't logged)

**Solution**: Use the PM system normally, then run `make optimize` again later.

### Commands still appear after disabling

If a disabled command still shows up:
1. Verify you edited `mcp/mcp_commands.json` correctly
2. Restart Claude Desktop to reload the MCP server
3. Check that JSON syntax is valid

### Analytics script errors

If the analytics script fails:
1. Ensure database is initialized: `make init-db`
2. Check Python dependencies: `make bootstrap-mcp`
3. Verify file path is correct

## Future Enhancements

Potential future improvements to the analytics platform:

- Performance metrics (command execution time)
- Usage patterns by time of day/day of week
- Correlation analysis (which commands are used together)
- Automatic configuration optimization
- Web UI dashboard for analytics
- Export analytics to CSV/JSON
- Command usage trends over time
