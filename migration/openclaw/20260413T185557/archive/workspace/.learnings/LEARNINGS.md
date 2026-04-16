# Learnings

## [LRN-20260312-001] best_practice

**Logged**: 2026-03-12T10:55:00+08:00
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
ClawHub rate limits anonymous requests; logging in bypasses the limit.

### Details
When installing skills via `clawhub install`, anonymous requests are rate-limited aggressively. After multiple quick installs, subsequent requests fail with "Rate limit exceeded". The user resolved this by logging into ClawHub (`clawhub login`), which allows higher rate limits for authenticated users.

### Suggested Action
When hitting ClawHub rate limits, ask the user to run `clawhub login` before retrying.

### Metadata
- Source: error
- Tags: clawhub, rate-limit, skills
- Related Files: N/A

---

## [LRN-20260312-002] best_practice

**Logged**: 2026-03-12T10:55:00+08:00
**Priority**: high
**Status**: pending
**Area**: config

### Summary
API keys may be in environment variables, not just openclaw.json config.

### Details
When looking for Tavily API key, it wasn't in openclaw.json or skill config. Found it via `env | grep -i tavily`. The key was set as `TAVILY_API_KEY=...` in the shell environment.

For OpenClaw setups:
1. Check `skills.entries.<skill>.apiKey` in openclaw.json
2. Check environment variables: `env | grep -i <service_name>`
3. Check other agent directories (e.g., `/Users/allenpan/.openclaw/agents/<agent>/agent/`)
4. Check workspace skill folders (e.g., `/workspace/skills/<skill>/`)

### Suggested Action
When looking for API keys, check environment variables first (`env | grep -i <name>`), then config files.

### Metadata
- Source: conversation
- Tags: api-keys, config, environment
- Related Files: ~/.openclaw/openclaw.json

---
