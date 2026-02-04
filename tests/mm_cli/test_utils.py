"""Tests for general CLI utilities."""

import click
import pytest

import mm_cli


class TestFatal:
    """Tests for fatal function."""

    def test_exits_with_code_1(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Prints message and raises typer.Exit with code 1."""
        with pytest.raises(click.exceptions.Exit, match="1"):
            mm_cli.fatal("something went wrong")
        assert capsys.readouterr().out == "something went wrong\n"

    def test_empty_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Handles empty message string."""
        with pytest.raises(click.exceptions.Exit, match="1"):
            mm_cli.fatal("")
        assert capsys.readouterr().out == "\n"
