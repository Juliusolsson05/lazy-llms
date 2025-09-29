# Cross-Machine Database Synchronization Guide

This guide explains how to sync your entire PM system state, including the SQLite database, between multiple machines (e.g., work laptop, personal MacBook, home desktop).

## 🎯 Why Use This?

If you work on the same project from multiple computers, you need a way to sync not just code, but also:
- Your PM database (issues, work logs, tasks)
- Local configuration files
- Server logs and event streams

This system uses a **secondary private Git remote** to sync everything while keeping the main repository clean for open source.

## 🚀 Quick Setup

### 1. Create a Private Sync Repository

Create a **private** GitHub repository for your sync (e.g., `my-project-sync`):
```bash
# This should be PRIVATE - never make it public!
# Go to GitHub and create: https://github.com/new
# Name it something like: projectname-sync-private
```

### 2. Initial Setup (Run Once Per Project)

On your first machine:
```bash
# Run the setup command
make -f Makefile.sync setup-sync

# When prompted, enter your private repo URL:
# git@github.com:yourusername/projectname-sync-private.git
```

This will:
- Add a remote called `sync` pointing to your private repo
- Create git hooks to prevent accidentally pushing DB to main remote
- Configure everything for safe syncing

### 3. First Push (From Primary Machine)

```bash
# Push your complete state to sync remote
make -f Makefile.sync push-sync
```

### 4. Pull on Other Machines

On your other computers:
```bash
# Clone the main repo first
git clone https://github.com/username/lazy-llms.git
cd lazy-llms

# Add the sync remote
make -f Makefile.sync setup-sync

# Pull the complete state including database
make -f Makefile.sync pull-sync

# Initialize the environment
make init-db  # This will use the synced database
```

## 📋 Daily Workflow

### Morning - Pull Latest State
```bash
# On the machine you're about to work on
make -f Makefile.sync pull-sync
make start  # Start services with updated DB
```

### Evening - Push Your Changes
```bash
# After finishing work
make -f Makefile.sync push-sync
```

### Check Sync Status
```bash
make -f Makefile.sync status-sync
```

## 🛠 Available Commands

| Command | Description |
|---------|-------------|
| `make -f Makefile.sync setup-sync` | Initial setup of sync remote |
| `make -f Makefile.sync push-sync` | Push everything to sync remote |
| `make -f Makefile.sync pull-sync` | Pull everything from sync remote |
| `make -f Makefile.sync status-sync` | Show sync status and info |
| `make -f Makefile.sync backup-before-sync` | Manual backup creation |

## ⚠️ Important Safety Features

### 1. Automatic Backups
Every sync operation automatically backs up your database to `backups/` folder.

### 2. Git Hook Protection
A pre-push hook prevents pushing database files to the main/origin remote.

### 3. Gitignore Switching
The system automatically switches between:
- `.gitignore` (main) - Excludes database and local files
- `.gitignore.sync` - Includes database for syncing

### 4. Confirmation Prompts
Push operations show what will be synced and ask for confirmation.

## 🔄 Conflict Resolution

If you accidentally modify the database on multiple machines:

### Option 1: Keep Remote Version
```bash
# Discard local changes and use remote
make -f Makefile.sync backup-before-sync
git checkout -- data/jira_lite.db
make -f Makefile.sync pull-sync
```

### Option 2: Keep Local Version
```bash
# Keep your local version
make -f Makefile.sync push-sync --force
```

### Option 3: Manual Merge
```bash
# Back up both versions
cp data/jira_lite.db data/jira_lite.local.db
make -f Makefile.sync pull-sync
cp data/jira_lite.db data/jira_lite.remote.db

# Now you have both versions to manually merge or choose from
```

## 🏗 Architecture

```
┌─────────────────┐          ┌─────────────────┐
│   Work Laptop   │          │ Personal Laptop │
│                 │          │                 │
│ ✓ Code          │          │ ✓ Code          │
│ ✓ Database      │◄────────►│ ✓ Database      │
│ ✓ Logs          │          │ ✓ Logs          │
│ ✓ Config        │          │ ✓ Config        │
└────────┬────────┘          └────────┬────────┘
         │                            │
         │      ┌──────────────┐     │
         └─────►│ Private Sync │◄────┘
                │    Remote     │
                │ (Everything)  │
                └──────────────┘

         ┌───────────────────────┐
         │   Public Main Remote  │
         │   (Code Only - Clean) │
         └───────────────────────┘
```

## 📝 What Gets Synced?

### ✅ Included in Sync
- `data/jira_lite.db` - Your PM database
- `data/events.jsonl` - Event log
- `mcp/server.log` - Server logs
- `.env` - Environment configuration (be careful!)
- All code changes

### ❌ Still Excluded
- Python cache (`__pycache__`, `*.pyc`)
- Virtual environments (`venv/`, `env/`)
- Editor files (`.vscode/`, `.idea/`, `.cursor/`)
- Build artifacts
- Temporary files
- Private keys and secrets (never sync these!)

## 🚨 Troubleshooting

### "Remote sync already exists"
```bash
# Remove and re-add
git remote remove sync
make -f Makefile.sync setup-sync
```

### "Permission denied pushing to sync"
```bash
# Check your SSH keys are set up for GitHub
ssh -T git@github.com

# Verify remote URL
git remote -v
```

### "Database locked" error
```bash
# Stop all services first
make stop

# Then try sync
make -f Makefile.sync pull-sync
```

### Accidentally pushed DB to main remote
```bash
# This should be prevented by git hooks, but if it happens:
# 1. Immediately remove from history (if not pulled by others)
git reset --hard HEAD~1
git push --force-with-lease

# 2. Clean up the main remote
# Contact repo admin to purge from history
```

## 🔒 Security Considerations

1. **Private Sync Repo**: Always use a PRIVATE repository for sync
2. **Sensitive Data**: Be careful with `.env` files containing secrets
3. **Access Control**: Only give sync repo access to your own machines
4. **Regular Backups**: The system auto-backs up, but keep external backups too
5. **Never Public**: Never make the sync repository public

## 💡 Pro Tips

1. **Sync Frequently**: Sync at the start and end of each work session
2. **Check Status**: Run `status-sync` to verify which mode you're in
3. **Use Branches**: Create feature branches for risky changes
4. **Backup Important Work**: Keep separate backups of critical databases
5. **Document Changes**: Use meaningful commit messages for sync commits

## 🎯 Example Workflow

```bash
# Monday - Work Laptop
cd ~/projects/lazy-llms
make -f Makefile.sync pull-sync    # Get weekend changes
make start                          # Work all day
# ... do work, create issues, log work ...
make -f Makefile.sync push-sync    # Push changes

# Monday Evening - Personal Laptop
cd ~/personal/lazy-llms
make -f Makefile.sync pull-sync    # Get work changes
make start                          # Continue working
# ... more work ...
make -f Makefile.sync push-sync    # Push changes

# Tuesday - Work Laptop
make -f Makefile.sync pull-sync    # Get personal laptop changes
# Continue seamlessly with full state!
```

## 🤝 Contributing

When contributing to the main project:
1. Always use the main `.gitignore` (excludes database)
2. Never commit database files to feature branches
3. Use `git push origin` for code contributions
4. Use `git push sync` only for personal state sync

---

Remember: **Main remote = Clean code only** | **Sync remote = Everything including state**