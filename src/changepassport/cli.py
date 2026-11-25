"""Command line interface: init, build, verify, render."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from changepassport import __version__
from changepassport.builder import build_passport
from changepassport.collectors.github import CollectorError, GitHubCollector, load_snapshot
from changepassport.config import MISSING, ConfigError, default_config, load_config, write_config
from changepassport.renderers import dump_json, render_markdown
from changepassport.verify import verify_passport


def _utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON in {path}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must contain a JSON object")
    return data


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="changepassport",
        description="Offline-friendly change evidence packets. No telemetry, no model calls.",
    )
    parser.add_argument("--version", action="version", version=f"changepassport {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="write a minimal JSON config")
    init_parser.add_argument("--output", default="changepassport.json", type=Path)
    init_parser.add_argument("--owner", default="missing")
    init_parser.add_argument("--name", default="missing")
    init_parser.add_argument("--change", default="missing", help="PR number or commit SHA")
    init_parser.add_argument("--force", action="store_true")

    build_parser = sub.add_parser("build", help="build a passport from GitHub or a snapshot")
    build_parser.add_argument("--config", default="changepassport.json", type=Path)
    build_parser.add_argument("--out", default="dist/passport.json", type=Path)
    build_parser.add_argument(
        "--snapshot", type=Path, help="offline JSON snapshot; disables network"
    )
    build_parser.add_argument(
        "--token-env", default="GITHUB_TOKEN", help="env var name, never a token value"
    )
    build_parser.add_argument("--generated-at", help="fixed ISO-8601 time for reproducible outputs")
    build_parser.add_argument("--pull-request", help="override config PR number")
    build_parser.add_argument("--commit-sha", help="override config commit SHA")

    verify_parser = sub.add_parser("verify", help="validate schema, digest and policy gaps")
    verify_parser.add_argument("--input", default="dist/passport.json", type=Path)
    verify_parser.add_argument("--schema", type=Path, help="override the packaged JSON Schema")
    verify_parser.add_argument("--out", type=Path, help="write the JSON verification report")
    verify_parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 on gaps/invalid (default: report-only, exit 0)",
    )

    render_parser = sub.add_parser("render", help="render Markdown from an existing passport")
    render_parser.add_argument("--input", default="dist/passport.json", type=Path)
    render_parser.add_argument("--out", default="dist/passport.md", type=Path)
    render_parser.add_argument(
        "--verification", type=Path, help="optional verification report to summarise"
    )
    return parser


def _cmd_init(args: argparse.Namespace) -> int:
    config = default_config(args.owner, args.name, args.change)
    write_config(config, args.output, args.force)
    print(f"Wrote {args.output}; all unconfigured facts remain 'missing'.")
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    if args.pull_request:
        if not args.pull_request.isdigit():
            raise ConfigError("--pull-request must be an integer")
        config["change"]["pull_request"] = int(args.pull_request)
        config["change"]["commit_sha"] = MISSING
    elif args.commit_sha:
        config["change"]["pull_request"] = MISSING
        config["change"]["commit_sha"] = args.commit_sha
    if args.snapshot is not None:
        snapshot = load_snapshot(args.snapshot)
        mode = "offline snapshot (no network)"
    else:
        token = os.environ.get(args.token_env)
        collector = GitHubCollector(token=token)
        snapshot = collector.collect(
            config["repository"]["owner"],
            config["repository"]["name"],
            config["change"].get("pull_request", "missing"),
            config["change"].get("commit_sha", "missing"),
        )
        mode = "GitHub API"
    passport = build_passport(config, snapshot, args.generated_at or _utcnow())
    dump_json(passport, args.out)
    print(
        f"Built {args.out} from {mode}: "
        f"{len(passport['approvals'])} approvals, {len(passport['checks'])} checks, "
        f"{len(passport['completeness']['missing'])} recorded gaps."
    )
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    passport = _read_json(args.input)
    report = verify_passport(passport, args.schema)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if args.strict and report["status"] != "pass":
        return 1
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    passport = _read_json(args.input)
    verification = _read_json(args.verification) if args.verification is not None else None
    text = render_markdown(passport, verification)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"Rendered {args.out}; no facts were re-fetched.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "init": _cmd_init,
        "build": _cmd_build,
        "verify": _cmd_verify,
        "render": _cmd_render,
    }
    try:
        return handlers[args.command](args)
    except (ConfigError, CollectorError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
