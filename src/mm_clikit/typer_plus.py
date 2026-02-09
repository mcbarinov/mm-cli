"""TyperPlus — Typer with command aliases and built-in --version support.

Provides ``TyperPlus``, a drop-in ``Typer`` replacement that adds:

* **Command aliases** — register short names via the ``aliases`` parameter::

      @app.command("deploy", aliases=["d"])
      def deploy_command(): ...

  In help output the command appears as ``deploy (d)``.

* **Automatic ``--version`` / ``-V``** — pass ``package_name`` at init
  and the flag is registered for you.

Note:
    If you register your own ``@app.callback()``, it replaces the
    auto-registered version callback.  In that case, add ``--version``
    manually via ``create_version_callback``.

"""

import importlib.metadata
from collections.abc import Callable, Sequence
from typing import Any

import click
import typer
from typer import Typer
from typer.core import TyperGroup

from .output import print_plain


def create_version_callback(package_name: str) -> Callable[[bool], None]:
    """Create a --version flag callback for a Typer CLI app.

    Args:
        package_name: The installed package name to look up the version for.

    """

    def version_callback(value: bool) -> None:
        """Print the version and exit when --version is passed."""
        if value:
            print_plain(f"{package_name}: {importlib.metadata.version(package_name)}")
            raise typer.Exit

    return version_callback


# Attribute name stored on command callbacks to carry alias info
_ALIASES_ATTR = "_typer_aliases"


class AliasGroup(TyperGroup):
    """TyperGroup subclass that supports command aliases with help display.

    Reads the aliases attribute from each command's callback during init,
    builds alias-to-canonical mappings, and patches help output so aliases
    appear next to their canonical command name (e.g. ``deploy (d)``).
    """

    def __init__(
        self,
        *,
        name: str | None = None,
        commands: dict[str, click.Command] | Sequence[click.Command] | None = None,
        **attrs: Any,  # noqa: ANN401 — must accept arbitrary kwargs from Typer internals
    ) -> None:
        """Scan commands for alias attributes and build alias mappings."""
        super().__init__(name=name, commands=commands, **attrs)

        # alias -> canonical name
        self._alias_to_cmd: dict[str, str] = {}
        # canonical name -> [aliases]
        self._cmd_aliases: dict[str, list[str]] = {}

        for cmd_name, cmd in list(self.commands.items()):
            callback = getattr(cmd, "callback", None)
            aliases: list[str] = getattr(callback, _ALIASES_ATTR, [])
            if not aliases:
                continue
            self._cmd_aliases[cmd_name] = list(aliases)
            for alias in aliases:
                self._alias_to_cmd[alias] = cmd_name
                self.commands[alias] = cmd

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Resolve alias to canonical command before lookup."""
        cmd_name = self._alias_to_cmd.get(cmd_name, cmd_name)
        return super().get_command(ctx, cmd_name)

    def list_commands(self, ctx: click.Context) -> list[str]:  # noqa: ARG002 — required by Click interface
        """Return canonical command names only, excluding aliases."""
        return [name for name in self.commands if name not in self._alias_to_cmd]

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Temporarily patch command names to include aliases for help display."""
        originals: dict[str, str] = {}
        for cmd_name, aliases in self._cmd_aliases.items():
            cmd = self.commands.get(cmd_name)
            if cmd and cmd.name:
                originals[cmd_name] = cmd.name
                alias_str = ", ".join(aliases)
                cmd.name = f"{cmd.name} ({alias_str})"
        try:
            super().format_help(ctx, formatter)
        finally:
            for cmd_name, original_name in originals.items():
                cmd = self.commands.get(cmd_name)
                if cmd:
                    cmd.name = original_name

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Non-Rich fallback: show aliases in parentheses next to command names."""
        rows: list[tuple[str, str]] = []
        for cmd_name in self.list_commands(ctx):
            cmd = self.commands.get(cmd_name)
            if cmd is None or cmd.hidden:
                continue
            help_text = cmd.get_short_help_str(limit=formatter.width)
            display_name = cmd_name
            if cmd_name in self._cmd_aliases:
                alias_str = ", ".join(self._cmd_aliases[cmd_name])
                display_name = f"{cmd_name} ({alias_str})"
            rows.append((display_name, help_text))

        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)


class TyperPlus(Typer):
    """Typer subclass with command aliases and built-in ``--version``.

    Args:
        package_name: If set, auto-registers a ``--version`` / ``-V`` callback
            that prints ``{package_name}: {version}`` and exits.
        **kwargs: Forwarded to ``Typer.__init__``.

    Note:
        Calling ``@app.callback()`` replaces the auto-registered version
        callback.  Use ``create_version_callback`` to re-add it manually.

    """

    def __init__(self, *, package_name: str | None = None, **kwargs: Any) -> None:  # noqa: ANN401 — must forward arbitrary kwargs to Typer
        """Set AliasGroup as default cls and optionally register --version."""
        kwargs.setdefault("cls", AliasGroup)
        super().__init__(**kwargs)

        if package_name:
            version_cb = create_version_callback(package_name)

            @self.callback()
            def _default_callback(
                _version: bool | None = typer.Option(None, "--version", "-V", callback=version_cb, is_eager=True),
            ) -> None:
                """Default callback with --version support."""

    def command(
        self,
        name: str | None = None,
        *,
        aliases: list[str] | None = None,
        **kwargs: Any,  # noqa: ANN401 — must forward arbitrary kwargs to Typer.command
    ) -> Callable[..., Any]:
        """Register a command with optional aliases."""
        decorator = super().command(name, **kwargs)

        if aliases is None:
            return decorator

        def wrapper(f: Callable[..., Any]) -> Callable[..., Any]:
            setattr(f, _ALIASES_ATTR, aliases)
            return decorator(f)

        return wrapper
