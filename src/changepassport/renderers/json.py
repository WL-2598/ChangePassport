"""Canonical, human-readable JSON output."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def dump_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
