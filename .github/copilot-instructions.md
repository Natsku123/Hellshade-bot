# Repository Python workflow

Use the uv-managed virtual environment for all Python work in this repository.

## Rules
- Prefer `uv sync` to create or refresh the environment.
- Prefer `uv run <command>` for Python tools such as `python`, `ruff`, `ty`, and tests.
- Do not invoke bare `python`, `pip`, `ruff`, `ty`, or `.venv/bin/python` directly when a repo command can be expressed through `uv run`.
- Run commands from the repository root so uv resolves the project environment correctly.
- If the execution environment is sandboxed, uv-managed runs may fail because the sandbox blocks the virtualenv or cache paths; in that case, execute the command outside the sandbox.

## Examples
- `uv sync`
- `uv run python -m pytest`
- `uv run ruff check .`
- `uv run ty check .`
