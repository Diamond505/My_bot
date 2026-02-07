#!/usr/bin/env python3
"""Local task manager and file organizer."""
from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any
import builtins

APP_NAME = "MyBot"
DATA_DIR = Path("data")
TASKS_FILE = DATA_DIR / "tasks.json"
RULES_FILE = DATA_DIR / "rules.json"


@dataclass
class Task:
    id: int
    title: str
    details: str
    project: str
    status: str
    created_at: str
    completed_at: str | None


DEFAULT_RULES = {
    "rules": [
        {"name": "Images", "extensions": [".png", ".jpg", ".jpeg", ".gif"], "target": "Images"},
        {"name": "Design", "extensions": [".psd", ".ai", ".xd"], "target": "Design"},
        {"name": "Docs", "extensions": [".pdf", ".docx", ".txt"], "target": "Docs"},
        {"name": "Archives", "extensions": [".zip", ".rar", ".7z"], "target": "Archives"},
    ]
}


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(exist_ok=True)


def load_tasks() -> list[Task]:
    if not TASKS_FILE.exists():
        return []
    raw = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    return [Task(**item) for item in raw]


def save_tasks(tasks: list[Task]) -> None:
    TASKS_FILE.write_text(
        json.dumps([asdict(task) for task in tasks], indent=2),
        encoding="utf-8",
    )


def next_task_id(tasks: list[Task]) -> int:
    return max((task.id for task in tasks), default=0) + 1


def add_task(args: argparse.Namespace) -> None:
    tasks = load_tasks()
    task = Task(
        id=next_task_id(tasks),
        title=args.title,
        details=args.details or "",
        project=args.project or "General",
        status="open",
        created_at=datetime.utcnow().isoformat(),
        completed_at=None,
    )
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added task #{task.id}: {task.title}")


def list_tasks(args: argparse.Namespace) -> None:
    tasks = load_tasks()
    filtered = [task for task in tasks if args.status == "all" or task.status == args.status]
    if args.project:
        filtered = [task for task in filtered if task.project == args.project]

    if not filtered:
        print("No tasks found.")
        return

    for task in filtered:
        status_marker = "✓" if task.status == "done" else "·"
        details = f" - {task.details}" if task.details else ""
        print(f"{status_marker} #{task.id} [{task.project}] {task.title}{details}")


def complete_task(args: argparse.Namespace) -> None:
    tasks = load_tasks()
    target = next((task for task in tasks if task.id == args.id), None)
    if not target:
        print(f"Task #{args.id} not found.")
        return
    target.status = "done"
    target.completed_at = datetime.utcnow().isoformat()
    save_tasks(tasks)
    print(f"Completed task #{target.id}: {target.title}")


def ensure_rules() -> dict[str, Any]:
    if not RULES_FILE.exists():
        RULES_FILE.write_text(json.dumps(DEFAULT_RULES, indent=2), encoding="utf-8")
    return json.loads(RULES_FILE.read_text(encoding="utf-8"))


def organize_files(args: argparse.Namespace) -> None:
    rules = ensure_rules().get("rules", [])
    source = Path(args.source).expanduser().resolve()
    if not source.exists() or not source.is_dir():
        print(f"Source directory not found: {source}")
        return

    moves: list[tuple[Path, Path]] = []
    for item in source.iterdir():
        if item.is_dir():
            continue
        extension = item.suffix.lower()
        for rule in rules:
            if extension in rule.get("extensions", []):
                target_dir = source / rule.get("target", "Organized")
                target_dir.mkdir(exist_ok=True)
                moves.append((item, target_dir / item.name))
                break

    if not moves:
        print("No files matched the current rules.")
        return

    for src, dst in moves:
        if args.dry_run:
            print(f"Would move {src.name} -> {dst.parent.name}/")
        else:
            shutil.move(str(src), str(dst))
            print(f"Moved {src.name} -> {dst.parent.name}/")


