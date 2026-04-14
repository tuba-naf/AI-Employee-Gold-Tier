"""
Ralph Wiggum Stop Hook — Gold Tier AI Employee
Configured as a Claude Code Stop hook in .claude/settings.json.

When Claude tries to exit, this hook checks if there is an active Ralph loop task.
- If a task file exists in /Vault/In_Progress/ AND is NOT yet in /Vault/Done/:
    Block the stop and re-inject the task prompt so Claude continues working.
- If no active task or max iterations reached:
    Allow Claude to exit normally.

State file: Vault/In_Progress/.ralph_state.json
  {
    "task_id": "unique_task_name",
    "prompt": "The full task prompt to re-inject",
    "max_iterations": 10,
    "current_iteration": 2,
    "completion_strategy": "file_movement" | "promise",
    "completion_promise": "TASK_COMPLETE",   (for promise strategy)
    "done_file": "task_name.md",             (for file_movement strategy)
    "created": "ISO datetime",
    "status": "active"
  }

Stop hook JSON output (stdout) format understood by Claude Code:
  Allow exit:  {"continue": True}
  Block exit:  {"continue": False, "stopReason": "...", "systemMessage": "..."}
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

VAULT_PATH = Path(os.getenv("VAULT_PATH", "C:/Users/user/Gold Tier/Vault"))
STATE_FILE = VAULT_PATH / "In_Progress" / ".ralph_state.json"
DONE_DIR = VAULT_PATH / "Done"


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


def is_task_complete(state: dict) -> bool:
    strategy = state.get("completion_strategy", "promise")
    if strategy == "file_movement":
        done_file = state.get("done_file", "")
        if done_file and DONE_DIR.exists():
            return (DONE_DIR / done_file).exists()
        return False
    # Promise strategy: hook can't read Claude's output directly,
    # so we rely on the orchestrator setting status="done" in the state file.
    return state.get("status") == "done"


def log_iteration(state: dict, action: str):
    """Log Ralph Wiggum loop events to the daily audit log."""
    logs_dir = VAULT_PATH / "Logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    entries = []
    if log_file.exists():
        try:
            entries = json.loads(log_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            entries = []
    entries.append({
        "timestamp": datetime.now().isoformat(),
        "action_type": "ralph_wiggum_hook",
        "actor": "ralph_wiggum_hook",
        "target": state.get("task_id", "unknown"),
        "parameters": {
            "iteration": state.get("current_iteration"),
            "max_iterations": state.get("max_iterations"),
            "strategy": state.get("completion_strategy"),
        },
        "result": action,
    })
    try:
        log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    except OSError:
        pass


def main():
    state = load_state()

    # No active Ralph task — allow Claude to exit normally
    if state is None or state.get("status") not in ("active",):
        print(json.dumps({"continue": True}))
        return 0

    task_id = state.get("task_id", "unknown")
    current_iter = state.get("current_iteration", 0)
    max_iter = state.get("max_iterations", 10)
    prompt = state.get("prompt", "Continue working on the current task until complete.")

    # Check if task is done
    if is_task_complete(state):
        state["status"] = "done"
        state["completed_at"] = datetime.now().isoformat()
        save_state(state)
        log_iteration(state, "task_complete_allow_exit")
        print(json.dumps({"continue": True}))
        return 0

    # Max iterations reached — allow exit to prevent infinite loop
    if current_iter >= max_iter:
        state["status"] = "max_iterations_reached"
        save_state(state)
        log_iteration(state, "max_iterations_reached_allow_exit")
        print(json.dumps({"continue": True}))
        return 0

    # Task not done, iterations remaining — block exit and re-inject prompt
    state["current_iteration"] = current_iter + 1
    save_state(state)
    log_iteration(state, f"block_reinjecting_iteration_{current_iter + 1}")

    iteration_note = (
        f"\n\n[Ralph Wiggum Loop — Iteration {current_iter + 1}/{max_iter}]\n"
        f"Task '{task_id}' is not yet complete. Continue until done.\n"
    )

    print(json.dumps({
        "continue": False,
        "stopReason": f"Task '{task_id}' not complete. Iteration {current_iter + 1}/{max_iter}.",
        "systemMessage": prompt + iteration_note,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
