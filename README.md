# wip

A minimal task tracker with tree visualization. Track what you're working on, manage dependencies, and keep focus on active tasks.

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Add tasks
wip add "Design API"
wip add "Implement endpoints"
wip add "Write tests"

# Link dependencies (task 1 must complete before task 2)
wip link 1 2

# Mark a task as active
wip mark 1 active

# View your tasks
wip
```

## Commands

### View Tasks

```bash
wip                    # Show all tasks as tree
wip status             # Same as above
wip status --done      # Show completed tasks with dates
```

Output shows tasks grouped by state (with bufo frog images in iTerm2):

**── ACTIVE ──**
- <img src="src/wip/assets/bufo_active.png" width="20"> [1] Design API
  - └── [2] Implement endpoints

**── ON HOLD ──**
- <img src="src/wip/assets/bufo_hold.png" width="20"> [4] Waiting on review (Bob)

**── BACKLOG ──**
- <img src="src/wip/assets/bufo_backlog.png" width="20"> [3] Write tests

### Add Tasks

```bash
wip add "Task title"                    # Add to backlog
wip add "Blocked task" -b "Waiting on Alice"  # Add as on-hold
```

### Manage Task State

```bash
wip mark 1 active      # Start working on task
wip mark 1 inactive    # Move back to backlog
wip mark 1 done        # Complete task (moves to history)
wip mark 1 hold --by "Reason"   # Put on hold
wip mark 1 release     # Release from hold
```

### Task Dependencies

```bash
wip link 1 2           # Task 2 depends on task 1
wip unlink 1 2         # Remove dependency
```

When you link to an on-hold task, dependent tasks automatically move to hold. When you link to an active task, dependent tasks appear dimmed in the ACTIVE panel.

### Share

Share your task status via GitHub Gist. Requires [gh CLI](https://cli.github.com/) authenticated.

```bash
wip share              # Enable sharing, get shareable link
wip share --status     # Show current sharing status
wip share --refresh    # Force update the shared content
wip share --disable    # Disable sharing and delete gist
```

Once enabled, the shared Markdown view auto-updates on every task change. The shared view shows:
- **Top of Mind** - Active tasks and workflows
- **On Hold** - Blocked tasks with blockers
- **Backlog** - Inactive tasks
- **This Week** - Tasks completed this week

### History & Progress

```bash
wip history            # Recent completed tasks
wip history -n 20      # Show last 20 completed
wip weekly             # Tasks completed this week
wip stale              # Tasks older than stale_days
```

### Save & Load

```bash
wip save backup.json              # Export all tasks
wip load backup.json              # Replace current state (creates backup)
wip load other.json --merge       # Merge with existing tasks
```

### Configuration

```bash
wip config max_active 3    # Max concurrent active tasks (default: 2)
wip config stale_days 7    # Days before task is stale (default: 14)
```

### Reset

```bash
wip reset              # Clear all tasks (backup saved to ~/.wip/backups/)
```

## Data Storage

Tasks are stored in `~/.wip/state.json`. Backups are saved to `~/.wip/backups/` before destructive operations.

## Task States

Tasks display with bufo frog images in iTerm2. In other terminals, fallback emojis are used:

| State | Bufo | Fallback | Description |
|-------|------|----------|-------------|
| Active | <img src="src/wip/assets/bufo_active.png" width="20"> | 🔥 | Currently working on |
| Backlog | <img src="src/wip/assets/bufo_backlog.png" width="20"> | 💤 | Inactive, waiting to start |
| On Hold | <img src="src/wip/assets/bufo_hold.png" width="20"> | 🔒 | Blocked by external dependency |
| Done | <img src="src/wip/assets/bufo_done.png" width="20"> | ✅ | Completed task |
| Stale | <img src="src/wip/assets/bufo_stale.png" width="20"> | ⚠️ | Task older than stale_days |

## Tips

- Keep max 2-3 tasks active at once
- Use `link` to build task sequences
- Check `wip stale` regularly to clean up old tasks
- Use `wip save` before major changes
