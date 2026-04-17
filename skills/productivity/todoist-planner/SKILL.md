---
name: todoist-planner
description: Smart Todoist task planner for Hermes. Parses natural-language Telegram messages (English + Chinese) into structured Todoist operations — adds/lists/completes/reschedules tasks, manages Topics (sections) within the 5 fixed projects, decomposes complex goals into subtasks, and detects scheduling conflicts with conversational escalation. Built on the low-level `todoist` skill.
version: 1.0.0
author: Hermes Agent
license: MIT
prerequisites:
  commands: [node]
metadata:
  hermes:
    tags: [Todoist, Task Management, Planning, Productivity, Telegram, Natural Language, Chinese]
---

# Todoist Planner — Smart Task Management

High-level planner that turns free-form user messages (typically from Telegram) into Todoist actions. Wraps the low-level [`todoist`](../todoist/SKILL.md) CLI skill with intent parsing, Topic management, subtask decomposition, conflict detection, and conversational escalation.

Use this skill whenever Hermes receives a message that could be a task, question about tasks, or edit to existing tasks — in English or Chinese.

---

## Overview

**When Hermes invokes this skill:**
- User sends a task-like message ("给生活/韩国游加个任务", "add a task to check server tomorrow")
- User asks about tasks ("what's on my plate today", "list work topics")
- User updates task state ("完成了订机票", "reschedule the CPU check")
- User wants goal decomposition ("help me plan the Korea trip")

**What it delivers:**
- Single Todoist operation when intent is clear and no conflicts exist (one-shot).
- Conversational confirmation when there's a conflict, ambiguity, destructive action, or a proposed subtask breakdown (escalation).

**Scope boundaries:**
- Projects are **fixed** (5 life-domain categories) — never create or delete projects.
- Sections = Topics, created on demand.
- No external storage; all state lives in Todoist.

---

## Preflight

Before any CLI call in a fresh shell, verify the Todoist CLI dependencies are installed. The initial `npm install -g @doist/todoist-cli` sometimes leaves the package's own `node_modules` incomplete, which makes every command fail with `ERR_MODULE_NOT_FOUND: Cannot find package 'commander'`.

```bash
TD_CLI="/opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js"
TD_PKG="/opt/homebrew/lib/node_modules/@doist/todoist-cli"

# Preflight: ensure commander is installed
ls "$TD_PKG/node_modules/commander" >/dev/null 2>&1 \
  || (cd "$TD_PKG" && npm install)

# Sanity check
node "$TD_CLI" --version
```

**Always use the full node path** — do not rely on a `td` alias being on PATH. Every example below uses `node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js` so it is copy-pasteable from any shell.

---

## Data Model

Todoist-native hierarchy — no external DB, no hardcoded IDs:

```
Project (5 fixed): 生活, 工作, 学习, Inbox, Welcome
  └─ Section (= Topic): 韩国游, 服务器部署, Moving, …
      └─ Task: 订机票
          ├─ due: 2026-04-20 (or datetime)
          ├─ priority: p1..p4
          ├─ description: context / why
          └─ Subtask: 比较航司
          └─ Subtask: 确认行李限制
```

Rules:
- **Projects are fixed.** The 5 projects (`生活`, `工作`, `学习`, `Inbox`, `Welcome`) are the only valid `--project` values. If the user mentions a project that isn't one of these, fall back to `Inbox` or ask which of the 5 to use. Never create a new project silently.
- **Sections are Topics.** Created on demand via `section create --project X --name Y`.
- **Tasks** belong to a Section within a Project. A task without a section is a "loose" task under the project.
- **Subtasks** are created with `--parent id:xxx`. Nesting is capped at 4 levels from root — deeper calls silently re-parent to the grandparent.

---

## Intent Parsing

From each user message, extract these fields. Defaults apply when the field is not mentioned.

| Field | Source | Default |
|-------|--------|---------|
| `project` | Explicit mention (`#生活`, `工作里`, "life:", "work:") or topic context | `Inbox` |
| `section` | Topic name (`/韩国游`, "韩国游 topic", "the server deploy topic") | none |
| `task` | Task title (imperative verb phrase) | required |
| `due` | Natural-language date/time (`下周`, `明天下午三点`, `tomorrow 3pm`, `next Friday`) | none |
| `priority` | Urgency words or explicit `p1..p4` | `p4` |
| `subtasks` | Auto-decompose if user asks for a plan or the task is complex | none |
| `context` | Why this task exists — raw phrasing or distilled summary | stored in `--description` |

