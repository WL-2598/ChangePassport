import json
from pathlib import Path

from changepassport.builder import build_passport
from changepassport.config import load_config
from changepassport.renderers import render_markdown
from changepassport.verify import verify_passport

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"
EXAMPLES = ROOT / "examples" / "basic"


def test_json_is_byte_stable_against_golden() -> None:
    config = load_config(FIXTURES / "config.json")
    snapshot = json.loads((FIXTURES / "snapshot.json").read_text(encoding="utf-8"))
    passport = build_passport(config, snapshot, "2026-01-15T10:30:00Z")
    expected = (EXAMPLES / "passport.json").read_text(encoding="utf-8")
    assert expected == json.dumps(passport, indent=2, ensure_ascii=False) + "\n"


def test_markdown_is_byte_stable_against_golden() -> None:
    passport = json.loads((EXAMPLES / "passport.json").read_text(encoding="utf-8"))
    assert (EXAMPLES / "passport.md").read_text(encoding="utf-8") == render_markdown(passport)


def test_golden_example_verifies_as_pass() -> None:
    passport = json.loads((EXAMPLES / "passport.json").read_text(encoding="utf-8"))
    report = verify_passport(passport)
    assert report["status"] == "pass"
    assert report["schema"]["valid"] is True
    assert report["digest"]["matches"] is True