def show_rules(_: argparse.Namespace) -> None:
    rules = ensure_rules()
    print(json.dumps(rules, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{APP_NAME}: local task manager and file organizer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add-task", help="Add a new task")
    add_parser.add_argument("title")
    add_parser.add_argument("--details")
    add_parser.add_argument("--project")
    add_parser.set_defaults(func=add_task)

    list_parser = subparsers.add_parser("list-tasks", help="List tasks")
    list_parser.add_argument("--status", choices=["all", "open", "done"], default="open")
    list_parser.add_argument("--project")
    list_parser.set_defaults(func=list_tasks)

    complete_parser = subparsers.add_parser("complete-task", help="Complete a task by id")
    complete_parser.add_argument("id", type=int)
    complete_parser.set_defaults(func=complete_task)

    organize_parser = subparsers.add_parser("organize", help="Organize files based on rules.json")
    organize_parser.add_argument("--source", required=True, help="Source directory to organize")
    organize_parser.add_argument("--dry-run", action="store_true", help="Preview changes without moving files")
    organize_parser.set_defaults(func=organize_files)

    rules_parser = subparsers.add_parser("show-rules", help="Show current file organization rules")
    rules_parser.set_defaults(func=show_rules)

    gui_parser = subparsers.add_parser("gui", help="Launch the desktop UI")
    gui_parser.set_defaults(func=launch_gui)

    return parser


def launch_gui(_: argparse.Namespace) -> None:
    import tkinter as tk
    from tkinter import messagebox, ttk

    ensure_data_dir()

    root = tk.Tk()
    root.title(f"{APP_NAME} - Local Task Manager")
    root.geometry("720x480")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    tasks_frame = ttk.Frame(notebook)
    organize_frame = ttk.Frame(notebook)
    notebook.add(tasks_frame, text="Tasks")
    notebook.add(organize_frame, text="Organize Files")

    tasks = load_tasks()

    def refresh_tasks() -> None:
        listbox.delete(0, tk.END)
        for task in load_tasks():
            status_marker = "✓" if task.status == "done" else "·"
            listbox.insert(tk.END, f"{status_marker} #{task.id} [{task.project}] {task.title}")

    def add_task_ui() -> None:
        title = title_entry.get().strip()
        if not title:
            messagebox.showwarning("Missing title", "Please enter a task title.")
            return
        details = details_entry.get().strip()
        project = project_entry.get().strip() or "General"
        add_task(argparse.Namespace(title=title, details=details, project=project))
        title_entry.delete(0, tk.END)
        details_entry.delete(0, tk.END)
        refresh_tasks()

    def complete_task_ui() -> None:
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("No selection", "Select a task to mark as complete.")
            return
        selected = listbox.get(selection[0])
        task_id = int(selected.split()[1].lstrip("#"))
        complete_task(argparse.Namespace(id=task_id))
        refresh_tasks()

    task_controls = ttk.Frame(tasks_frame)
    task_controls.pack(fill="x", pady=5)

    ttk.Label(task_controls, text="Title").grid(row=0, column=0, sticky="w")
    title_entry = ttk.Entry(task_controls, width=40)
    title_entry.grid(row=0, column=1, padx=5, sticky="we")

    ttk.Label(task_controls, text="Details").grid(row=1, column=0, sticky="w")
    details_entry = ttk.Entry(task_controls, width=40)
    details_entry.grid(row=1, column=1, padx=5, sticky="we")

    ttk.Label(task_controls, text="Project").grid(row=2, column=0, sticky="w")
    project_entry = ttk.Entry(task_controls, width=40)
    project_entry.grid(row=2, column=1, padx=5, sticky="we")

    add_button = ttk.Button(task_controls, text="Add Task", command=add_task_ui)
    add_button.grid(row=0, column=2, rowspan=2, padx=5, sticky="nsew")

    complete_button = ttk.Button(task_controls, text="Mark Complete", command=complete_task_ui)
    complete_button.grid(row=2, column=2, padx=5, sticky="nsew")

    task_controls.columnconfigure(1, weight=1)

    listbox = tk.Listbox(tasks_frame, height=12)
    listbox.pack(fill="both", expand=True, padx=5, pady=10)

    refresh_tasks()

    org_controls = ttk.Frame(organize_frame)
    org_controls.pack(fill="x", pady=10)

    ttk.Label(org_controls, text="Source Folder").grid(row=0, column=0, sticky="w")
    source_entry = ttk.Entry(org_controls, width=50)
    source_entry.grid(row=0, column=1, padx=5, sticky="we")

    dry_run_var = tk.BooleanVar(value=True)
    dry_run_check = ttk.Checkbutton(org_controls, text="Dry Run (preview only)", variable=dry_run_var)
    dry_run_check.grid(row=1, column=1, sticky="w", pady=5)

    output = tk.Text(organize_frame, height=12, state="disabled")
    output.pack(fill="both", expand=True, padx=5, pady=10)

    def run_organizer() -> None:
        source = source_entry.get().strip()
        if not source:
            messagebox.showwarning("Missing folder", "Please enter a folder path to organize.")
            return

        args = argparse.Namespace(source=source, dry_run=dry_run_var.get())
        output.configure(state="normal")
        output.delete("1.0", tk.END)

        def log_print(message: str) -> None:
            output.insert(tk.END, message + "\n")
            output.see(tk.END)

        original_print = builtins.print

        def patched_print(*values: Any, **kwargs: Any) -> None:
            log_print(" ".join(str(value) for value in values))

        builtins.print = patched_print
        try:
            organize_files(args)
        finally:
            builtins.print = original_print
            output.configure(state="disabled")

    org_controls.columnconfigure(1, weight=1)

    organize_button = ttk.Button(org_controls, text="Organize Files", command=run_organizer)
    organize_button.grid(row=0, column=2, rowspan=2, padx=5, sticky="nsew")

    root.mainloop()


def main() -> None:
    ensure_data_dir()
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
