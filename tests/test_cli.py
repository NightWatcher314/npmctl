from typer.testing import CliRunner

from npmctl.cli import app


def test_help():
    res = CliRunner().invoke(app, ["--help"])
    assert res.exit_code == 0
    assert "Nginx Proxy Manager CLI" in res.output


def test_missing_top_level_command_shows_help():
    res = CliRunner().invoke(app, [])
    assert res.exit_code == 0
    assert "Nginx Proxy Manager CLI" in res.output
    assert "Missing command" not in res.output


def test_missing_command_group_subcommand_shows_help():
    res = CliRunner().invoke(app, ["proxy"])
    assert res.exit_code == 0
    assert "Manage Proxy Hosts" in res.output
    assert "Missing command" not in res.output


def test_missing_nested_command_group_subcommand_shows_help():
    res = CliRunner().invoke(app, ["proxy", "location"])
    assert res.exit_code == 0
    assert "Manage custom locations" in res.output
    assert "Missing command" not in res.output
