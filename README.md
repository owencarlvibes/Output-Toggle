## What this repo contains

This repository contains a small, dependency-free Python CLI for managing a local TODO list stored in a JSON file.

## Quick start

Run it directly with Python:

```bash
python a.py --help
python a.py add "buy milk"
python a.py add "write report"
python a.py list
python a.py done 1
python a.py list --all
python a.py clear-done
```

## Storage location

By default it stores data at:

- **Linux XDG**: `$XDG_DATA_HOME/todo-cli/todos.json`
- **Fallback**: `~/.local/share/todo-cli/todos.json`

Override storage location (useful for scripts/tests):

```bash
python a.py --data /tmp/my-todos.json add "temp task"
python a.py --data /tmp/my-todos.json list --all
```

## Running tests

```bash
python -m unittest -v
```

