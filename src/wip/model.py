"""Data model classes for WIP task tracker."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Task:
    """A task in the task pool."""

    id: int
    title: str
    active: bool = False
    created_at: str = ""  # ISO format datetime string

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "active": self.active,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            active=data.get("active", False),
            created_at=data.get("created_at", ""),
        )

    @property
    def created_datetime(self) -> datetime | None:
        """Get created_at as datetime object."""
        if not self.created_at:
            return None
        return datetime.fromisoformat(self.created_at)


@dataclass
class Edge:
    """A dependency edge between tasks."""

    from_id: int
    to_id: int

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary for JSON serialization."""
        return {"from": self.from_id, "to": self.to_id}

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "Edge":
        """Create from dictionary."""
        return cls(from_id=data["from"], to_id=data["to"])


@dataclass
class BlockedTask:
    """A task blocked by an external dependency."""

    id: int
    title: str
    blocker: str
    created_at: str = ""  # ISO format datetime string

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "blocker": self.blocker,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlockedTask":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            blocker=data["blocker"],
            created_at=data.get("created_at", ""),
        )

    @property
    def created_datetime(self) -> datetime | None:
        """Get created_at as datetime object."""
        if not self.created_at:
            return None
        return datetime.fromisoformat(self.created_at)


@dataclass
class HistoryEntry:
    """A completed task in history."""

    id: int
    title: str
    completed_at: str  # ISO format datetime string
    created_at: str = ""  # ISO format datetime string

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "completed_at": self.completed_at,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistoryEntry":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            completed_at=data["completed_at"],
            created_at=data.get("created_at", ""),
        )

    @property
    def completed_datetime(self) -> datetime:
        """Parse completed_at as datetime."""
        return datetime.fromisoformat(self.completed_at)

    @property
    def created_datetime(self) -> datetime | None:
        """Parse created_at as datetime."""
        if not self.created_at:
            return None
        return datetime.fromisoformat(self.created_at)


@dataclass
class ShareConfig:
    """Sharing configuration for GitHub Gist."""

    enabled: bool = False
    gist_id: str | None = None
    gist_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "enabled": self.enabled,
            "gist_id": self.gist_id,
            "gist_url": self.gist_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ShareConfig":
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            gist_id=data.get("gist_id"),
            gist_url=data.get("gist_url"),
        )


@dataclass
class Config:
    """Configuration settings."""

    max_active: int = 2
    stale_days: int = 14
    share: ShareConfig = field(default_factory=ShareConfig)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "max_active": self.max_active,
            "stale_days": self.stale_days,
            "share": self.share.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create from dictionary."""
        return cls(
            max_active=data.get("max_active", 2),
            stale_days=data.get("stale_days", 14),
            share=ShareConfig.from_dict(data.get("share", {})),
        )


@dataclass
class State:
    """Complete application state."""

    tasks: dict[str, Task] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    blocked: list[BlockedTask] = field(default_factory=list)
    history: list[HistoryEntry] = field(default_factory=list)
    next_id: int = 1
    config: Config = field(default_factory=Config)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "edges": [e.to_dict() for e in self.edges],
            "blocked": [b.to_dict() for b in self.blocked],
            "history": [h.to_dict() for h in self.history],
            "next_id": self.next_id,
            "config": self.config.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "State":
        """Create from dictionary."""
        tasks = {k: Task.from_dict(v) for k, v in data.get("tasks", {}).items()}
        edges = [Edge.from_dict(e) for e in data.get("edges", [])]
        blocked = [BlockedTask.from_dict(b) for b in data.get("blocked", [])]
        history = [HistoryEntry.from_dict(h) for h in data.get("history", [])]
        next_id = data.get("next_id", 1)
        config = Config.from_dict(data.get("config", {}))
        return cls(
            tasks=tasks,
            edges=edges,
            blocked=blocked,
            history=history,
            next_id=next_id,
            config=config,
        )

    def get_task(self, task_id: int) -> Task | None:
        """Get a task by ID."""
        return self.tasks.get(str(task_id))

    def get_blocked(self, task_id: int) -> BlockedTask | None:
        """Get a blocked task by ID."""
        for b in self.blocked:
            if b.id == task_id:
                return b
        return None

    def active_count(self) -> int:
        """Count currently active tasks."""
        return sum(1 for t in self.tasks.values() if t.active)

    def has_edge(self, from_id: int, to_id: int) -> bool:
        """Check if an edge exists."""
        return any(e.from_id == from_id and e.to_id == to_id for e in self.edges)

    def get_edges_from(self, task_id: int) -> list[Edge]:
        """Get all edges starting from a task."""
        return [e for e in self.edges if e.from_id == task_id]

    def get_edges_to(self, task_id: int) -> list[Edge]:
        """Get all edges ending at a task."""
        return [e for e in self.edges if e.to_id == task_id]
