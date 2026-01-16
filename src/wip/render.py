"""Rendering utilities for WIP CLI output."""

import sys
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .iterm2 import bufo, is_iterm2
from .model import BlockedTask, HistoryEntry, State, Task


# ANSI color codes for simple output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"


def render_history_table(entries: list[HistoryEntry]) -> None:
    """Render completed tasks as a table."""
    console = Console()

    table = Table(title="COMPLETED TASKS", show_header=True, header_style="bold")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Title")
    table.add_column("Created", style="green")
    table.add_column("Completed", style="yellow")

    for entry in entries:
        created = entry.created_at[:10] if entry.created_at else "unknown"
        completed = entry.completed_at[:10] if entry.completed_at else "unknown"
        table.add_row(str(entry.id), entry.title, created, completed)

    console.print(table)


def render_recent_history(entries: list[HistoryEntry]) -> None:
    """Render recently completed tasks."""
    console = Console()

    lines = []
    for entry in entries:
        lines.append(f"{bufo('done')} {entry.title}")

    count = len(entries)
    content = "\n".join(lines)
    panel = Panel(
        content,
        title=f"[bold green]Recent History ({count} task{'s' if count != 1 else ''})[/bold green]",
        border_style="green",
        width=60,
    )
    console.print(panel)


def render_recent_history_simple(entries: list[HistoryEntry]) -> None:
    """Render recently completed tasks with iTerm2 inline images."""
    c = Colors
    count = len(entries)

    print(f"\n{c.BOLD}{c.GREEN}── Recent History ({count} task{'s' if count != 1 else ''}) ──{c.RESET}\n")

    for entry in entries:
        sys.stdout.write(f"  {bufo('done')} {entry.title}\n")
    sys.stdout.flush()
    print()


def render_stale_tasks(tasks: list[Task], blocked: list[BlockedTask], stale_days: int) -> None:
    """Render stale tasks."""
    console = Console()

    lines = []
    for task in sorted(tasks, key=lambda t: t.created_at or ""):
        created = task.created_at[:10] if task.created_at else "unknown"
        lines.append(f"{bufo('stale')} [cyan][{task.id}][/cyan] {task.title} [dim](created {created})[/dim]")

    for b in sorted(blocked, key=lambda t: t.created_at or ""):
        created = b.created_at[:10] if b.created_at else "unknown"
        lines.append(f"{bufo('hold')} [cyan][{b.id}][/cyan] {b.title} [dim](created {created}, {b.blocker})[/dim]")

    content = "\n".join(lines)
    count = len(tasks) + len(blocked)
    panel = Panel(
        content,
        title=f"[bold yellow]Stale Tasks ({count} older than {stale_days} days)[/bold yellow]",
        border_style="yellow",
    )
    console.print(panel)


def render_weekly_table(entries: list[HistoryEntry], monday: datetime, sunday: datetime) -> None:
    """Render weekly completed tasks as a table with weekdays as columns."""
    console = Console()

    week_range = f"Week of {monday.strftime('%b %d')} - {sunday.strftime('%b %d, %Y')}"

    # Group tasks by weekday (0=Mon, 4=Fri) - weekdays only
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    tasks_by_day: dict[int, list[str]] = {i: [] for i in range(5)}

    for entry in entries:
        day_idx = entry.completed_datetime.weekday()
        if day_idx < 5:  # Only include weekdays
            tasks_by_day[day_idx].append(entry.title)

    # Find max tasks in any day for row count
    max_tasks = max((len(tasks_by_day[i]) for i in range(5)), default=0)

    if max_tasks == 0:
        console.print("[dim]No tasks completed on weekdays this week.[/dim]")
        return

    # Wrap text helper - wraps text to fit within max_width
    max_width = 16

    def wrap_text(text: str) -> str:
        if len(text) <= max_width:
            return text
        lines = []
        while text:
            if len(text) <= max_width:
                lines.append(text)
                break
            # Find a good break point
            break_at = max_width
            space_idx = text.rfind(" ", 0, max_width)
            if space_idx > 0:
                break_at = space_idx
            lines.append(text[:break_at].rstrip())
            text = text[break_at:].lstrip()
        return "\n".join(lines)

    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1), expand=False)
    for day_idx in range(5):
        table.add_column(day_names[day_idx], justify="left", vertical="top")

    # Add rows - use bufo fallback emoji for done tasks
    for row_idx in range(max_tasks):
        row = []
        for day_idx in range(5):
            tasks = tasks_by_day[day_idx]
            if row_idx < len(tasks):
                wrapped = wrap_text(tasks[row_idx])
                row.append(f"{bufo('done')} {wrapped}")
            else:
                row.append("")
        table.add_row(*row)

    count = sum(len(tasks_by_day[i]) for i in range(5))
    footer = f"Total: {count} task{'s' if count != 1 else ''} completed"

    panel = Panel(
        table,
        title=f"[bold green]{week_range}[/bold green]",
        border_style="green",
        subtitle=f"[dim]{footer}[/dim]",
        expand=False,
    )
    console.print(panel)


