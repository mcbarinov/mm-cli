# mm-clikit

Shared CLI utilities on top of [Typer](https://typer.tiangolo.com/).

## Installation

```bash
uv add mm-clikit
```

## Usage

### TyperPlus

Drop-in `Typer` replacement with automatic `--version`/`-V` and command aliases.

```python
from mm_clikit import TyperPlus

app = TyperPlus(package_name="my-app")

@app.command("deploy", aliases=["d"])
def deploy():
    """Deploy the application."""
    ...
```

Running `my-app --version` prints `my-app: 0.1.0` and exits.
Running `my-app d` is equivalent to `my-app deploy`. Help output shows `deploy (d)`.

> **Note:** Registering a custom `@app.callback()` replaces the auto-registered version callback.
> Use `create_version_callback` to re-add `--version` manually.

### create_version_callback

Escape hatch for adding `--version` when you use a custom callback.

```python
from mm_clikit import TyperPlus, create_version_callback
import typer

app = TyperPlus()

@app.callback()
def main(
    _version: bool | None = typer.Option(
        None, "--version", "-V",
        callback=create_version_callback("my-app"),
        is_eager=True,
    ),
):
    """My CLI app."""
```

### fatal

Print a message to stdout and exit with code 1.

```python
from mm_clikit import fatal

fatal("something went wrong")
```

### Output functions

#### print_plain

Print to stdout without formatting.

```python
from mm_clikit import print_plain

print_plain("hello", "world")
```

#### print_json

Print an object as formatted JSON.

```python
from mm_clikit import print_json

print_json({"key": "value", "count": 42})
```

Custom type serialization via `type_handlers`:

```python
from datetime import datetime

print_json(
    {"ts": datetime.now()},
    type_handlers={datetime: lambda d: d.isoformat()},
)
```

#### print_table

Print a Rich table.

```python
from mm_clikit import print_table

print_table(
    columns=["Name", "Status"],
    rows=[["api", "running"], ["db", "stopped"]],
    title="Services",
)
```

#### print_toml

Print TOML with syntax highlighting.

```python
from mm_clikit import print_toml

# From a string
print_toml('[server]\nhost = "localhost"\nport = 8080')

# From a mapping
print_toml({"server": {"host": "localhost", "port": 8080}})

# With line numbers and a custom theme
print_toml({"debug": True}, line_numbers=True, theme="dracula")
```
