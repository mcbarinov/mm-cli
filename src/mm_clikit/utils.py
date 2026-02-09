"""General CLI utilities."""

from typing import NoReturn

import typer


def fatal(message: str) -> NoReturn:
    """Print an error message and exit with code 1."""
    typer.echo(message)
    raise typer.Exit(1)