def render_weekly_simple(entries: list[HistoryEntry], monday: datetime, sunday: datetime) -> None:
    """Render weekly completed tasks with iTerm2 inline images."""
    week_range = f"Week of {monday.strftime('%b %d')} - {sunday.strftime('%b %d, %Y')}"

    # Group tasks by weekday (0=Mon, 4=Fri) - weekdays only
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    tasks_by_day: dict[int, list[str]] = {i: [] for i in range(5)}

    for entry in entries:
        day_idx = entry.completed_datetime.weekday()
        if day_idx < 5:  # Only include weekdays
            tasks_by_day[day_idx].append(entry.title)

    # Find max tasks in any day for row count
    max_tasks = max((len(tasks_by_day[i]) for i in range(5)), default=0)

    if max_tasks == 0:
        print("No tasks completed on weekdays this week.")
        return

    c = Colors

    print(f"\n{c.BOLD}{c.GREEN}── {week_range} ──{c.RESET}\n")

    # Calculate column widths
    col_width = 18
    text_width = col_width - 3  # Account for emoji

    def wrap_text(text: str) -> list[str]:
        """Wrap text into multiple lines."""
        if len(text) <= text_width:
            return [text]
        lines = []
        while text:
            if len(text) <= text_width:
                lines.append(text)
                break
            break_at = text_width
            space_idx = text.rfind(" ", 0, text_width)
            if space_idx > 0:
                break_at = space_idx
            lines.append(text[:break_at].rstrip())
            text = text[break_at:].lstrip()
        return lines

    # Print header
    header = " ".join(f"{c.BOLD}{c.CYAN}{name:^{col_width}}{c.RESET}" for name in day_names)
    sys.stdout.write(header + "\n")
    sys.stdout.write("-" * (col_width * 5 + 4) + "\n")

    # Build wrapped content for each day
    wrapped_by_day: dict[int, list[list[str]]] = {i: [] for i in range(5)}
    for day_idx in range(5):
        for task in tasks_by_day[day_idx]:
            wrapped_by_day[day_idx].append(wrap_text(task))

    # Print rows - need to handle multi-line cells
    for row_idx in range(max_tasks):
        # Get max lines needed for this row
        max_lines = 1
        for day_idx in range(5):
            if row_idx < len(wrapped_by_day[day_idx]):
                max_lines = max(max_lines, len(wrapped_by_day[day_idx][row_idx]))

        # Print each line of this row
        for line_idx in range(max_lines):
            row_parts = []
            for day_idx in range(5):
                if row_idx < len(wrapped_by_day[day_idx]):
                    lines = wrapped_by_day[day_idx][row_idx]
                    if line_idx < len(lines):
                        if line_idx == 0:
                            text = f"{bufo('done')} {lines[line_idx]}"
                        else:
                            text = f"   {lines[line_idx]}"
                        row_parts.append(f"{text:<{col_width}}")
                    else:
                        row_parts.append(" " * col_width)
                else:
                    row_parts.append(" " * col_width)
            sys.stdout.write(" ".join(row_parts) + "\n")
    sys.stdout.flush()

    count = sum(len(tasks_by_day[i]) for i in range(5))
    print(f"\n{c.DIM}Total: {count} task{'s' if count != 1 else ''} completed{c.RESET}\n")