### Priority word mapping

| Words (EN / 中文) | CLI priority | JSON `priority` (inverted) |
|-------------------|--------------|----------------------------|
| urgent, critical, ASAP / 紧急, 火烧眉毛 | `p1` | 4 |
| important, high / 比较重要, 重要 | `p2` | 3 |
| medium, soon / 一般, 稍后 | `p3` | 2 |
| (none) / default | `p4` | 1 |

> Note: CLI priority is inverted in JSON responses — `p1` (urgent) reads back as `priority: 4`. Normalize before displaying.

### Natural-language examples

1. **"给生活/韩国游加个任务，下周订机票，比较重要"**
   → `project=生活`, `section=韩国游`, `task=订机票`, `due="next week"`, `priority=p2`, `description="用户原话：...给生活/韩国游加个任务..."`.

2. **"工作里加个新topic叫服务器部署，明天下午三点检查CPU"**
   → `project=工作`, `section=服务器部署` (create if missing), `task=检查CPU`, `due="tomorrow 3pm"`, `priority=p4`, `description="新topic：服务器部署，明天 3pm 检查 CPU"`.

3. **"完成了订机票"**
   → `action=complete`, `task=订机票` (resolve via `task list` if ambiguous).

4. **"add a task to review PR #42 tomorrow morning, urgent"** (English)
   → `project=工作`, `section=none`, `task="Review PR #42"`, `due="tomorrow 9am"`, `priority=p1`.

5. **"plan the Korea trip — need flights, hotels, itinerary"**
   → `action=decompose`, `project=生活`, `section=韩国游`, `task=Plan Korea trip`, proposed subtasks: `订机票`, `订酒店`, `写行程`. **Conversational** — confirm the subtask list before creating.

### Context preservation

The raw user message (or a 1-line "why" distillation) always goes into `--description`. This preserves intent for future review and helps the agent answer "why is this task here?" later.

```bash
--description "Telegram 2026-04-17: 下周去首尔，需要先订机票比价"
```

---

## Section (Topic) Management

### Create-if-missing workflow

```bash
TD_CLI="/opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js"
PROJECT="生活"
TOPIC="韩国游"

# 1. Look up existing sections in the project.
#    NOTE: `project view --detailed` is currently broken (zod validation error
#    on collaborators). Use `section list --project X --json` instead.
EXISTING=$(node "$TD_CLI" section list --project "$PROJECT" --json)

# 2. Check whether the topic already exists.
HAS=$(echo "$EXISTING" | python3 -c "
import sys, json
data = json.load(sys.stdin)
sections = data.get('results', data) if isinstance(data, dict) else data
names = [s['name'] for s in sections]
print('yes' if '$TOPIC' in names else 'no')
")

# 3. Create if missing and capture the new section id.
if [ "$HAS" = "no" ]; then
  SECTION_JSON=$(node "$TD_CLI" section create --project "$PROJECT" --name "$TOPIC" --json)
  SECTION_ID=$(echo "$SECTION_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
  # Report back to the user
  echo "Created new topic '$TOPIC' under $PROJECT"
fi
```

### Other section commands

```bash
# Search within a project
node "$TD_CLI" section list --project "生活" --search "韩国" --json

# Rename
node "$TD_CLI" section update <section_id> --name "韩国自由行" --json

# Delete (fails if tasks remain in the section — move or delete tasks first)
node "$TD_CLI" section delete <section_id> --yes
```

> Always address sections by `--project X --name Y` (or by `<section_id>` captured from create). `project view --detailed` does NOT reliably enumerate sections — do not depend on it.

---

## Task Operations

All examples use the 5 fixed project names. Substitute as needed.

### Add a task (all fields)

```bash
TD_CLI="/opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js"

# Structured add — best for programmatic use. Capture the id from --json.
RESULT=$(node "$TD_CLI" task add "订机票" \
  --project "生活" \
  --section "韩国游" \
  --due "next week" \
  --priority p2 \
  --description "Telegram 2026-04-17: 下周去首尔，需要先订机票比价" \
  --json)

TASK_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Created task id:$TASK_ID"
```

