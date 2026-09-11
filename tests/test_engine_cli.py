"""Filesystem boundaries, weighted scoring and installed CLI integration."""

import json

import pytest
from typer.testing import CliRunner

from repopulse.checks import CHECKS
from repopulse.cli import app
from repopulse.config import Config, load_config
from repopulse.engine import scan
from repopulse.scanner import discover

runner = CliRunner()


def test_healthy_score(healthy):
    report = scan(healthy)
    assert report.score == 100
    assert report.passed == len(CHECKS)


def test_weighted_score(tmp_path):
    disabled = [c.id for c in CHECKS if c.id not in {"README", "SECRETS"}]
    report = scan(
        tmp_path,
        Config(disabled_checks=disabled, category_weights={"documentation": 3.0, "security": 1.0}),
    )
    assert report.score == 62.5


def test_disabled_category_renormalizes(tmp_path):
    config = Config(disabled_checks=[c.id for c in CHECKS if c.id != "README"])
    assert scan(tmp_path, config).score == 50


def test_unknown_check(tmp_path):
    with pytest.raises(ValueError, match="Unknown disabled"):
        scan(tmp_path, Config(disabled_checks=["TYPO"]))


def test_no_checks(tmp_path):
    with pytest.raises(ValueError, match="At least one"):
        scan(tmp_path, Config(disabled_checks=[c.id for c in CHECKS]))


@pytest.mark.parametrize(
    "settings",
    [
        {"max_file_bytes": 0},
        {"unknown": 2},
        {"category_weights": {"typo": 1}},
        {"category_weights": {"security": -1}},
    ],
)
def test_bad_config(settings):
    with pytest.raises(ValueError):
        Config(**settings)


def test_toml(tmp_path):
    (tmp_path / ".repopulse.toml").write_text(
        'disabled_checks = ["README"]\nfail_under = 75\n', encoding="utf-8"
    )
    assert load_config(tmp_path).fail_under == 75


def test_exclusions_and_binary(tmp_path):
    for directory in (".git", "node_modules", "venv", "build", "custom"):
        (tmp_path / directory).mkdir()
        (tmp_path / directory / "secret.py").write_text("hidden", encoding="utf-8")
    (tmp_path / "binary").write_bytes(b"abc\x00def")
    (tmp_path / "bad-encoding").write_bytes(b"\xff\xfe")
    (tmp_path / "ok.py").write_text("hello", encoding="utf-8")
    ctx = discover(tmp_path, Config(exclude_dirs=["custom"]))
    assert ctx.files == {"ok.py": "hello"} and ctx.skipped == 2


def test_size_limit(tmp_path):
    (tmp_path / "big.py").write_bytes(b"x" * 11)
    assert discover(tmp_path, Config(max_file_bytes=10)).skipped == 1


def test_worktree_git_pointer_not_read(tmp_path):
    (tmp_path / ".git").write_text("gitdir: /private/worktree", encoding="utf-8")
    ctx = discover(tmp_path, Config())
    assert not ctx.files and ctx.skipped == 1


def test_custom_named_virtualenv(tmp_path):
    (tmp_path / "python-env").mkdir()
    (tmp_path / "python-env/pyvenv.cfg").write_text("home=x", encoding="utf-8")
    assert not discover(tmp_path, Config()).files


def test_symlink_not_read(tmp_path):
    target = tmp_path / "real.py"
    target.write_text("hello", encoding="utf-8")
    try:
        (tmp_path / "link.py").symlink_to(target)
    except OSError:
        pytest.skip("Host does not permit symlink creation")
    assert "link.py" not in discover(tmp_path, Config()).files


def test_json_cli(healthy):
    result = runner.invoke(app, ["scan", str(healthy), "--format", "json"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["score"] == 100


def test_terminal_cli(healthy):
    result = runner.invoke(app, ["scan", str(healthy)])
    assert result.exit_code == 0 and "100.00/100" in result.output


def test_markdown_output(healthy, tmp_path):
    output = tmp_path / "report.md"
    result = runner.invoke(
        app, ["scan", str(healthy), "--format", "markdown", "--output", str(output)]
    )
    assert result.exit_code == 0
    assert output.read_text("utf-8").startswith("# RepoPulse report")


def test_threshold_failure(tmp_path):
    result = runner.invoke(app, ["scan", str(tmp_path), "--fail-under", "100"])
    assert result.exit_code == 1


def test_critical_failure_and_no_leak(healthy):
    token = "ghp_" + "aB34" * 9
    (healthy / "secret.txt").write_text(token, encoding="utf-8")
    for fmt in ("json", "terminal", "markdown"):
        result = runner.invoke(app, ["scan", str(healthy), "--format", fmt])
        assert result.exit_code == 1 and token not in result.output
        assert "REDACTED" in result.output


@pytest.mark.parametrize(
    "args",
    [
        ["scan", "absent-directory"],
        ["scan", "--format", "xml"],
        ["scan", "--fail-under", "101"],
        ["explain", "UNKNOWN"],
    ],
)
def test_launch_errors(args):
    assert runner.invoke(app, args).exit_code == 2


def test_invalid_config_no_value_leak(tmp_path):
    (tmp_path / ".repopulse.toml").write_text('fail_under = "confidential-value"', encoding="utf-8")
    result = runner.invoke(app, ["scan", str(tmp_path)])
    assert result.exit_code == 2 and "confidential-value" not in result.output


def test_threshold_override(healthy):
    (healthy / ".repopulse.toml").write_text(
        'fail_under = 100\ndisabled_checks = ["SECRETS"]', encoding="utf-8"
    )
    (healthy / "README.md").unlink()
    assert runner.invoke(app, ["scan", str(healthy)]).exit_code == 1
    assert runner.invoke(app, ["scan", str(healthy), "--fail-under", "0"]).exit_code == 0


def test_explain_and_registry():
    assert "Root README" in runner.invoke(app, ["explain", "readme"]).output
    result = runner.invoke(app, ["list-checks"])
    assert all(c.id in result.output for c in CHECKS)


def test_output_io_error(healthy):
    assert runner.invoke(app, ["scan", str(healthy), "--output", str(healthy)]).exit_code == 2


def test_terminal_legacy_encoding(tmp_path):
    import io

    from rich.console import Console

    from repopulse.render import terminal

    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="cp1251")
    (tmp_path / "測試.py").write_text("# TODO: add tests", encoding="utf-8")
    terminal(scan(tmp_path), Console(file=stream, force_terminal=False))
    stream.flush()
    assert b"RepoPulse" in raw.getvalue()