def _build_dag_content(
    task_ids: set[int],
    edges: list,
    format_task: callable,
    format_task_no_emoji: callable,
) -> str:
    """Build tree content for a set of tasks.

    Returns a string with tree structure for linked tasks and plain list for isolated tasks.
    Root tasks and standalone tasks get emoji, child tasks don't.
    """
    if not task_ids:
        return ""

    # Build adjacency maps for tasks in this set
    children: dict[int, list[int]] = {tid: [] for tid in task_ids}
    parents: dict[int, list[int]] = {tid: [] for tid in task_ids}

    for edge in edges:
        # Only include edges where both endpoints are in our set
        if edge.from_id in task_ids and edge.to_id in task_ids:
            children[edge.from_id].append(edge.to_id)
            parents[edge.to_id].append(edge.from_id)

    # Separate isolated tasks (no edges) from linked tasks
    isolated_ids = [tid for tid in task_ids if not children[tid] and not parents[tid]]
    linked_ids = task_ids - set(isolated_ids)

    lines: list[str] = []

    # Build tree for linked tasks using manual formatting
    if linked_ids:
        # Find root tasks (no parents within linked set)
        roots = [tid for tid in linked_ids if not parents.get(tid, [])]
        roots.sort()

        visited: set[int] = set()

        def add_lines(task_id: int, prefix: str = "", is_last: bool = True, depth: int = 0) -> None:
            if task_id in visited or depth > 10:
                return
            visited.add(task_id)

            task_children = sorted(children.get(task_id, []))

            # Root tasks (depth 0) get emoji, children don't
            formatter = format_task if depth == 0 else format_task_no_emoji

            if depth == 0:
                # Root level - no prefix
                lines.append(formatter(task_id))
            else:
                # Child level - show tree connector
                connector = "└── " if is_last else "├── "
                lines.append(prefix + connector + formatter(task_id))

            # Calculate prefix for children
            if depth == 0:
                child_prefix = ""
            else:
                child_prefix = prefix + ("    " if is_last else "│   ")

            for i, child_id in enumerate(task_children):
                is_last_child = (i == len(task_children) - 1)
                add_lines(child_id, child_prefix, is_last_child, depth + 1)

        for root_id in roots:
            add_lines(root_id)

        # Add any unvisited linked tasks (handles cycles)
        for task_id in sorted(linked_ids):
            if task_id not in visited:
                add_lines(task_id)

    # Add isolated tasks as plain list (standalone, get emoji)
    for tid in sorted(isolated_ids):
        lines.append(format_task(tid))

    return "\n".join(lines)


def _get_descendants(task_id: int, edges: list) -> set[int]:
    """Get all descendants of a task."""
    descendants: set[int] = set()
    stack = [task_id]
    while stack:
        current = stack.pop()
        for edge in edges:
            if edge.from_id == current and edge.to_id not in descendants:
                descendants.add(edge.to_id)
                stack.append(edge.to_id)
    return descendants


