"""Schema, digest and deterministic policy verification."""

from __future__ import annotations

import hashlib
import json
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from changepassport import policy

DEFAULT_SCHEMA_PATH = Path("schemas/v1/passport.schema.json")


def load_schema(path: Path | None = None) -> dict[str, Any]:
    """Load the packaged schema by default; allow an explicit local override."""
    if path is not None:
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = json.loads(
            (resources.files("changepassport") / "schemas/v1/passport.schema.json").read_text(
                encoding="utf-8"
            )
        )
    if not isinstance(data, dict):
        raise ValueError("schema must be a JSON object")
    return data


def compute_digest(passport: dict[str, Any]) -> str:
    """SHA-256 of the canonical passport with the digest field blanked.

    This detects content changes only. It is not a signature, a tamper-proof
    record, or a trusted timestamp.
    """
    clone = json.loads(json.dumps(passport, ensure_ascii=False))
    clone["content_digest"] = {"algorithm": "sha256", "value": ""}
    canonical = json.dumps(clone, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_passport(
    passport: dict[str, Any],
    schema_path: Path | None = None,
) -> dict[str, Any]:
    """Return a structured report; verification never mutates the passport."""
    schema = load_schema(schema_path)
    validator = Draft202012Validator(schema)
    errors = [
        {
            "path": "/" + "/".join(str(part) for part in error.absolute_path),
            "message": error.message,
        }
        for error in validator.iter_errors(passport)
    ]
    declared_digest = passport.get("content_digest", {}).get("value")
    digest_matches = declared_digest == compute_digest(passport)
    requirements = passport.get("policy", {}).get("required", [])
    results = policy.evaluate(passport, requirements) if isinstance(requirements, list) else []
    gaps = [item for item in results if item["status"] == "gap"]
    status = "invalid" if errors or not digest_matches else ("gaps" if gaps else "pass")
    return {
        "status": status,
        "schema": {"valid": not errors, "errors": errors},
        "digest": {"algorithm": "sha256", "matches": digest_matches},
        "policy": {
            "id": passport.get("policy", {}).get("id", "unknown"),
            "results": results,
            "gaps": gaps,
        },
        "notice": "内容摘要只检测内容变化；不是签名、防篡改证明或可信时间戳，也不构成审计结论。",
    }
