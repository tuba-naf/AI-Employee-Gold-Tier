# Skill: Ralph Wiggum Loop

## Description
Start an autonomous multi-step task loop that keeps Claude working until completion.
Uses the Stop hook in `.claude/settings.json` to intercept Claude's exit and re-inject
the task prompt until the task is marked done or max iterations are reached.

## How It Works
1. User invokes `/ralph-loop "<task prompt>"` with options
2. Orchestrator writes a state file to `/Vault/In_Progress/.ralph_state.json`
3. Claude begins working on the task
4. When Claude tries to exit, the Stop hook (`ralph_wiggum_hook.py`) reads the state:
   - Task NOT done + iterations remaining → block exit, re-inject prompt
   - Task done OR max iterations → allow exit
5. Cycle repeats until complete

## Completion Strategies
- **promise** (simple): Claude outputs `<promise>TASK_COMPLETE</promise>` when done
- **file_movement** (reliable): Orchestrator watches for a specific file in `/Vault/Done/`

## Usage

When the user says `/ralph-loop "<task>" [options]`:

### Step 1 — Start the loop
```bash
cd "C:/Users/user/Gold Tier/Watchers"
python orchestrator.py start \
  --task "process-inbox" \
  --prompt "Check /Vault/Needs_Action/ and process all pending drafts. Verify facts, move verified ones to /Vault/Done/. Output <promise>TASK_COMPLETE</promise> when all files are processed." \
  --max-iterations 10 \
  --strategy promise
```

### Step 2 — Trigger Claude to work
Tell Claude: "Process all pending drafts in /Needs_Action/ following the workflow in Company_Handbook.md. When all are processed, output `<promise>TASK_COMPLETE</promise>`."

### Step 3 — Monitor
```bash
python orchestrator.py status
```

### Step 4 — If needed, cancel
```bash
python orchestrator.py reset
```

## Common Ralph Loop Tasks

### Process all inbox drafts
```bash
python orchestrator.py start \
  --task "process-all-drafts" \
  --prompt "Process every file in /Vault/Needs_Action/: verify facts via GPT-4o, update status, move verified to /Completed/. Output <promise>TASK_COMPLETE</promise> when done." \
  --max-iterations 15 \
  --strategy promise
```

### Run full content pipeline
```bash
python orchestrator.py start \
  --task "full-pipeline" \
  --prompt "Run the full Gold Tier content pipeline: 1) Generate new drafts for all platforms, 2) Verify all drafts, 3) Post approved Facebook drafts, 4) Send email digest for other platforms. Output <promise>TASK_COMPLETE</promise> when done." \
  --max-iterations 10 \
  --strategy promise
```

### Weekly CEO briefing
```bash
python orchestrator.py start \
  --task "ceo-briefing" \
  --prompt "Generate the weekly CEO briefing: read /Vault/Logs/, count posts per platform, read Odoo accounting summary, write /Vault/Briefings/<date>_CEO_Briefing.md. Output <promise>TASK_COMPLETE</promise> when done." \
  --max-iterations 5 \
  --strategy file_movement \
  --done-file "ceo-briefing.md"
```

## Important Rules
- Always check `orchestrator.py status` before starting a new loop — never run two loops simultaneously
- Set `--max-iterations` conservatively (5-15) to prevent runaway loops
- The Stop hook is always active when `.ralph_state.json` exists — call `orchestrator.py reset` to disable
- If Claude gets stuck, `orchestrator.py reset` immediately allows exit
- All loop iterations are logged to `/Vault/Logs/YYYY-MM-DD.json`