def render_dag(state: State) -> None:
    """Render tasks as trees grouped by state."""
    console = Console()

    if not state.tasks and not state.blocked:
        console.print("[dim]No tasks.[/dim]")
        return

    # Group tasks by state
    active_ids: set[int] = set()
    inactive_ids: set[int] = set()
    blocked_ids: set[int] = set()

    all_tasks: dict[int, Task] = {}
    blocked_tasks: dict[int, BlockedTask] = {}

    for tid, task in state.tasks.items():
        task_id = int(tid)
        all_tasks[task_id] = task
        if task.active:
            active_ids.add(task_id)
        else:
            inactive_ids.add(task_id)

    for blocked in state.blocked:
        blocked_ids.add(blocked.id)
        blocked_tasks[blocked.id] = blocked

    # Find inactive tasks that are descendants of active tasks (active workflow)
    active_workflow_ids: set[int] = set()
    for active_id in active_ids:
        descendants = _get_descendants(active_id, state.edges)
        for desc_id in descendants:
            if desc_id in inactive_ids:
                active_workflow_ids.add(desc_id)

    # Remove active workflow tasks from backlog
    backlog_ids = inactive_ids - active_workflow_ids

    # Combine active and active workflow for ACTIVE panel
    active_panel_ids = active_ids | active_workflow_ids

    # Render ON HOLD panel
    if blocked_ids:
        def format_blocked(tid: int) -> str:
            b = blocked_tasks[tid]
            return f"{bufo('hold')} [cyan][{tid}][/cyan] {b.title} [dim]({b.blocker})[/dim]"

        def format_blocked_no_emoji(tid: int) -> str:
            b = blocked_tasks[tid]
            return f"[cyan][{tid}][/cyan] {b.title} [dim]({b.blocker})[/dim]"

        content = _build_dag_content(blocked_ids, state.edges, format_blocked, format_blocked_no_emoji)
        if content:
            panel = Panel(content, title="[bold yellow]ON HOLD[/bold yellow]", border_style="yellow")
            console.print(panel)

    # Render BACKLOG panel (inactive tasks NOT in active workflow)
    if backlog_ids:
        def format_backlog(tid: int) -> str:
            task = all_tasks[tid]
            return f"{bufo('backlog')} [cyan][{tid}][/cyan] {task.title}"

        def format_backlog_no_emoji(tid: int) -> str:
            task = all_tasks[tid]
            return f"[cyan][{tid}][/cyan] {task.title}"

        content = _build_dag_content(backlog_ids, state.edges, format_backlog, format_backlog_no_emoji)
        if content:
            panel = Panel(content, title="[bold blue]BACKLOG[/bold blue]", border_style="blue")
            console.print(panel)

    # Render ACTIVE panel (active tasks + their inactive descendants dimmed)
    if active_panel_ids:
        def format_active(tid: int) -> str:
            task = all_tasks[tid]
            if tid in active_workflow_ids:
                # Dimmed - part of active workflow but waiting
                return f"[dim]{bufo('backlog')} [cyan][{tid}][/cyan] {task.title}[/dim]"
            return f"{bufo('active')} [cyan][{tid}][/cyan] {task.title}"

        def format_active_no_emoji(tid: int) -> str:
            task = all_tasks[tid]
            if tid in active_workflow_ids:
                return f"[dim][cyan][{tid}][/cyan] {task.title}[/dim]"
            return f"[cyan][{tid}][/cyan] {task.title}"

        content = _build_dag_content(active_panel_ids, state.edges, format_active, format_active_no_emoji)
        if content:
            panel = Panel(content, title="[bold green]ACTIVE[/bold green]", border_style="green")
            console.print(panel)


def render_blocked(blocked: list[BlockedTask]) -> None:
    """Render tasks on hold (called separately when no tasks exist)."""
    # Now handled in render_dag
    pass


def _build_dag_content_simple(
    task_ids: set[int],
    edges: list,
    format_task: callable,
    format_task_no_emoji: callable,
    c: type,
) -> list[str]:
    """Build tree content for a set of tasks using ANSI colors.

    Returns a list of lines with tree structure for linked tasks and plain list for isolated tasks.
    Root tasks and standalone tasks get emoji, child tasks don't.
    """
    if not task_ids:
        return []

    # Build adjacency maps for tasks in this set
    children: dict[int, list[int]] = {tid: [] for tid in task_ids}
    parents: dict[int, list[int]] = {tid: [] for tid in task_ids}

    for edge in edges:
        # Only include edges where both endpoints are in our set
        if edge.from_id in task_ids and edge.to_id in task_ids:
            children[edge.from_id].append(edge.to_id)
            parents[edge.to_id].append(edge.from_id)

    # Separate isolated tasks (no edges) from linked tasks
    isolated_ids = [tid for tid in task_ids if not children[tid] and not parents[tid]]
    linked_ids = task_ids - set(isolated_ids)

    lines: list[str] = []

    # Build tree for linked tasks using manual formatting
    if linked_ids:
        # Find root tasks (no parents within linked set)
        roots = [tid for tid in linked_ids if not parents.get(tid, [])]
        roots.sort()

        visited: set[int] = set()

        def add_lines(task_id: int, prefix: str = "", is_last: bool = True, depth: int = 0) -> None:
            if task_id in visited or depth > 10:
                return
            visited.add(task_id)

            task_children = sorted(children.get(task_id, []))

            # Root tasks (depth 0) get emoji, children don't
            formatter = format_task if depth == 0 else format_task_no_emoji

            if depth == 0:
                # Root level - no prefix
                lines.append(f"  {formatter(task_id)}")
            else:
                # Child level - show tree connector
                connector = "└── " if is_last else "├── "
                lines.append(f"  {prefix}{connector}{formatter(task_id)}")

            # Calculate prefix for children
            if depth == 0:
                child_prefix = ""
            else:
                child_prefix = prefix + ("    " if is_last else "│   ")

            for i, child_id in enumerate(task_children):
                is_last_child = i == len(task_children) - 1
                add_lines(child_id, child_prefix, is_last_child, depth + 1)

        for root_id in roots:
            add_lines(root_id)

        # Add any unvisited linked tasks (handles cycles)
        for task_id in sorted(linked_ids):
            if task_id not in visited:
                add_lines(task_id)

    # Add isolated tasks as plain list (standalone, get emoji)
    for tid in sorted(isolated_ids):
        lines.append(f"  {format_task(tid)}")

    return lines


