"""Tests for TyperPlus and version callback."""

import click
import pytest
import typer
from typer.testing import CliRunner

import mm_clikit
from mm_clikit.typer_plus import AliasGroup

runner = CliRunner()


@pytest.fixture(scope="module")
def app() -> typer.Typer:
    """App with three commands: single-alias, multi-alias, no-alias."""
    _app = mm_clikit.TyperPlus()

    @_app.command("deploy", aliases=["d"])
    def deploy() -> None:
        """Deploy the application."""
        typer.echo("deployed")

    @_app.command("status", aliases=["st", "s"])
    def status() -> None:
        """Show current status."""
        typer.echo("status-ok")

    @_app.command("info")
    def info() -> None:
        """Show info."""
        typer.echo("info-ok")

    return _app


class TestCreateVersionCallback:
    """Tests for create_version_callback factory."""

    def test_returns_callable(self) -> None:
        """Returns a callable."""
        callback = mm_clikit.create_version_callback("mm-clikit")
        assert callable(callback)

    def test_no_op_when_false(self) -> None:
        """Does nothing when value is False."""
        callback = mm_clikit.create_version_callback("mm-clikit")
        callback(False)

    def test_exits_when_true(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Prints version and exits when value is True."""
        callback = mm_clikit.create_version_callback("mm-clikit")
        with pytest.raises(click.exceptions.Exit):
            callback(True)
        output = capsys.readouterr().out
        assert "mm-clikit:" in output

    def test_callback_works_with_typer_option(self) -> None:
        """Can be used as a Typer Option callback."""
        callback = mm_clikit.create_version_callback("mm-clikit")
        typer.Option(None, "--version", callback=callback, is_eager=True)


class TestCommandAliases:
    """Tests for command alias resolution via CliRunner."""

    def test_canonical_name(self, app: typer.Typer) -> None:
        """Canonical command name works."""
        result = runner.invoke(app, ["deploy"])
        assert result.exit_code == 0
        assert "deployed" in result.output

    def test_single_alias(self, app: typer.Typer) -> None:
        """Single alias resolves to canonical command."""
        result = runner.invoke(app, ["d"])
        assert result.exit_code == 0
        assert "deployed" in result.output

    @pytest.mark.parametrize("alias", ["st", "s"])
    def test_multi_alias(self, app: typer.Typer, alias: str) -> None:
        """Each alias of a multi-alias command resolves correctly."""
        result = runner.invoke(app, [alias])
        assert result.exit_code == 0
        assert "status-ok" in result.output

    def test_no_alias_command(self, app: typer.Typer) -> None:
        """Command without aliases works normally."""
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "info-ok" in result.output

    def test_unknown_command(self, app: typer.Typer) -> None:
        """Unknown command fails gracefully."""
        result = runner.invoke(app, ["nonexistent"])
        assert result.exit_code != 0

    def test_list_commands_excludes_aliases(self, app: typer.Typer) -> None:
        """list_commands returns only canonical names."""
        group: AliasGroup = typer.main.get_command(app)  # type: ignore[assignment]
        ctx = click.Context(group)
        names = group.list_commands(ctx)
        assert "deploy" in names
        assert "status" in names
        assert "info" in names
        assert "d" not in names
        assert "st" not in names
        assert "s" not in names


class TestHelpOutput:
    """Tests for alias display in help output."""

    def test_aliases_shown_in_help(self, app: typer.Typer) -> None:
        """Help output shows aliases in parentheses."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "deploy (d)" in result.output

    def test_multi_aliases_shown_in_help(self, app: typer.Typer) -> None:
        """Multi-alias command shows all aliases."""
        result = runner.invoke(app, ["--help"])
        assert "status (st, s)" in result.output

    def test_plain_command_no_parens(self, app: typer.Typer) -> None:
        """Non-aliased command appears without parentheses."""
        result = runner.invoke(app, ["--help"])
        # "info" must appear but not "info ("
        assert "info" in result.output
        assert "info (" not in result.output

    def test_names_restored_after_help(self, app: typer.Typer) -> None:
        """Command names are restored after help rendering."""
        group: AliasGroup = typer.main.get_command(app)  # type: ignore[assignment]
        deploy_cmd = group.commands["deploy"]
        original_name = deploy_cmd.name

        # Trigger help rendering
        runner.invoke(app, ["--help"])

        assert deploy_cmd.name == original_name

    def test_format_commands_shows_aliases(self, app: typer.Typer) -> None:
        """format_commands fallback renders aliases correctly."""
        group: AliasGroup = typer.main.get_command(app)  # type: ignore[assignment]
        ctx = click.Context(group)
        formatter = click.HelpFormatter()
        group.format_commands(ctx, formatter)
        output = formatter.getvalue()
        assert "deploy (d)" in output
        assert "status (st, s)" in output

    def test_format_commands_excludes_hidden(self) -> None:
        """Hidden commands are excluded from format_commands."""
        hidden_app = mm_clikit.TyperPlus()

        @hidden_app.command("visible")
        def visible() -> None:
            """Visible command."""
            typer.echo("visible")

        @hidden_app.command("secret", hidden=True)
        def secret() -> None:
            """Secret command."""
            typer.echo("secret")

        group: AliasGroup = typer.main.get_command(hidden_app)  # type: ignore[assignment]
        ctx = click.Context(group)
        formatter = click.HelpFormatter()
        group.format_commands(ctx, formatter)
        output = formatter.getvalue()
        assert "visible" in output
        assert "secret" not in output


class TestTyperPlusInit:
    """Tests for TyperPlus initialization."""

    def test_default_cls_is_alias_group(self) -> None:
        """Default cls is AliasGroup."""
        app = mm_clikit.TyperPlus()

        @app.command("one")
        def one() -> None:
            """First."""

        @app.command("two")
        def two() -> None:
            """Second."""

        group = typer.main.get_command(app)
        assert isinstance(group, AliasGroup)

    def test_version_flag(self) -> None:
        """--version works when package_name is provided."""
        app = mm_clikit.TyperPlus(package_name="mm-clikit")

        @app.command("noop")
        def noop() -> None:
            """No-op."""

        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "mm-clikit:" in result.output

    def test_version_short_flag(self) -> None:
        """-V works when package_name is provided."""
        app = mm_clikit.TyperPlus(package_name="mm-clikit")

        @app.command("noop")
        def noop() -> None:
            """No-op."""

        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert "mm-clikit:" in result.output

    def test_no_version_without_package_name(self) -> None:
        """--version is absent when package_name is not set."""
        app = mm_clikit.TyperPlus()

        @app.command("noop")
        def noop() -> None:
            """No-op."""

        result = runner.invoke(app, ["--version"])
        assert result.exit_code != 0


class TestCommandDecorator:
    """Tests for the command() decorator alias storage."""

    def test_aliases_stored_on_callback(self) -> None:
        """_typer_aliases is set on callback when aliases are provided."""
        app = mm_clikit.TyperPlus()

        @app.command("cmd", aliases=["c", "cm"])
        def cmd() -> None:
            """Command."""

        assert getattr(cmd, "_typer_aliases", None) == ["c", "cm"]

    def test_no_aliases_attr_without_param(self) -> None:
        """_typer_aliases is absent when aliases param is not passed."""
        app = mm_clikit.TyperPlus()

        @app.command("cmd")
        def cmd() -> None:
            """Command."""

        assert not hasattr(cmd, "_typer_aliases")

    def test_empty_aliases_list(self) -> None:
        """Empty aliases=[] stores empty list, treated as no aliases."""
        app = mm_clikit.TyperPlus()

        @app.command("cmd", aliases=[])
        def cmd() -> None:
            """Command."""

        assert getattr(cmd, "_typer_aliases", None) == []
