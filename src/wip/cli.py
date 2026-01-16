"""WIP - Task tracker CLI with tree visualization."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import click

from .model import BlockedTask, Edge, HistoryEntry, State, Task
from .render import (
    render_blocked,
    render_dag,
    render_dag_simple,
    render_history_table,
    render_recent_history,
    render_recent_history_simple,
    render_stale_tasks,
    render_weekly_simple,
    render_weekly_table,
)
from .iterm2 import is_iterm2
from .storage import backup_state, load_state, save_state


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.version_option(version="0.1.0")
@click.pass_context
def main(ctx):
    """WIP - Manage tasks with tree visualization."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(status)


@main.command(name="status")
@click.option("--done", is_flag=True, help="Show completed tasks with dates")
def status(done: bool):
    """Show tasks with tree visualization and blocked list."""
    state = load_state()

    if done:
        # Show completed tasks with created and completed dates
        if not state.history:
            click.echo("No completed tasks.")
            return

        render_history_table(state.history)
        return

    if not state.tasks and not state.blocked:
        click.echo("No tasks yet. Use 'wip add <title>' to add a task.")
        return

    # Use simple renderer for iTerm2 (supports inline images)
    # Use Rich panels for other terminals
    if is_iterm2():
        render_dag_simple(state)
    else:
        render_dag(state)
        render_blocked(state.blocked)


