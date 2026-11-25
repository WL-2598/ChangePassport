import json
from pathlib import Path

import pytest

from changepassport.cli import main
from changepassport.config import ConfigError, default_config, load_config, validate_config

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_default_config_uses_missing_sentinels() -> None:
    config = default_config("example-org", "demo-service", "42")
    assert config["change"]["pull_request"] == 42
    assert config["declared"]["purpose"] == "missing"
    assert config["declared"]["exceptions_reviewed"] is False


def test_init_cli_writes_reproducible_config(tmp_path: Path, capsys) -> None:
    target = tmp_path / "config.json"
    assert (
        main(
            [
                "init",
                "--output",
                str(target),
                "--owner",
                "example-org",
                "--name",
                "demo",
                "--change",
                "7",
            ]
        )
        == 0
    )
    assert json.loads(target.read_text(encoding="utf-8"))["change"]["pull_request"] == 7
    assert main(["init", "--output", str(target)]) == 2
    assert "already exists" in capsys.readouterr().err


def test_invalid_config_is_rejected() -> None:
    with pytest.raises(ConfigError, match="version"):
        validate_config({"version": 2})
    config = json.loads((FIXTURES / "config.json").read_text(encoding="utf-8"))
    config["policy"]["require"] = ["made_up_check"]
    with pytest.raises(ConfigError, match="unknown policy requirement"):
        validate_config(config)


def test_load_config_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="config not found"):
        load_config(tmp_path / "nope.json")


def test_unknown_config_keys_are_rejected() -> None:
    config = json.loads((FIXTURES / "config.json").read_text(encoding="utf-8"))
    config["surprise"] = "typo"
    with pytest.raises(ConfigError, match="unknown key"):
        validate_config(config)


def test_wrong_declared_types_are_rejected() -> None:
    config = json.loads((FIXTURES / "config.json").read_text(encoding="utf-8"))
    config["declared"]["purpose"] = 42
    with pytest.raises(ConfigError, match="purpose must be a non-empty string"):
        validate_config(config)


def test_malformed_deployment_record_is_rejected() -> None:
    config = json.loads((FIXTURES / "config.json").read_text(encoding="utf-8"))
    config["declared"]["deployments"] = [{"environment": "staging"}]
    with pytest.raises(ConfigError, match="deployed_at must be a non-empty string"):
        validate_config(config)


def test_valid_fixture_still_passes_strict_validation() -> None:
    assert load_config(FIXTURES / "config.json")["version"] == 1
