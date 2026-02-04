"""Output functions for formatted printing."""

from collections.abc import Callable, Mapping
from typing import Any

import rich
import tomlkit
from mm_std import json_dumps
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table


def print_plain(*messages: object) -> None:
    """Print to stdout without any formatting."""
    print(*messages)  # noqa: T201 - printing is the function's purpose


def print_json(data: object, type_handlers: dict[type[Any], Callable[[Any], Any]] | None = None) -> None:
    """Print object as formatted JSON."""
    rich.print_json(json_dumps(data, type_handlers=type_handlers))


def print_table(columns: list[str], rows: list[list[Any]], *, title: str | None = None) -> None:
    """Print data as a formatted table."""
    table = Table(*columns, title=title)
    for row in rows:
        table.add_row(*(str(cell) for cell in row))
    console = Console()
    console.print(table)


def print_toml(content: str | Mapping[str, Any], *, line_numbers: bool = False, theme: str = "monokai") -> None:
    """Print TOML with syntax highlighting.

    Args:
        content: TOML string or object to serialize to TOML.
        line_numbers: Whether to show line numbers.
        theme: Syntax highlighting theme.

    """
    toml_string = tomlkit.dumps(content) if isinstance(content, Mapping) else content

    console = Console()
    syntax = Syntax(toml_string, "toml", theme=theme, line_numbers=line_numbers)
    console.print(syntax)
