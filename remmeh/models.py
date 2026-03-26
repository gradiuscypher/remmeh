"""Data models for remmeh chat sessions and messages."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

MessageRole = Literal["user", "assistant", "error"]

_VALID_ROLES = {"user", "assistant", "error"}


@dataclass
class Message:
    """A single chat message with role, content, and metadata."""

    role: MessageRole
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    session_id: str = ""

    def __post_init__(self) -> None:
        """Validate role after construction."""
        if self.role not in _VALID_ROLES:
            raise ValueError(f"Invalid role {self.role!r}. Must be one of: {sorted(_VALID_ROLES)}")

    def to_dict(self) -> dict:
        """Serialize message to a dictionary with ISO 8601 timestamp."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Message:
        """Deserialize a message from a dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            id=data["id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            session_id=data.get("session_id", ""),
        )


@dataclass
class ChatSession:
    """A chat session containing a list of messages and session metadata."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Chat"
    model: str = "anthropic/claude-3.5-sonnet"
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, message: Message) -> None:
        """Append a message to the session and update updated_at."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Serialize session to a dictionary with all fields including messages."""
        return {
            "id": self.id,
            "name": self.name,
            "model": self.model,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ChatSession:
        """Deserialize a session from a dictionary, reconstructing Message objects."""
        messages = [Message.from_dict(m) for m in data.get("messages", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            model=data["model"],
            messages=messages,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
