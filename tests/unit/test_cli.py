import json
from pathlib import Path

import pytest

from changepassport.cli import main
from changepassport.renderers import render_markdown

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_full_offline_cli_flow(tmp_path: Path, capsys) -> None:
    config = tmp_path / "changepassport.json"
    passport_path = tmp_path / "dist" / "passport.json"
    report_path = tmp_path / "dist" / "verify.json"
    markdown_path = tmp_path / "dist" / "passport.md"

    assert (
        main(
            [
                "init",
                "--output",
                str(config),
                "--owner",
                "example-org",
                "--name",
                "demo-service",
                "--change",
                "42",
            ]
        )
        == 0
    )
    assert json.loads(config.read_text(encoding="utf-8"))["change"]["pull_request"] == 42
    assert (
        main(["init", "--output", str(config), "--owner", "example-org", "--name", "demo-service"])
        == 2
    )
    assert (
        main(
            [
                "build",
                "--config",
                str(FIXTURES / "config.json"),
                "--snapshot",
                str(FIXTURES / "snapshot.json"),
                "--out",
                str(passport_path),
                "--generated-at",
                "2026-01-15T10:30:00Z",
            ]
        )
        == 0
    )
    assert "offline snapshot (no network)" in capsys.readouterr().out

    assert main(["verify", "--input", str(passport_path), "--out", str(report_path)]) == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert main(["render", "--input", str(passport_path), "--out", str(markdown_path)]) == 0
    assert "## 缺失与未知" in markdown_path.read_text(encoding="utf-8")


def test_verify_strict_exits_on_gaps(tmp_path: Path, capsys) -> None:
    passport_path = tmp_path / "passport.json"
    assert (
        main(
            [
                "build",
                "--config",
                str(FIXTURES / "config_missing.json"),
                "--snapshot",
                str(FIXTURES / "snapshot_missing.json"),
                "--out",
                str(passport_path),
                "--generated-at",
                "2026-01-15T10:30:00Z",
            ]
        )
        == 0
    )
    capsys.readouterr()  # discard build output
    assert main(["verify", "--input", str(passport_path)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "gaps"
    assert len(report["policy"]["gaps"]) == 7
    assert main(["verify", "--input", str(passport_path), "--strict"]) == 1


def test_render_does_not_require_network_or_recompute_facts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CHANGEPASSPORT_SHOULD_NOT_BE_USED", "1")
    passport = json.loads(
        (FIXTURES.parent.parent / "examples/basic/passport.json").read_text(encoding="utf-8")
    )
    rendered = render_markdown(passport)
    assert rendered.startswith("# 变更证据包 / Change Passport")
    assert passport["content_digest"]["value"] in rendered


def test_missing_input_reports_error_not_traceback(tmp_path: Path, capsys) -> None:
    assert main(["verify", "--input", str(tmp_path / "missing.json")]) == 2
    assert capsys.readouterr().err.startswith("error: file not found")


def test_build_cli_can_override_pr_and_rejects_bad_value(tmp_path: Path, capsys) -> None:
    out = tmp_path / "passport.json"
    assert (
        main(
            [
                "build",
                "--config",
                str(FIXTURES / "config.json"),
                "--snapshot",
                str(FIXTURES / "snapshot.json"),
                "--out",
                str(out),
                "--generated-at",
                "2026-01-15T10:30:00Z",
                "--pull-request",
                "99",
            ]
        )
        == 0
    )
    assert json.loads(out.read_text(encoding="utf-8"))["change"]["id"] == "PR #99"
    assert (
        main(
            [
                "build",
                "--config",
                str(FIXTURES / "config.json"),
                "--snapshot",
                str(FIXTURES / "snapshot.json"),
                "--out",
                str(out),
                "--pull-request",
                "not-a-number",
            ]
        )
        == 2
    )
    assert "must be an integer" in capsys.readouterr().err
