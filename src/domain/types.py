from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class QueryResult:
    type: str
    key: str
    title: str
    data: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)
