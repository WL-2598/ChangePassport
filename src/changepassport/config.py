"""Load and validate the minimal JSON configuration used by the CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from changepassport.policy import KNOWN_REQUIREMENTS

MISSING = "missing"
UNKNOWN = "unknown"

DEFAULT_REQUIREMENTS = [
    "purpose",
    "external_ticket",
    "approval",
    "successful_checks",
    "deployment",
    "rollback_plan",
    "exception_disclosure",
]


class ConfigError(ValueError):
    """Raised when a configuration file is missing, malformed or unsupported."""


def default_config(
    owner: str = MISSING,
    name: str = MISSING,
    change: str = MISSING,
) -> dict[str, Any]:
    """Return a minimal config. Unsupplied facts are ``missing``, never guessed."""
    pull_request: int | str = MISSING
    commit_sha = MISSING
    if change.isdigit():
        pull_request = int(change)
    elif change != MISSING:
        commit_sha = change

    return {
        "version": 1,
        "repository": {
            "owner": owner,
            "name": name,
            "url": (
                f"https://github.com/{owner}/{name}"
                if owner != MISSING and name != MISSING
                else MISSING
            ),
        },
        "change": {"pull_request": pull_request, "commit_sha": commit_sha},
        "declared": {
            "purpose": MISSING,
            "external_ticket": {"reference": MISSING, "url": MISSING},
            "deployments": [],
            "rollbacks": [],
            "exceptions": [],
            "exceptions_reviewed": False,
            "rollback_plan": {"description": MISSING, "source_url": MISSING},
        },
        "policy": {"id": "default-v1", "require": list(DEFAULT_REQUIREMENTS)},
    }


def validate_config(raw: Any) -> dict[str, Any]:
    """Validate only the shape we consume; unknown keys are rejected as typos."""
    if not isinstance(raw, dict):
        raise ConfigError("configuration must be a JSON object")
    if raw.get("version") != 1:
        raise ConfigError("configuration 'version' must be 1")
    for key in ("repository", "change", "declared", "policy"):
        if not isinstance(raw.get(key), dict):
            raise ConfigError(f"configuration '{key}' must be an object")
    repository = raw["repository"]
    for key in ("owner", "name"):
        value = repository.get(key)
        if not isinstance(value, str) or not value:
            raise ConfigError(f"repository.{key} must be a non-empty string")
    change = raw["change"]
    pull_request = change.get("pull_request", MISSING)
    commit_sha = change.get("commit_sha", MISSING)
    if (
        not (isinstance(pull_request, int) and not isinstance(pull_request, bool))
        and pull_request != MISSING
    ):
        raise ConfigError("change.pull_request must be an integer or 'missing'")
    if not isinstance(commit_sha, str) or not commit_sha:
        raise ConfigError("change.commit_sha must be a non-empty string or 'missing'")
    if pull_request == MISSING and commit_sha == MISSING:
        raise ConfigError("set change.pull_request or change.commit_sha")

    declared = raw["declared"]
    for key in ("deployments", "rollbacks", "exceptions"):
        if declared.get(key) is None:
            declared[key] = []
        if not isinstance(declared[key], list):
            raise ConfigError(f"declared.{key} must be a list")
    if not isinstance(declared.get("exceptions_reviewed"), bool):
        raise ConfigError("declared.exceptions_reviewed must be a boolean")

    policy = raw["policy"]
    requirements = policy.get("require")
    if not isinstance(requirements, list) or not all(
        isinstance(item, str) for item in requirements
    ):
        raise ConfigError("policy.require must be a list of strings")
    unknown = sorted(set(requirements) - set(KNOWN_REQUIREMENTS))
    if unknown:
        raise ConfigError(f"unknown policy requirement(s): {', '.join(unknown)}")
    return raw


def load_config(path: Path) -> dict[str, Any]:
    """Read a JSON config file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"config not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON in {path}: {exc.msg}") from exc
    return validate_config(raw)


def write_config(config: dict[str, Any], path: Path, force: bool = False) -> None:
    """Write a config file without overwriting an existing one by default."""
    if path.exists() and not force:
        raise ConfigError(f"{path} already exists; use --force to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
