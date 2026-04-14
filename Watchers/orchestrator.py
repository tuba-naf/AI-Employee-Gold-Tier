"""
Orchestrator — Gold Tier AI Employee
Manages Ralph Wiggum loop tasks. Creates or clears the state file that
ralph_wiggum_hook.py reads on each Claude Code Stop event.

Usage:
  # Start a Ralph loop task
  python orchestrator.py start \
      --task "process-inbox" \
      --prompt "Check /Needs_Action and process all pending drafts. Move each to /Done when verified." \
      --max-iterations 10 \
      --strategy file_movement \
      --done-file "process-inbox.md"

  # Mark current task as done (for promise strategy)
  python orchestrator.py complete

  # Cancel / reset (clears state, allows Claude to exit)
  python orchestrator.py reset

  # Check current loop status
  python orchestrator.py status
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

VAULT_PATH = Path(os.getenv("VAULT_PATH", "C:/Users/user/Gold Tier/Vault"))
STATE_FILE = VAULT_PATH / "In_Progress" / ".ralph_state.json"


def load_state() -> dict | None:
    if not STATE_FILE.exists():
        return None
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def cmd_start(args):
    existing = load_state()
    if existing and existing.get("status") == "active":
        print(f"[Ralph] WARNING: Active task '{existing['task_id']}' already running.")
        print(f"  Run 'orchestrator.py reset' to cancel it first.")
        sys.exit(1)

    state = {
        "task_id": args.task,
        "prompt": args.prompt,
        "max_iterations": args.max_iterations,
        "current_iteration": 0,
        "completion_strategy": args.strategy,
        "completion_promise": args.completion_promise,
        "done_file": args.done_file,
        "created": datetime.now().isoformat(),
        "status": "active",
    }
    save_state(state)
    print(f"[Ralph] Loop started: task='{args.task}', max_iterations={args.max_iterations}, strategy={args.strategy}")
    print(f"[Ralph] State file: {STATE_FILE}")
    print(f"[Ralph] Now run Claude Code — it will loop until the task is complete or {args.max_iterations} iterations.")


def cmd_complete(args):
    state = load_state()
    if not state:
        print("[Ralph] No active task found.")
        return
    state["status"] = "done"
    state["completed_at"] = datetime.now().isoformat()
    save_state(state)
    print(f"[Ralph] Task '{state['task_id']}' marked as done. Claude will exit on next stop.")


def cmd_reset(args):
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    print("[Ralph] State cleared. Claude will exit normally on next stop.")


def cmd_status(args):
    state = load_state()
    if not state:
        print("[Ralph] No active task. Claude will exit normally.")
        return
    print(json.dumps(state, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Ralph Wiggum Loop Orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    # start
    p_start = sub.add_parser("start", help="Start a Ralph loop task")
    p_start.add_argument("--task", required=True, help="Unique task name/ID")
    p_start.add_argument("--prompt", required=True, help="Prompt to re-inject on each iteration")
    p_start.add_argument("--max-iterations", type=int, default=10, help="Max loop iterations (default: 10)")
    p_start.add_argument("--strategy", choices=["file_movement", "promise"], default="promise",
                         help="Completion detection strategy (default: promise)")
    p_start.add_argument("--completion-promise", default="TASK_COMPLETE",
                         help="Promise string Claude outputs when done (promise strategy)")
    p_start.add_argument("--done-file", default="",
                         help="Filename to watch for in /Done/ (file_movement strategy)")
    p_start.set_defaults(func=cmd_start)

    # complete
    p_complete = sub.add_parser("complete", help="Mark current task as done")
    p_complete.set_defaults(func=cmd_complete)

    # reset
    p_reset = sub.add_parser("reset", help="Cancel/clear current task state")
    p_reset.set_defaults(func=cmd_reset)

    # status
    p_status = sub.add_parser("status", help="Print current loop state")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