Supported `task add` flags (verified): `--project`, `--section` (requires `--project`), `--due` (natural language OK), `--priority p1..p4`, `--description`, `--labels a,b,c`, `--parent id:xxx`, `--duration 30m|1h|1h30m`, `--assignee`, `--order N`, `--uncompletable`, `--dry-run`, `--json`.

**Do NOT use `--deadline`** — returns `403 AUTH_ERROR` on this account (likely a paid-plan feature).

### Quick add (natural-language one-liner)

When the user's message maps cleanly:

```bash
node "$TD_CLI" add "订机票 #生活 /韩国游 p1 next Friday 2pm" --json
```

- `#ProjectName` → project (Chinese OK)
- `/SectionName` → section (Chinese OK)
- `p1..p4` → priority
- `tomorrow 2pm`, `next Friday`, `Apr 20 at 3pm` → due
- `@label` is **NOT** parsed by quick add — add labels separately with `task update --labels a,b,c`.

### List tasks

```bash
# By due date
node "$TD_CLI" task list --due 2026-04-17 --json

# By project
node "$TD_CLI" task list --project "工作" --json

# By project + section (raw filter syntax — there is no --section on task list)
node "$TD_CLI" task list --filter "##生活 & /韩国游" --json

# Project + "today"
node "$TD_CLI" task list --filter "##生活 & today" --json

# Direct children of a specific parent (one level)
node "$TD_CLI" task list --parent "id:$PARENT_ID" --json

# Limit
node "$TD_CLI" task list --project "工作" --limit 10 --json
```

### View a task

```bash
node "$TD_CLI" task view "订机票" --json
# or by id (preferred when name may be ambiguous)
node "$TD_CLI" task view "id:$TASK_ID" --json
```

### Complete a task

```bash
# By name (fine if unique)
node "$TD_CLI" task complete "订机票"

# By id (recommended after creation to avoid AMBIGUOUS_TASK)
node "$TD_CLI" task complete "id:$TASK_ID"
```

> `task complete` does NOT support `--json`. It prints a human-readable `Completed: <name> (id:xxx)` line. Parse that string or just check the exit code.
>
> **Cascade warning:** Completing a parent task auto-completes ALL descendants (children, grandchildren, etc.). When the target task has subtasks, escalate to conversational mode and confirm with the user before completing.

### Reschedule (natural language — use `task update`, NOT `task reschedule`)

```bash
# WRONG — task reschedule only accepts YYYY-MM-DD / YYYY-MM-DDTHH:MM:SS
# node "$TD_CLI" task reschedule "订机票" "tomorrow 3pm"   # ← rejected

# CORRECT — task update accepts natural language in --due
node "$TD_CLI" task update "id:$TASK_ID" --due "tomorrow 3pm"
```

If you must use `task reschedule`, pre-format the date:

```bash
node "$TD_CLI" task reschedule "id:$TASK_ID" "2026-04-18T15:00:00"
```

