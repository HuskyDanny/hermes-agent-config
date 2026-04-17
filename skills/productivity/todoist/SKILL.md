---
name: todoist
description: Manage Todoist tasks, projects, and labels via the official CLI (td). Create tasks with natural language, list by project/date/priority, detect scheduling conflicts, and manage projects. Authenticated via system credential manager.
version: 1.0.0
author: Hermes Agent
license: MIT
prerequisites:
  commands: [node]
metadata:
  hermes:
    tags: [Todoist, Tasks, Productivity, CLI, Task Management]
---

# Todoist — Task & Project Management

Manage Todoist tasks and projects via the official `@doist/todoist-cli`. No API token in commands — authentication is stored in the system credential manager.

## CLI Binary

```bash
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js <command>
```

Always use the full `node /path/to/index.js` invocation — the `td` symlink may not be in PATH.

## Quick Add (Natural Language)

The fastest way to create a task. Parses project, date, priority, and labels from natural language:

```bash
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js add "Buy milk tomorrow p1 #Shopping"
```

Supports: dates ("tomorrow", "next Monday", "Apr 20"), priorities (p1-p4), projects (#ProjectName), labels (@label).

## Task Operations

### Create a task (structured)
```bash
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task add "Check server status" \
  --due "2026-04-17" \
  --priority p1 \
  --project "工作" \
  --description "Traffic anomaly detected last night" \
  --json
```

Options: `--due <date>`, `--deadline <date>`, `--priority <p1-p4>`, `--project <name>`, `--section <name>`, `--labels <a,b>`, `--parent <ref>`, `--description <text>`, `--duration <time>`, `--assignee <ref>`, `--json`

### List tasks
```bash
# All tasks in a project
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task list --project "工作" --json

# Tasks due on a specific date
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task list --due 2026-04-17 --json

# Filter by priority
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task list --priority p1 --json

# Raw Todoist filter query
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task list --filter "due before: Apr 20 & #工作" --json

# Limit results
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task list --limit 10 --json
```

### View a task
```bash
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task view "task name or id:xxx" --json
```

### Complete a task
```bash
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task complete "task name or id:xxx"
```

### Update a task
```bash
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task update "task name or id:xxx" \
  --due "next Monday" \
  --priority p2
```

### Reschedule a task
```bash
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task reschedule "task name" "tomorrow 3pm"
```

### Delete a task
```bash
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task delete "task name or id:xxx"
```

### Add subtasks
```bash
# First create the parent, capture its ID
PARENT_ID=$(node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task add "Check server" --project "工作" --due "2026-04-17" --json | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Then create subtasks under it
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task add "Check CPU usage" --parent "id:$PARENT_ID"
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task add "Check memory" --parent "id:$PARENT_ID"
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task add "Check error logs" --parent "id:$PARENT_ID"
```

## Project Operations

### List projects
```bash
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js project list --json
```

### Create a project
```bash
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js project create --name "AI 部署" --color blue --json
```

### View project details
```bash
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js project view "工作" --detailed
```

### Project progress
```bash
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js project progress "工作"
```

## Conflict Detection Pattern

Before adding a task, check for existing tasks on the same date:

```bash
# 1. List tasks due on the target date
EXISTING=$(node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js task list --due 2026-04-17 --json)

# 2. Parse and check for time conflicts
echo "$EXISTING" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tasks = data.get('results', [])
if tasks:
    print(f'Found {len(tasks)} task(s) on this date:')
    for t in tasks:
        due = t.get('due', {})
        time_str = due.get('datetime', 'no specific time') if due else 'no due'
        print(f'  - {t[\"content\"]} ({time_str})')
else:
    print('No conflicts found.')
"

# 3. If conflicts exist, suggest alternative time before creating
```

## Label Operations

```bash
# List labels
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js label list --json

# Create label
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js label create --name "urgent" --color red
```

## Completed Tasks

```bash
node /opt/homebrew/lib/node_modules/@doist/todoist-cli/dist/index.js completed --json
```

## Typical Workflow (Telegram → Hermes → Todoist)

1. **Parse intent:** Extract topic/project, task title, due date, priority, context from user message
2. **Check project exists:** `project list --json` — create if missing
3. **Conflict detection:** `task list --due <date> --json` — warn user if same-day tasks exist
4. **Create task:** `task add` with all extracted fields
5. **Add subtasks:** If task is complex, auto-decompose into 3-5 subtasks under the parent
6. **Confirm:** Report back what was created and any conflicts detected

## Important Notes

- Always use `--json` flag when parsing output programmatically
- The CLI handles authentication via system credential manager — no token needed in commands
- Natural language dates work in both `--due` and quick add: "tomorrow", "next Monday", "Apr 20 at 3pm"
- Priority levels: p1 (urgent/red), p2 (high/orange), p3 (medium/yellow), p4 (normal/no color)
- Existing projects: Inbox, Welcome, 生活, 工作, 学习
