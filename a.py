#!/usr/bin/env python3
"""
Simple local TODO CLI (no external dependencies).

Stores data in a JSON file under XDG data dir by default:
  $XDG_DATA_HOME/todo-cli/todos.json
or:
  ~/.local/share/todo-cli/todos.json

You can override storage location with: --data /path/to/todos.json
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


APP_NAME = "todo-cli"
DEFAULT_FILENAME = "todos.json"
VERSION = "0.1.0"


class TodoError(RuntimeError):
    pass


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat(timespec="seconds")


def _xdg_data_home() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg).expanduser()
    return Path.home() / ".local" / "share"


def default_data_path() -> Path:
    return _xdg_data_home() / APP_NAME / DEFAULT_FILENAME


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def atomic_write_text(path: Path, text: str) -> None:
    ensure_parent_dir(path)
    # Write to a temp file in the same directory for atomic replace semantics.
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as tf:
        tf.write(text)
        tf.flush()
        os.fsync(tf.fileno())
        tmp = Path(tf.name)
    os.replace(tmp, path)


def _coerce_path(p: str | None) -> Path:
    return Path(p).expanduser() if p else default_data_path()


def load_db(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "next_id": 1, "todos": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 (keep stdlib compatible)
        raise TodoError(f"Failed to read JSON from {path}") from e

    if not isinstance(data, dict):
        raise TodoError(f"Invalid DB format in {path}: expected object")
    if "todos" not in data:
        data["todos"] = []
    if "next_id" not in data:
        data["next_id"] = 1
    if "version" not in data:
        data["version"] = 1
    if not isinstance(data["todos"], list):
        raise TodoError(f"Invalid DB format in {path}: 'todos' must be a list")
    if not isinstance(data["next_id"], int):
        raise TodoError(f"Invalid DB format in {path}: 'next_id' must be an int")
    return data


def save_db(path: Path, db: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(db, indent=2, sort_keys=True) + "\n")


def _iter_todos(db: dict[str, Any]) -> Iterable[dict[str, Any]]:
    todos = db.get("todos", [])
    for t in todos:
        if isinstance(t, dict):
            yield t


def _find_by_id(db: dict[str, Any], todo_id: int) -> dict[str, Any]:
    for t in _iter_todos(db):
        if t.get("id") == todo_id:
            return t
    raise TodoError(f"No todo with id {todo_id}")


def add_todo(db: dict[str, Any], text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        raise TodoError("Todo text cannot be empty")

    todo_id = int(db.get("next_id", 1))
    db["next_id"] = todo_id + 1
    todo = {
        "id": todo_id,
        "text": text,
        "done": False,
        "created_at": _now_iso(),
        "done_at": None,
    }
    db.setdefault("todos", []).append(todo)
    return todo


def set_done(db: dict[str, Any], todo_id: int, done: bool) -> dict[str, Any]:
    t = _find_by_id(db, todo_id)
    t["done"] = bool(done)
    t["done_at"] = _now_iso() if t["done"] else None
    return t


def remove_todo(db: dict[str, Any], todo_id: int) -> dict[str, Any]:
    todos = db.setdefault("todos", [])
    for i, t in enumerate(list(todos)):
        if isinstance(t, dict) and t.get("id") == todo_id:
            return todos.pop(i)
    raise TodoError(f"No todo with id {todo_id}")


def clear_done(db: dict[str, Any]) -> int:
    todos = db.setdefault("todos", [])
    before = len(todos)
    db["todos"] = [t for t in todos if not (isinstance(t, dict) and t.get("done") is True)]
    return before - len(db["todos"])


def list_todos(
    db: dict[str, Any],
    *,
    show: str = "open",
) -> list[dict[str, Any]]:
    items = list(_iter_todos(db))
    if show == "all":
        return items
    if show == "done":
        return [t for t in items if t.get("done") is True]
    if show == "open":
        return [t for t in items if t.get("done") is not True]
    raise TodoError(f"Unknown show filter: {show}")


@dataclass(frozen=True)
class RenderOptions:
    json_output: bool = False


def render_todos(todos: list[dict[str, Any]], opts: RenderOptions) -> str:
    if opts.json_output:
        return json.dumps(todos, indent=2, sort_keys=True) + "\n"

    if not todos:
        return "No todos.\n"

    lines: list[str] = []
    for t in todos:
        done = "x" if t.get("done") else " "
        lines.append(f"[{done}] {t.get('id')}: {t.get('text')}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="todo", description="A tiny local TODO CLI.")
    p.add_argument("--data", help="Path to the JSON database file (overrides default).")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    sub = p.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Add a todo")
    p_add.add_argument("text", nargs="+", help="Todo text")

    p_list = sub.add_parser("list", help="List todos")
    g = p_list.add_mutually_exclusive_group()
    g.add_argument("--all", action="store_true", help="Show all todos")
    g.add_argument("--done", action="store_true", help="Show completed todos")
    g.add_argument("--open", action="store_true", help="Show open todos (default)")
    p_list.add_argument("--json", action="store_true", help="Output JSON")

    p_done = sub.add_parser("done", help="Mark todo as done")
    p_done.add_argument("id", type=int)

    p_undo = sub.add_parser("undo", help="Mark todo as not done")
    p_undo.add_argument("id", type=int)

    p_rm = sub.add_parser("rm", help="Remove a todo")
    p_rm.add_argument("id", type=int)

    sub.add_parser("clear-done", help="Remove all completed todos")

    return p


def run(argv: list[str], *, stdout: Any = None, stderr: Any = None) -> int:
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr
    p = build_parser()
    ns = p.parse_args(argv)

    data_path = _coerce_path(ns.data)
    try:
        db = load_db(data_path)

        if ns.cmd == "add":
            todo = add_todo(db, " ".join(ns.text))
            save_db(data_path, db)
            stdout.write(f"Added {todo['id']}: {todo['text']}\n")
            return 0

        if ns.cmd == "list":
            show = "open"
            if ns.all:
                show = "all"
            elif ns.done:
                show = "done"
            elif ns.open:
                show = "open"
            stdout.write(render_todos(list_todos(db, show=show), RenderOptions(json_output=ns.json)))
            return 0

        if ns.cmd == "done":
            todo = set_done(db, ns.id, True)
            save_db(data_path, db)
            stdout.write(f"Done {todo['id']}: {todo['text']}\n")
            return 0

        if ns.cmd == "undo":
            todo = set_done(db, ns.id, False)
            save_db(data_path, db)
            stdout.write(f"Undone {todo['id']}: {todo['text']}\n")
            return 0

        if ns.cmd == "rm":
            todo = remove_todo(db, ns.id)
            save_db(data_path, db)
            stdout.write(f"Removed {todo['id']}: {todo['text']}\n")
            return 0

        if ns.cmd == "clear-done":
            removed = clear_done(db)
            save_db(data_path, db)
            stdout.write(f"Removed {removed} completed todo(s).\n")
            return 0

        raise TodoError(f"Unknown command: {ns.cmd}")
    except TodoError as e:
        stderr.write(f"error: {e}\n")
        return 2


def main() -> int:
    return run(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
