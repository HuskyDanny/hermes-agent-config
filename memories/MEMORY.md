*Curated learnings and context. Updated periodically.*
§
About Allen: Software engineer
§
About Allen: Timezone: Asia/Shanghai (GMT+8)
§
About Allen: Prefers depth, first-principles thinking, concrete examples
§
About Allen: No jargon without explanation
§
Key Events: **2026-03-18:** PR #4 merged on HuskyDanny/financial-agent (multiply function, closes #3). See `memory/2026-03-18.md`.
§
Memory Cleanup Log: **2026-03-20:** Deleted 20 obsolete memory files (boot loop artifacts, stale proxy debugging sessions from 9091 era, empty sessions, 164K raw transcript with binary audio). 2 files retained.
§
Telegram Setup (updated 2026-04-17):
- Bot token: TELEGRAM_BOT_TOKEN in .env (845120...HFXI)
- Home channel: 8201206139 (Allen's DM)
- Allowed users: 8201206139
- require_mention: false (group responds freely, no @mention needed)
- Gateway: running, Telegram: connected
§
Rules consolidation (2026-04-17): 41 rule files deleted, 9 consolidated into ~/.claude/rules/. 7 standalone files remain (claudemd-stays-neutral, demo-projects-stay-self-contained, lead-orchestrator-protocol, llm-judgment-over-keyword-matching, phrase-over-bag-of-tokens-for-containment, react-refresh-component-only-exports, template.md). CONSOLIDATION-2026-04-17.md log created. **Pending: create weekly cron job to re-run consolidation** (user asked for this, not yet done). Conflict resolution: later rule wins.

Rules directory before: 50+. After: 17 files.
§
Todoist CLI: "monday 9am" → parsed as next monday 9am correctly, due date stored as "2026-04-20T09:00:00". Works fine.

Allen: 驾照扣分 (driver's license point deduction) - needs someone else to deduct 6 points (代扣). Task created in Todoist for 2026-04-20 Monday 9am.

Allen sometimes says "sessionid" when meaning "Todoid task ID" - informal shorthand. He meant Todoist, not cronjob.
§
Hermes config bug (auxiliary_client.py line 2174): `provider: openai` with `base_url`/`api_key` in config.yaml is broken — credentials are silently discarded. Workaround: use native provider `kimi-coding-cn` + set `KIMI_CN_API_KEY` env var. Alternative: use `provider: custom` with `base_url` explicitly set (this path does pass api_key through).