> **Re-check conflicts at the new date before committing a reschedule.** Run the same time-overlap + capacity check described in [Conflict Detection](#conflict-detection) for the target datetime, exactly as you would for a new add. If new conflicts appear, escalate conversationally before updating.

### Delete (conversational — confirm first)

Delete is destructive. Always confirm with the user before executing, even if the intent looks clear.

```
User: "删除订机票"
Hermes: "确认删除『订机票』（生活/韩国游, 2026-04-20）吗？此操作不可恢复，子任务也会一并删除。"
User: "是的"
# → only THEN run:
```

```bash
node "$TD_CLI" task delete "id:$TASK_ID" --yes
```

> **Cascade warning:** Deleting a parent also deletes all descendants. Surface the descendant list in the confirmation prompt before proceeding.

---

## Subtask Decomposition

Create a parent task, capture its id from `--json`, then loop the subtasks with `--parent id:$PARENT_ID`.

```bash
TD_CLI="/opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js"

# 1. Create the parent task and capture its id
PARENT_JSON=$(node "$TD_CLI" task add "Plan Korea trip" \
  --project "生活" \
  --section "韩国游" \
  --due "next week" \
  --description "Decomposed from user message: plan the Korea trip" \
  --json)

PARENT_ID=$(echo "$PARENT_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Parent id:$PARENT_ID"

# 2. Create subtasks under it (always use id:PARENT_ID to avoid AMBIGUOUS_TASK)
for sub in "订机票" "订酒店" "写行程" "换韩元" "买旅游保险"; do
  node "$TD_CLI" task add "$sub" --parent "id:$PARENT_ID" --json
done
```

### Decomposition is conversational

Auto-decomposition (3–5 subtasks) is a **conversational** action: propose the breakdown first, get user confirmation, then create. Never generate subtasks silently.

```
Hermes: "帮你拆成 5 步可以吗？
  1. 订机票
  2. 订酒店
  3. 写行程
  4. 换韩元
  5. 买旅游保险
需要增减或调整顺序吗？"
```

Only after the user confirms (or edits the list) do you call `task add` per subtask.

### Depth cap

Subtasks are capped at **4 levels from the root**. Attempts to nest deeper silently re-parent to the grandparent — not an error, but unexpected. Keep decompositions shallow.

---

## Conflict Detection

Before creating or rescheduling a task, run two checks against the target date.

### Step 1 — Time overlap (1-hour granularity)

```bash
TD_CLI="/opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js"
TARGET_DATE="2026-04-20"
TARGET_TIME="15:00"   # 24h, empty if no specific time

EXISTING=$(node "$TD_CLI" task list --due "$TARGET_DATE" --json)

TD_JSON="$EXISTING" TARGET_DATE="$TARGET_DATE" TARGET_TIME="$TARGET_TIME" python3 <<'PY'
import os, sys, json
from datetime import datetime, timedelta

data = json.loads(os.environ['TD_JSON'])
tasks = data.get('results', data if isinstance(data, list) else [])
target_date = os.environ['TARGET_DATE']
target_time = os.environ.get('TARGET_TIME', '').strip()

def parse_due(task):
    """Handle both `due.date` shapes: local-naive ISO and UTC-Z."""
    due = task.get('due') or {}
    raw = due.get('datetime') or due.get('date')
    if not raw:
        return None
    # Normalize: strip trailing 'Z', parse as naive local
    raw = raw.rstrip('Z')
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None

if not target_time:
    # Day-level check only — surface all tasks on that date
    print(f"{len(tasks)} existing task(s) on {target_date}")
    for t in tasks:
        print(f"  - {t['content']}  due={t.get('due',{}).get('datetime') or t.get('due',{}).get('date')}")
    sys.exit(0)

target_dt = datetime.fromisoformat(f"{target_date}T{target_time}:00")
window_start = target_dt - timedelta(hours=1)
window_end   = target_dt + timedelta(hours=1)

overlaps = []
for t in tasks:
    dt = parse_due(t)
    if dt and window_start <= dt <= window_end:
        overlaps.append((t['content'], dt.isoformat()))

if overlaps:
    print(f"TIME OVERLAP on {target_date} near {target_time}:")
    for name, when in overlaps:
        print(f"  - {name} @ {when}")
else:
    print("No time overlap.")
PY
```

> **`due.date` has two shapes.** Structured `task add --due "tomorrow 3pm"` returns local-naive ISO (`2026-04-18T15:00:00`, no `Z`). Quick add (`td add "... tomorrow 2pm"`) returns UTC with a trailing `Z` plus a populated `timezone` field. The parser above strips the `Z` and treats both as naive — good enough for 1-hour overlap detection.

### Step 2 — Daily capacity (>= 5 tasks/day)

```bash
DAILY_CAPACITY=5   # tunable — see "Configurable thresholds" below

COUNT=$(node "$TD_CLI" task list --due "$TARGET_DATE" --json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('results', d if isinstance(d,list) else [])))")

if [ "$COUNT" -ge "$DAILY_CAPACITY" ]; then
  echo "DAILY CAPACITY EXCEEDED: $COUNT tasks already on $TARGET_DATE (limit $DAILY_CAPACITY)"
  # Suggest previous/next day — escalate conversationally
else
  echo "Capacity OK: $COUNT/$DAILY_CAPACITY tasks on $TARGET_DATE"
fi
```

### Step 3 — Decision branching

| Result | Action |
|--------|--------|
| No time overlap AND count < 5 | **One-shot**: create the task, report back. |
| Time overlap on target slot | **Conversational**: name the overlapping task(s), suggest adjacent slot, wait for user. |
| Count >= 5 on target date | **Conversational**: note overload, suggest previous/next day, wait for user. |

### Configurable thresholds

`daily_capacity` (default 5) and `time_granularity` (default 1 hour) are tunable — they live in the skill config, not hard-wired in the Python snippet. When the user says "bump my daily limit to 8", edit the config, not the script.

---

## Conversational Escalation Rules

Action → mode table (use this to decide one-shot vs. ask-first):

| Intent | One-shot? | Escalate when |
|--------|-----------|---------------|
| Add task (no conflict, clear project/section) | Yes | Time overlap OR day >= 5 tasks OR project ambiguous |
| Add subtasks (under confirmed parent) | Yes | — |
| List (by date / project / section) | Yes | — |
| Complete simple task (no subtasks) | Yes | Task has children (cascade), or name is ambiguous |
| Reschedule (no new conflict at target date) | Yes | New date has time overlap OR >= 5 tasks |
| Delete any task | No — always confirm | Always (destructive, cascades) |
| Decompose complex goal | No | Always — confirm subtask list first |

**The five escalation triggers:**
1. **Date conflict** — same or overlapping time slot on the target date.
2. **Day overloaded** — >= 5 existing tasks on the target date.
3. **Ambiguous project or section** — user said "服务器部署" but no such section exists in any of the 5 projects (ask which project).
4. **Complex decomposition** — user asks for a plan; confirm the proposed 3–5 subtasks before creating.
5. **Destructive action** — delete, or complete-with-cascade on a parent that has subtasks.

When escalating, state the conflict, propose an alternative, and wait for user confirmation before calling any CLI write command.

---

## Project Overview

To answer "what's on my plate for 生活?" or "list all topics under 工作":

```bash
TD_CLI="/opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js"
PROJECT="工作"

# 1. List all topics (sections) in the project
node "$TD_CLI" section list --project "$PROJECT" --json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); s=d.get('results', d if isinstance(d,list) else []); print('Topics:', [x['name'] for x in s])"

# 2. List all open tasks in the project
node "$TD_CLI" task list --project "$PROJECT" --json \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
tasks = d.get('results', d if isinstance(d, list) else [])
for t in tasks:
    due = (t.get('due') or {}).get('date', '—')
    pri = t.get('priority', 1)  # JSON priority: 4=urgent, 1=normal (inverted vs CLI)
    cli_pri = {4:'p1',3:'p2',2:'p3',1:'p4'}.get(pri, 'p?')
    print(f'  [{cli_pri}] {t[\"content\"]} — due {due}')
"

# 3. Tasks in a specific topic
node "$TD_CLI" task list --filter "##$PROJECT & /韩国游" --json
```

Present back to the user grouped by topic (section) with due date and CLI-style priority.

---

## Typical Workflow (Telegram → Hermes → Todoist)

End-to-end example. User sends the Telegram message:

> "给生活/韩国游加个任务，下周订机票，比较重要"

**Step 1 — Parse intent.**
`project=生活`, `section=韩国游`, `task=订机票`, `due="next week"`, `priority=p2`, `description="Telegram 2026-04-17: 下周订机票 比较重要"`.

**Step 2 — Ensure the topic exists.**
```bash
TD_CLI="/opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js"
node "$TD_CLI" section list --project "生活" --json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); s=d.get('results', d if isinstance(d,list) else []); print('yes' if '韩国游' in [x['name'] for x in s] else 'no')"
# If 'no' → section create --project "生活" --name "韩国游" --json
```

**Step 3 — Conflict check.**
```bash
# "next week" resolves to e.g. 2026-04-24. Check that date.
node "$TD_CLI" task list --due "2026-04-24" --json
# Run the Python time-overlap + capacity checks from the Conflict Detection section.
```

If no conflicts → proceed to Step 4. Otherwise → reply with conflicts and wait.

**Step 4 — Create the task.**
```bash
RESULT=$(node "$TD_CLI" task add "订机票" \
  --project "生活" \
  --section "韩国游" \
  --due "next week" \
  --priority p2 \
  --description "Telegram 2026-04-17: 下周订机票 比较重要" \
  --json)
TASK_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

**Step 5 — Confirm back to the user.**
> "已加到 生活/韩国游：『订机票』 (p2, 2026-04-24)。还需要拆成子任务（订机票/订酒店/写行程）吗？"

If the user says yes → switch to the Subtask Decomposition flow (conversational, confirm the list, then create).

---

## Error Handling

### Project not one of the 5 fixed projects
Never create a new project silently. Options:
1. Fall back to `Inbox` with a note in the description: `"Original target: '家庭财务' — not a fixed project, placed in Inbox"`, OR
2. Ask the user: "『家庭财务』不是固定项目之一（生活/工作/学习/Inbox/Welcome）。放哪个项目下？"

### Section not found
Create it via `section create --project X --name Y --json`, report back to the user: **"Created new topic 'X' under Y"**. No error — this is expected create-if-missing behavior.

### Ambiguous task name on complete/reschedule/delete
CLI returns `AMBIGUOUS_TASK` with candidate ids in `hints[]`. Disambiguate conversationally:
```
Hermes: "『订机票』匹配 2 个任务：
  1. 订机票 — 生活/韩国游, 2026-04-24
  2. 订机票 — 生活/日本游, 2026-05-02
要操作哪一个？"
```
After the user picks one, use `id:$CHOSEN_ID` for the write — never re-run with the ambiguous name.

### CLI error propagation
If `node $TD_CLI ...` exits non-zero, surface the stderr (or the JSON `error.message`) verbatim to the user. Do NOT swallow errors or retry blindly. The user needs to see what Todoist said — "403 AUTH_ERROR on --deadline", "SECTION_NOT_FOUND", etc. — to decide next steps.

---

## Known Caveats (Validation Findings)

These are the verified quirks of `@doist/todoist-cli` v1.47.0 as of 2026-04-17. Design the skill around them.

1. **`project view --detailed` is broken.** Zod validation error on the `collaborators` field. **Use `section list --project X --json`** to enumerate sections.

2. **`task reschedule` rejects natural language.** Only `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`, and requires an existing due date. **For NL rescheduling, use `task update --due "tomorrow 3pm"` instead.**

3. **`--deadline` returns 403 AUTH_ERROR.** Likely paid-plan only. **Do NOT use.**

4. **`@label` is NOT parsed in quick add.** `td add "buy milk @urgent"` keeps `@urgent` as literal text in `content`. Use `task add --labels a,b,c` or follow up with `task update --labels`.

5. **Priority inversion in JSON.** CLI `p1` (urgent) = JSON `priority: 4`; CLI `p4` (default) = JSON `priority: 1`. Normalize when reading JSON back.

6. **Parent complete/delete CASCADES to ALL descendants.** Completing a parent auto-completes every child and grandchild; deleting a parent deletes them all. Planner MUST warn the user before acting on a parent with subtasks.

7. **Subtask nesting cap = 4 levels from root.** Deeper attempts silently re-parent to the grandparent (no error). Keep decompositions shallow.

8. **`task complete` does NOT support `--json`.** Only prints human-readable `Completed: <name> (id:xxx)`. Parse that string or check exit code.

9. **Always use `id:xxx` after creation** for subsequent writes. Name-based writes risk `AMBIGUOUS_TASK` when duplicates exist. Capture `id` from the `--json` response on create, use `id:$CAPTURED_ID` from then on.

10. **Two `due.date` shapes.** Structured `task add --due "..."` returns local-naive ISO (`2026-04-18T15:00:00`, no `Z`). Quick add (`td add "... tomorrow 2pm"`) returns UTC with trailing `Z` and a populated `timezone` field. The conflict-detection parser handles both — any new code that reads `due.datetime` must too.

---

## Related Skills

- **[`todoist`](../todoist/SKILL.md)** — low-level CLI reference (every flag, every command). This planner calls into it.
- **`telegram`** — how Hermes receives the user message in the first place (if wired up via the Telegram skill).
