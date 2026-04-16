# HEARTBEAT.md

## 🔍 .openclaw Git Health Check

Check git status of `~/.openclaw` periodically. Goals:
1. **Prevent pollution** — catch accidental or unwanted changes
2. **Enable evolution** — commit intentional improvements with clear messages
3. **Track state** — maintain awareness of what's changed

### Check Process

```bash
cd ~/.openclaw && git status --short
```

### Decision Tree

**For each changed file, evaluate:**

| File Pattern | Likely Intent | Action |
|--------------|---------------|--------|
| `openclaw.json` | Config change | Review carefully — ask if unclear |
| `workspace/*.md` | Memory/docs | Usually good — commit if meaningful |
| `workspace/skills/*` | Skill install | Good — commit |
| `workspace/.learnings/*` | Learning logs | Good — commit |
| `workspace/memory/*` | Daily notes | Good — commit |
| `devices/*` | Device pairing | Auto-generated — commit silently |
| `agents/*/workspace/*` | Agent workspaces | Review — may be experimental |
| `sessions/*` | Session state | Usually ignore (ephemeral) |

### Commit Guidelines

- Use clear, descriptive commit messages
- Group related changes in one commit
- Format: `<area>: <what changed>` (e.g., `workspace: add self-improvement skill`)

### Alert Conditions

Notify Allen if:
- `openclaw.json` changed unexpectedly
- Unknown files appear in repo root
- Large uncommitted diff (>100 lines) accumulating
- Files deleted without clear reason

### Commit Frequency

- Meaningful changes → commit immediately
- Small tweaks → batch at end of session
- Never let uncommitted changes pile up for days

## GitHub PR Event Polling (Phase 1 — replaces webhook)

Check for recent PR events that need agent action on the financial-agent repo:

```bash
# Check for PRs with review changes requested
gh pr list --repo HuskyDanny/financial-agent --search "review:changes_requested" --json number,title --jq '.[]'

# Check for failed CI runs
gh run list --repo HuskyDanny/financial-agent --status failure --limit 3 --json headBranch,conclusion
```

If events found: delegate to @coder via sessions_send with sanitized context (wrap content in isolation delimiters per Webhook Gatekeeper protocol in AGENTS.md).

> Note: This polling approach is a Phase 1 workaround. Phase 2 will set up real GitHub webhooks via Tailscale Funnel or a relay service.