@main.command()
def weekly():
    """Show tasks completed this week."""
    state = load_state()

    if not state.history:
        click.echo("No tasks completed this week.")
        return

    # Get Monday of current week
    today = datetime.now()
    monday = today - __import__("datetime").timedelta(days=today.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    sunday = monday + __import__("datetime").timedelta(days=6)

    # Filter tasks completed this week
    week_tasks = []
    for entry in state.history:
        completed_dt = entry.completed_datetime
        if completed_dt >= monday:
            week_tasks.append(entry)

    if not week_tasks:
        click.echo("No tasks completed this week.")
        return

    # Use simple renderer for iTerm2 (supports inline images)
    if is_iterm2():
        render_weekly_simple(week_tasks, monday, sunday)
    else:
        render_weekly_table(week_tasks, monday, sunday)


@main.command(name="history")
@click.option("-n", "--count", default=10, help="Number of recent tasks to show")
def history(count: int):
    """Show recently completed tasks."""
    state = load_state()

    if not state.history:
        click.echo("No completed tasks.")
        return

    # Sort by completed_at descending and take the most recent
    sorted_history = sorted(
        state.history,
        key=lambda e: e.completed_at or "",
        reverse=True,
    )
    recent = sorted_history[:count]

    # Use simple renderer for iTerm2 (supports inline images)
    if is_iterm2():
        render_recent_history_simple(recent)
    else:
        render_recent_history(recent)


@main.command()
def stale():
    """Show tasks older than stale_days that are not active."""
    state = load_state()
    stale_days = state.config.stale_days
    cutoff = datetime.now() - timedelta(days=stale_days)

    stale_tasks = []
    for task in state.tasks.values():
        if not task.active:
            created = task.created_datetime
            if created and created < cutoff:
                stale_tasks.append(task)

    # Also check blocked tasks
    stale_blocked = []
    for blocked in state.blocked:
        created = blocked.created_datetime
        if created and created < cutoff:
            stale_blocked.append(blocked)

    if not stale_tasks and not stale_blocked:
        click.echo(f"No stale tasks (older than {stale_days} days).")
        return

    render_stale_tasks(stale_tasks, stale_blocked, stale_days)


@main.command()
@click.argument("title")
@click.option("--blocked", "-b", help="Add as blocked by this person")
def add(title: str, blocked: str | None):
    """Add a new task."""
    state = load_state()
    task_id = state.next_id
    state.next_id += 1
    now = datetime.now().isoformat()

    if blocked:
        # Add as blocked task
        blocked_task = BlockedTask(id=task_id, title=title, blocker=blocked, created_at=now)
        state.blocked.append(blocked_task)
        save_state(state)
        click.echo(f"Added blocked task [{task_id}]: {title} (blocked by: {blocked})")
    else:
        # Add as regular task
        task = Task(id=task_id, title=title, created_at=now)
        state.tasks[str(task_id)] = task
        save_state(state)
        click.echo(f"Added task [{task_id}]: {title}")


def _would_create_cycle(state, from_id: int, to_id: int) -> bool:
    """Check if adding edge from_id -> to_id would create a cycle using DFS."""
    # If we can reach from_id starting from to_id, adding from_id -> to_id creates a cycle
    visited = set()
    stack = [to_id]

    while stack:
        node = stack.pop()
        if node == from_id:
            return True
        if node in visited:
            continue
        visited.add(node)
        for edge in state.get_edges_from(node):
            stack.append(edge.to_id)

    return False


def _task_exists(state, task_id: int) -> bool:
    """Check if a task exists (in tasks or blocked)."""
    return state.get_task(task_id) is not None or state.get_blocked(task_id) is not None


def _get_all_descendants(state, task_id: int) -> set[int]:
    """Get all tasks that depend on the given task (directly or indirectly)."""
    descendants: set[int] = set()
    stack = [task_id]
    while stack:
        current = stack.pop()
        for edge in state.edges:
            if edge.from_id == current and edge.to_id not in descendants:
                descendants.add(edge.to_id)
                stack.append(edge.to_id)
    return descendants


def _move_to_hold(state, task_id: int, blocker: str) -> str | None:
    """Move a task to on hold. Returns the task title if moved, None if already on hold."""
    task = state.get_task(task_id)
    if not task:
        return None  # Already on hold or doesn't exist

    # Remove from tasks and add to blocked
    del state.tasks[str(task_id)]
    blocked_task = BlockedTask(
        id=task_id, title=task.title, blocker=blocker, created_at=task.created_at
    )
    state.blocked.append(blocked_task)
    return task.title


@main.command()
@click.argument("from_id", type=int)
@click.argument("to_id", type=int)
def link(from_id: int, to_id: int):
    """Add a dependency between tasks."""
    state = load_state()

    # Verify both tasks exist (in tasks or blocked)
    if not _task_exists(state, from_id):
        click.echo(f"Error: Task {from_id} not found", err=True)
        return
    if not _task_exists(state, to_id):
        click.echo(f"Error: Task {to_id} not found", err=True)
        return

    # Check for self-loop
    if from_id == to_id:
        click.echo("Error: Cannot link a task to itself", err=True)
        return

    # Check if edge already exists
    if state.has_edge(from_id, to_id):
        click.echo(f"Error: Edge {from_id} -> {to_id} already exists", err=True)
        return

    # Check for cycle
    if _would_create_cycle(state, from_id, to_id):
        click.echo(f"Error: Adding edge {from_id} -> {to_id} would create a cycle", err=True)
        return

    state.edges.append(Edge(from_id=from_id, to_id=to_id))

    # If from_id is on hold, cascade to to_id and all its descendants
    blocked_parent = state.get_blocked(from_id)
    if blocked_parent:
        moved_tasks: list[str] = []
        # Move to_id and all its descendants to hold
        all_to_move = {to_id} | _get_all_descendants(state, to_id)
        for tid in all_to_move:
            title = _move_to_hold(state, tid, f"Task {from_id}")
            if title:
                moved_tasks.append(f"[{tid}] {title}")

        save_state(state)
        click.echo(f"Linked task {from_id} -> {to_id}")
        if moved_tasks:
            click.echo(f"Moved to hold (blocked by Task {from_id}): {', '.join(moved_tasks)}")
    else:
        save_state(state)
        click.echo(f"Linked task {from_id} -> {to_id}")


@main.command()
@click.argument("from_id", type=int)
@click.argument("to_id", type=int)
def unlink(from_id: int, to_id: int):
    """Remove a dependency between tasks."""
    state = load_state()

    if not state.has_edge(from_id, to_id):
        click.echo(f"Error: Edge {from_id} -> {to_id} not found", err=True)
        return

    state.edges = [e for e in state.edges if not (e.from_id == from_id and e.to_id == to_id)]
    save_state(state)
    click.echo(f"Unlinked task {from_id} -> {to_id}")


@main.command()
@click.argument("task_id", type=int)
@click.argument("state_name", type=click.Choice(["active", "inactive", "done", "hold", "release", "gone"]))
@click.option("--by", help="Who/what is holding this task (required for 'hold' state)")
def mark(task_id: int, state_name: str, by: str | None):
    """Mark a task with a state: active, inactive, done, hold, release, gone.

    \b
    State machine:
    ┌────────────────────────────────────────────────┐
    │                                                │
    │          ┌──────────┐                          │
    │  ┌──────→│  ACTIVE  │───────┐                  │
    │  │       └──────────┘       │                  │
    │  │         │      ↑         │                  │
    │  │ inactive│      │active   │                  │
    │  │         ↓      │         │                  │
    │  │       ┌──────────┐       │                  │
    │  │hold   │ INACTIVE │←──────┼───┐              │
    │  │       └──────────┘       │   │release       │
    │  │              │      hold │   │              │
    │  │              └─────→┌────↓───┴───┐          │
    │  └─────────────────────│  ON HOLD   │          │
    │                        └────────────┘          │
    │                                                │
    │────────────────────────────────────────────────│
    │              done ↓         ↓ gone             │
    │           ┌──────────┐  ┌──────────┐           │
    │           │   DONE   │  │   GONE   │           │
    │           └──────────┘  └──────────┘           │
    │           (active/       (any state)           │
    │            inactive)                           │
    └────────────────────────────────────────────────┘
    """
    state = load_state()

    if state_name == "active":
        task = state.get_task(task_id)
        if not task:
            # Check if it's on hold
            if state.get_blocked(task_id):
                click.echo(
                    f"Error: Task {task_id} is on hold. Use 'wip mark {task_id} release' first.",
                    err=True,
                )
                return
            click.echo(f"Error: Task {task_id} not found", err=True)
            return

        if task.active:
            click.echo(f"Task {task_id} is already active")
            return

        # Check for incomplete dependencies
        dependencies = state.get_edges_to(task_id)
        if dependencies:
            dep_ids = [str(e.from_id) for e in dependencies]
            click.echo(
                f"Error: Cannot activate task {task_id}. "
                f"It depends on incomplete tasks [{', '.join(dep_ids)}]. "
                f"Complete those first.",
                err=True,
            )
            return

        # Check max_active limit
        current_active = state.active_count()
        if current_active >= state.config.max_active:
            click.echo(
                f"Error: Maximum active tasks ({state.config.max_active}) reached. "
                f"Use 'wip mark <id> inactive' or 'wip mark <id> done' first.",
                err=True,
            )
            return

        task.active = True
        save_state(state)
        click.echo(f"Marked task [{task_id}] as active")

    elif state_name == "inactive":
        task = state.get_task(task_id)
        if not task:
            # Check if it's on hold
            if state.get_blocked(task_id):
                click.echo(
                    f"Error: Task {task_id} is on hold. Use 'wip mark {task_id} release' first.",
                    err=True,
                )
                return
            click.echo(f"Error: Task {task_id} not found", err=True)
            return

        if not task.active:
            click.echo(f"Task {task_id} is not active")
            return

        task.active = False
        save_state(state)
        click.echo(f"Marked task [{task_id}] as inactive")

    elif state_name == "done":
        task = state.get_task(task_id)
        if not task:
            # Check if it's on hold
            if state.get_blocked(task_id):
                click.echo(
                    f"Error: Task {task_id} is on hold. Use 'wip mark {task_id} release' first.",
                    err=True,
                )
                return
            click.echo(f"Error: Task {task_id} not found", err=True)
            return

        # Check for incomplete dependencies (tasks this task depends on)
        dependencies = state.get_edges_to(task_id)
        if dependencies:
            dep_ids = [str(e.from_id) for e in dependencies]
            click.echo(
                f"Error: Cannot complete task {task_id}. "
                f"It depends on incomplete tasks [{', '.join(dep_ids)}]. "
                f"Complete those first.",
                err=True,
            )
            return

        # Remove from tasks
        del state.tasks[str(task_id)]

        # Remove any edges connected to this task
        state.edges = [e for e in state.edges if e.from_id != task_id and e.to_id != task_id]

        # Add to history
        now = datetime.now().isoformat()
        entry = HistoryEntry(
            id=task_id, title=task.title, completed_at=now, created_at=task.created_at
        )
        state.history.append(entry)

        save_state(state)
        click.echo(f"Completed task [{task_id}]: {task.title}")

    elif state_name == "hold":
        if not by:
            click.echo("Error: --by option is required for 'hold' state", err=True)
            return

        task = state.get_task(task_id)
        if not task:
            # Check if it's already on hold
            if state.get_blocked(task_id):
                click.echo(f"Error: Task {task_id} is already on hold", err=True)
                return
            click.echo(f"Error: Task {task_id} not found", err=True)
            return

        # Remove from tasks and add to blocked (keep edges for tree display)
        del state.tasks[str(task_id)]
        blocked_task = BlockedTask(
            id=task_id, title=task.title, blocker=by, created_at=task.created_at
        )
        state.blocked.append(blocked_task)
        save_state(state)
        click.echo(f"Task [{task_id}] on hold ({by})")

    elif state_name == "release":
        blocked = state.get_blocked(task_id)
        if not blocked:
            click.echo(f"Error: Task {task_id} not found in hold", err=True)
            return

        # Remove from blocked and add to tasks
        state.blocked = [b for b in state.blocked if b.id != task_id]
        task = Task(id=task_id, title=blocked.title, created_at=blocked.created_at)
        state.tasks[str(task_id)] = task
        save_state(state)
        click.echo(f"Released task [{task_id}]: {blocked.title}")

    elif state_name == "gone":
        # Try to remove from tasks
        if str(task_id) in state.tasks:
            task = state.tasks.pop(str(task_id))
            state.edges = [e for e in state.edges if e.from_id != task_id and e.to_id != task_id]
            save_state(state)
            click.echo(f"Task [{task_id}] gone: {task.title}")
            return

        # Try to remove from blocked
        for i, blocked in enumerate(state.blocked):
            if blocked.id == task_id:
                state.blocked.pop(i)
                save_state(state)
                click.echo(f"Task [{task_id}] gone: {blocked.title}")
                return

        # Try to remove from history
        for i, entry in enumerate(state.history):
            if entry.id == task_id:
                state.history.pop(i)
                save_state(state)
                click.echo(f"Task [{task_id}] gone: {entry.title}")
                return

        click.echo(f"Error: Task {task_id} not found", err=True)


@main.command()
@click.argument("key")
@click.argument("value")
def config(key: str, value: str):
    """Set configuration values.

    Available keys:

    \b
      max_active  Maximum number of active tasks allowed (default: 2)
      stale_days  Days before inactive task is considered stale (default: 14)
    """
    state = load_state()

    if key == "max_active":
        try:
            max_val = int(value)
            if max_val < 1:
                click.echo("Error: max_active must be at least 1", err=True)
                return
            state.config.max_active = max_val
            save_state(state)
            click.echo(f"Set max_active = {max_val}")
        except ValueError:
            click.echo("Error: max_active must be an integer", err=True)
    elif key == "stale_days":
        try:
            days = int(value)
            if days < 1:
                click.echo("Error: stale_days must be at least 1", err=True)
                return
            state.config.stale_days = days
            save_state(state)
            click.echo(f"Set stale_days = {days}")
        except ValueError:
            click.echo("Error: stale_days must be an integer", err=True)
    else:
        click.echo(f"Error: Unknown config key '{key}'", err=True)


@main.command()
def reset():
    """Clear all tasks (backup saved to ~/.wip/backups/)."""
    state = load_state()

    # Create backup
    backup_path = backup_state()
    if backup_path:
        click.echo(f"Backup saved to: {backup_path}")

    # Preserve config, reset everything else
    config = state.config
    state = __import__("wip.model", fromlist=["State"]).State()
    state.config = config

    save_state(state)
    click.echo("State reset. All tasks cleared.")


@main.command()
@click.argument("file", type=click.Path())
def save(file: str):
    """Save all tasks to a file."""
    state = load_state()
    path = Path(file)
    path.write_text(json.dumps(state.to_dict(), indent=2))
    task_count = len(state.tasks) + len(state.blocked)
    click.echo(f"Saved {task_count} tasks to {file}")


def _remap_state(imported: State, start_id: int) -> tuple[State, dict[int, int]]:
    """Remap all IDs in imported state starting from start_id.

    Returns the remapped state and the ID mapping.
    """
    # Build ID mapping for all IDs in imported state
    all_ids: set[int] = set()
    for tid in imported.tasks:
        all_ids.add(int(tid))
    for b in imported.blocked:
        all_ids.add(b.id)
    for h in imported.history:
        all_ids.add(h.id)

    id_map: dict[int, int] = {}
    next_id = start_id
    for old_id in sorted(all_ids):
        id_map[old_id] = next_id
        next_id += 1

    # Remap tasks
    new_tasks: dict[str, Task] = {}
    for tid, task in imported.tasks.items():
        new_id = id_map[int(tid)]
        new_tasks[str(new_id)] = Task(
            id=new_id,
            title=task.title,
            active=task.active,
            created_at=task.created_at,
        )

    # Remap edges
    new_edges: list[Edge] = []
    for edge in imported.edges:
        if edge.from_id in id_map and edge.to_id in id_map:
            new_edges.append(Edge(
                from_id=id_map[edge.from_id],
                to_id=id_map[edge.to_id],
            ))

    # Remap blocked tasks
    new_blocked: list[BlockedTask] = []
    for b in imported.blocked:
        new_id = id_map[b.id]
        new_blocked.append(BlockedTask(
            id=new_id,
            title=b.title,
            blocker=b.blocker,
            created_at=b.created_at,
        ))

    # Remap history
    new_history: list[HistoryEntry] = []
    for h in imported.history:
        new_id = id_map[h.id]
        new_history.append(HistoryEntry(
            id=new_id,
            title=h.title,
            completed_at=h.completed_at,
            created_at=h.created_at,
        ))

    remapped = State(
        tasks=new_tasks,
        edges=new_edges,
        blocked=new_blocked,
        history=new_history,
        next_id=next_id,
        config=imported.config,
    )

    return remapped, id_map


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--merge", is_flag=True, help="Merge with existing tasks instead of replacing")
def load(file: str, merge: bool):
    """Load tasks from a file."""
    path = Path(file)

    try:
        data = json.loads(path.read_text())
        imported_state = State.from_dict(data)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in {file}: {e}", err=True)
        return
    except (KeyError, TypeError) as e:
        click.echo(f"Error: Invalid state format in {file}: {e}", err=True)
        return

    if merge:
        current_state = load_state()

        # Remap imported IDs to avoid conflicts
        remapped, id_map = _remap_state(imported_state, current_state.next_id)

        # Merge into current state
        current_state.tasks.update(remapped.tasks)
        current_state.edges.extend(remapped.edges)
        current_state.blocked.extend(remapped.blocked)
        current_state.history.extend(remapped.history)
        current_state.next_id = remapped.next_id

        save_state(current_state)

        task_count = len(remapped.tasks) + len(remapped.blocked)
        click.echo(f"Merged {task_count} tasks from {file}")
        if id_map:
            click.echo(f"Task IDs remapped: {len(id_map)} IDs reassigned")
    else:
        # Create backup first
        backup_path = backup_state()
        if backup_path:
            click.echo(f"Backup saved to: {backup_path}")

        save_state(imported_state)
        task_count = len(imported_state.tasks) + len(imported_state.blocked)
        click.echo(f"Loaded {task_count} tasks from {file}")


@main.command()
@click.option("--disable", is_flag=True, help="Disable sharing and delete the gist")
@click.option("--status", "show_status", is_flag=True, help="Show sharing status")
@click.option("--refresh", is_flag=True, help="Force refresh the shared content")
def share(disable: bool, show_status: bool, refresh: bool):
    """Share WIP status via GitHub Gist.

    \b
    Usage:
      wip share           Enable sharing, show link
      wip share --status  Show current sharing status
      wip share --refresh Force update the shared content
      wip share --disable Disable sharing and delete gist

    Requires: gh CLI authenticated (https://cli.github.com/)
    """
    from .gist import (
        check_gh_auth,
        create_gist,
        delete_gist,
        remove_gist_file,
        update_gist,
    )
    from .render_md import render_state_md

    state = load_state()

    if show_status:
        if state.config.share.enabled and state.config.share.gist_url:
            click.echo("Sharing: enabled")
            click.echo(f"URL: {state.config.share.gist_url}")
        else:
            click.echo("Sharing: disabled")
        return

    if disable:
        if not state.config.share.enabled:
            click.echo("Sharing is already disabled")
            return

        if state.config.share.gist_id:
            click.echo("Deleting gist...")
            result = delete_gist(state.config.share.gist_id)
            if not result.success:
                click.echo(f"Warning: Could not delete gist: {result.error}", err=True)

        state.config.share.enabled = False
        state.config.share.gist_id = None
        state.config.share.gist_url = None
        save_state(state)
        click.echo("Sharing disabled")
        return

    if refresh:
        if not state.config.share.enabled or not state.config.share.gist_id:
            click.echo("Sharing is not enabled. Run 'wip share' first.", err=True)
            return

        # Clean up old HTML file if it exists
        remove_gist_file(state.config.share.gist_id, "wip.html")

        md = render_state_md(state)
        result = update_gist(state.config.share.gist_id, "wip.md", md)

        if result.success:
            click.echo(f"Updated: {state.config.share.gist_url}")
        else:
            click.echo(f"Error: {result.error}", err=True)
        return

    # Default: enable sharing
    is_auth, auth_error = check_gh_auth()
    if not is_auth:
        click.echo(f"Error: {auth_error}", err=True)
        click.echo("Run 'gh auth login' to authenticate.")
        return

    if state.config.share.enabled and state.config.share.gist_url:
        click.echo(f"Sharing already enabled: {state.config.share.gist_url}")
        click.echo("Use --refresh to force update, --disable to turn off.")
        return

    click.echo("Creating shareable link...")
    md = render_state_md(state)
    result = create_gist(
        filename="wip.md",
        content=md,
        description="WIP Task Status (auto-updated)",
    )

    if not result.success:
        click.echo(f"Error: {result.error}", err=True)
        return

    state.config.share.enabled = True
    state.config.share.gist_id = result.gist_id
    state.config.share.gist_url = result.gist_url
    save_state(state, skip_publish=True)  # Gist already has content

    click.echo("Sharing enabled!")
    click.echo(f"URL: {result.gist_url}")
    click.echo("")
    click.echo("This link will auto-update when you modify tasks.")


if __name__ == "__main__":
    main()