def render_dag_simple(state: State) -> None:
    """Render tasks as simple text output with inline bufo images.

    This bypasses Rich panels to allow iTerm2 inline images to work.
    """
    if not state.tasks and not state.blocked:
        print("No tasks.")
        return

    # Group tasks by state
    active_ids: set[int] = set()
    inactive_ids: set[int] = set()
    blocked_ids: set[int] = set()

    all_tasks: dict[int, Task] = {}
    blocked_tasks: dict[int, BlockedTask] = {}

    for tid, task in state.tasks.items():
        task_id = int(tid)
        all_tasks[task_id] = task
        if task.active:
            active_ids.add(task_id)
        else:
            inactive_ids.add(task_id)

    for blocked in state.blocked:
        blocked_ids.add(blocked.id)
        blocked_tasks[blocked.id] = blocked

    # Find inactive tasks that are descendants of active tasks
    active_workflow_ids: set[int] = set()
    for active_id in active_ids:
        descendants = _get_descendants(active_id, state.edges)
        for desc_id in descendants:
            if desc_id in inactive_ids:
                active_workflow_ids.add(desc_id)

    backlog_ids = inactive_ids - active_workflow_ids
    active_panel_ids = active_ids | active_workflow_ids

    c = Colors

    # Render ACTIVE section
    if active_panel_ids:
        def format_active(tid: int) -> str:
            task = all_tasks[tid]
            if tid in active_workflow_ids:
                # Dimmed - part of active workflow but waiting
                return f"{c.DIM}{bufo('backlog')} {c.CYAN}[{tid}]{c.RESET}{c.DIM} {task.title}{c.RESET}"
            return f"{bufo('active')} {c.CYAN}[{tid}]{c.RESET} {task.title}"

        def format_active_no_emoji(tid: int) -> str:
            task = all_tasks[tid]
            if tid in active_workflow_ids:
                return f"{c.DIM}{c.CYAN}[{tid}]{c.RESET}{c.DIM} {task.title}{c.RESET}"
            return f"{c.CYAN}[{tid}]{c.RESET} {task.title}"

        print(f"\n{c.BOLD}{c.GREEN}── ACTIVE ──{c.RESET}")
        lines = _build_dag_content_simple(active_panel_ids, state.edges, format_active, format_active_no_emoji, c)
        for line in lines:
            sys.stdout.write(line + "\n")
        sys.stdout.flush()

    # Render ON HOLD section
    if blocked_ids:
        def format_blocked(tid: int) -> str:
            b = blocked_tasks[tid]
            return f"{bufo('hold')} {c.CYAN}[{tid}]{c.RESET} {b.title} {c.DIM}({b.blocker}){c.RESET}"

        def format_blocked_no_emoji(tid: int) -> str:
            b = blocked_tasks[tid]
            return f"{c.CYAN}[{tid}]{c.RESET} {b.title} {c.DIM}({b.blocker}){c.RESET}"

        print(f"\n{c.BOLD}{c.YELLOW}── ON HOLD ──{c.RESET}")
        lines = _build_dag_content_simple(blocked_ids, state.edges, format_blocked, format_blocked_no_emoji, c)
        for line in lines:
            sys.stdout.write(line + "\n")
        sys.stdout.flush()

    # Render BACKLOG section
    if backlog_ids:
        def format_backlog(tid: int) -> str:
            task = all_tasks[tid]
            return f"{bufo('backlog')} {c.CYAN}[{tid}]{c.RESET} {task.title}"

        def format_backlog_no_emoji(tid: int) -> str:
            task = all_tasks[tid]
            return f"{c.CYAN}[{tid}]{c.RESET} {task.title}"

        print(f"\n{c.BOLD}{c.BLUE}── BACKLOG ──{c.RESET}")
        lines = _build_dag_content_simple(backlog_ids, state.edges, format_backlog, format_backlog_no_emoji, c)
        for line in lines:
            sys.stdout.write(line + "\n")
        sys.stdout.flush()

    print()  # Final newline
