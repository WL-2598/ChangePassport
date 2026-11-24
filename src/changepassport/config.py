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


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{label} must be an object")
    return value


def _keys(value: dict[str, Any], allowed: tuple[str, ...], label: str) -> None:
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise ConfigError(f"{label} has unknown key(s): {', '.join(unknown)}")


def _text_field(value: dict[str, Any], key: str, label: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ConfigError(f"{label}.{key} must be a non-empty string or 'missing'")
    return item


def _list_of_records(value: Any, label: str, fields: tuple[str, ...]) -> None:
    if not isinstance(value, list):
        raise ConfigError(f"{label} must be a list")
    for index, item in enumerate(value):
        record = _object(item, f"{label}[{index}]")
        _keys(record, fields, f"{label}[{index}]")
        for field in fields:
            _text_field(record, field, f"{label}[{index}]")


def validate_config(raw: Any) -> dict[str, Any]:
    """Validate the shape we consume; unknown keys are rejected as typos."""
    config = _object(raw, "configuration")
    _keys(
        config,
        ("version", "repository", "change", "declared", "policy"),
        "configuration",
    )
    if config.get("version") != 1:
        raise ConfigError("configuration 'version' must be 1")

    repository = _object(config.get("repository"), "repository")
    _keys(repository, ("owner", "name", "url"), "repository")
    for key in ("owner", "name", "url"):
        _text_field(repository, key, "repository")

    change = _object(config.get("change"), "change")
    _keys(change, ("pull_request", "commit_sha"), "change")
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

    declared = _object(config.get("declared"), "declared")
    _keys(
        declared,
        (
            "purpose",
            "external_ticket",
            "deployments",
            "rollbacks",
            "exceptions",
            "exceptions_reviewed",
            "rollback_plan",
        ),
        "declared",
    )
    _text_field(declared, "purpose", "declared")
    ticket = _object(declared.get("external_ticket"), "declared.external_ticket")
    _keys(ticket, ("reference", "url"), "declared.external_ticket")
    for key in ("reference", "url"):
        _text_field(ticket, key, "declared.external_ticket")
    plan = _object(declared.get("rollback_plan"), "declared.rollback_plan")
    _keys(plan, ("description", "source_url"), "declared.rollback_plan")
    for key in ("description", "source_url"):
        _text_field(plan, key, "declared.rollback_plan")
    _list_of_records(
        declared.get("deployments"),
        "declared.deployments",
        ("environment", "deployed_at", "actor", "status", "source_url"),
    )
    _list_of_records(
        declared.get("rollbacks"),
        "declared.rollbacks",
        ("environment", "rolled_back_at", "actor", "notes", "source_url"),
    )
    _list_of_records(
        declared.get("exceptions"),
        "declared.exceptions",
        ("type", "description", "approved_by", "source_url"),
    )
    if not isinstance(declared.get("exceptions_reviewed"), bool):
        raise ConfigError("declared.exceptions_reviewed must be a boolean")

    policy = _object(config.get("policy"), "policy")
    _keys(policy, ("id", "require"), "policy")
    _text_field(policy, "id", "policy")
    requirements = policy.get("require")
    if not isinstance(requirements, list) or not all(
        isinstance(item, str) for item in requirements
    ):
        raise ConfigError("policy.require must be a list of strings")
    unknown = sorted(set(requirements) - set(KNOWN_REQUIREMENTS))
    if unknown:
        raise ConfigError(f"unknown policy requirement(s): {', '.join(unknown)}")
    return config


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
