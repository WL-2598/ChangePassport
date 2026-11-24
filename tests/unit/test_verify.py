import json
from pathlib import Path

from jsonschema import Draft202012Validator

from changepassport.builder import build_passport
from changepassport.config import load_config
from changepassport.verify import compute_digest, load_schema, verify_passport

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"


def test_sample_passport_is_schema_valid() -> None:
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    sample = json.loads((ROOT / "examples/basic/passport.json").read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(schema).iter_errors(sample))


def test_packaged_schema_matches_repository_schema() -> None:
    packaged = (ROOT / "src/changepassport/schemas/v1/passport.schema.json").read_bytes()
    assert packaged == (ROOT / "schemas/v1/passport.schema.json").read_bytes()


def test_digest_detects_fact_change() -> None:
    passport = json.loads((ROOT / "examples/basic/passport.json").read_text(encoding="utf-8"))
    assert verify_passport(passport)["digest"]["matches"] is True
    tampered = json.loads(json.dumps(passport))
    tampered["change"]["purpose"] = "we changed this fact"
    assert verify_passport(tampered)["digest"]["matches"] is False
    assert compute_digest(tampered) != passport["content_digest"]["value"]


def test_schema_rejects_invalid_passport() -> None:
    passport = json.loads((ROOT / "examples/basic/passport.json").read_text(encoding="utf-8"))
    del passport["change"]["purpose"]
    passport["content_digest"]["value"] = compute_digest(passport)
    report = verify_passport(passport)
    assert report["status"] == "invalid"
    assert report["schema"]["valid"] is False
    assert any(error["path"] == "/change" for error in report["schema"]["errors"])


def test_two_same_inputs_produce_identical_digest() -> None:
    config = load_config(FIXTURES / "config.json")
    snapshot = json.loads((FIXTURES / "snapshot.json").read_text(encoding="utf-8"))
    first = build_passport(config, snapshot, "2026-01-15T10:30:00Z")
    second = build_passport(config, snapshot, "2026-01-15T10:30:00Z")
    assert first == second
    assert first["content_digest"]["value"] == second["content_digest"]["value"]
    assert isinstance(first["content_digest"]["value"], str)
    assert len(first["content_digest"]["value"]) == 64


def test_unknown_sentinel_is_preserved() -> None:
    config = load_config(FIXTURES / "config.json")
    snapshot = json.loads((FIXTURES / "snapshot.json").read_text(encoding="utf-8"))
    snapshot["pull_request"]["base"]["ref"] = "unknown"
    passport = build_passport(config, snapshot, "2026-01-15T10:30:00Z")
    assert passport["repository"]["default_branch"] == "unknown"
