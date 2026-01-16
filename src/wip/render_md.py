"""Markdown rendering for shareable WIP view."""

from datetime import datetime, timedelta

from .model import BlockedTask, HistoryEntry, State, Task


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


def _get_week_tasks(history: list[HistoryEntry]) -> list[HistoryEntry]:
    """Get tasks completed this week."""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)

    return [entry for entry in history if entry.completed_datetime >= monday]


def _render_task_tree_md(
    task_ids: set[int],
    edges: list,
    format_task: callable,
    indent: str = "",
) -> list[str]:
    """Build markdown tree structure for tasks."""
    if not task_ids:
        return []

    children: dict[int, list[int]] = {tid: [] for tid in task_ids}
    parents: dict[int, list[int]] = {tid: [] for tid in task_ids}

    for edge in edges:
        if edge.from_id in task_ids and edge.to_id in task_ids:
            children[edge.from_id].append(edge.to_id)
            parents[edge.to_id].append(edge.from_id)

    isolated = [tid for tid in task_ids if not children[tid] and not parents[tid]]
    linked = task_ids - set(isolated)

    lines: list[str] = []

    if linked:
        roots = sorted([tid for tid in linked if not parents.get(tid, [])])
        visited: set[int] = set()

        def add_tree(task_id: int, depth: int = 0) -> None:
            if task_id in visited or depth > 10:
                return
            visited.add(task_id)

            prefix = "  " * depth + "- " if depth > 0 else "- "
            lines.append(prefix + format_task(task_id, depth == 0))

            for child_id in sorted(children.get(task_id, [])):
                add_tree(child_id, depth + 1)

        for root_id in roots:
            add_tree(root_id)

    for tid in sorted(isolated):
        lines.append("- " + format_task(tid, True))

    return lines


def render_state_md(state: State) -> str:
    """Render complete state as Markdown document."""
    now = datetime.now()

    # Categorize tasks
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

    # Find workflow tasks (inactive descendants of active)
    active_workflow_ids: set[int] = set()
    for active_id in active_ids:
        descendants = _get_descendants(active_id, state.edges)
        for desc_id in descendants:
            if desc_id in inactive_ids:
                active_workflow_ids.add(desc_id)

    backlog_ids = inactive_ids - active_workflow_ids
    active_panel_ids = active_ids | active_workflow_ids

    # Weekly progress
    week_tasks = _get_week_tasks(state.history)

    # Build markdown
    lines = ["# WIP Status", ""]

    # Active section
    if active_panel_ids:
        lines.append("## Top of Mind")
        lines.append("")

        def format_active(tid: int, is_root: bool) -> str:
            task = all_tasks[tid]
            if tid in active_ids:
                return f"**[{tid}] {task.title}**"
            return f"*[{tid}] {task.title}*"

        lines.extend(_render_task_tree_md(active_panel_ids, state.edges, format_active))
        lines.append("")

    # On Hold section
    if blocked_ids:
        lines.append("## On Hold")
        lines.append("")

        def format_blocked(tid: int, is_root: bool) -> str:
            b = blocked_tasks[tid]
            return f"[{tid}] {b.title} _{b.blocker}_"

        lines.extend(_render_task_tree_md(blocked_ids, state.edges, format_blocked))
        lines.append("")

    # Backlog section
    if backlog_ids:
        lines.append("## Backlog")
        lines.append("")

        def format_backlog(tid: int, is_root: bool) -> str:
            task = all_tasks[tid]
            return f"[{tid}] {task.title}"

        lines.extend(_render_task_tree_md(backlog_ids, state.edges, format_backlog))
        lines.append("")

    # Weekly progress section
    lines.append("## This Week")
    lines.append("")

    if week_tasks:
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        tasks_by_day: dict[int, list[str]] = {i: [] for i in range(5)}
        for entry in week_tasks:
            day_idx = entry.completed_datetime.weekday()
            if day_idx < 5:  # Only include weekdays
                tasks_by_day[day_idx].append(entry.title)

        weekday_count = sum(len(tasks_by_day[i]) for i in range(5))
        if weekday_count > 0:
            for day_idx in range(5):
                if tasks_by_day[day_idx]:
                    for title in tasks_by_day[day_idx]:
                        lines.append(f"- **{day_names[day_idx]}**: {title}")

            lines.append("")
            lines.append(f"*{weekday_count} completed*")
        else:
            lines.append("*No tasks completed on weekdays this week*")
    else:
        lines.append("*No tasks completed this week*")

    lines.append("")
    lines.append("---")
    lines.append(f"*Updated: {now.strftime('%Y-%m-%d %H:%M')}*")

    return "\n".join(lines)
