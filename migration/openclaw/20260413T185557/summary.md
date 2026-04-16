# OpenClaw -> Hermes Migration Report

- Timestamp: 20260413T185557
- Mode: execute
- Source: `/Users/allenpan/.openclaw`
- Target: `/Users/allenpan/.hermes`

## Summary

- migrated: 2
- archived: 17
- skipped: 26
- conflict: 5
- error: 0

## What Was Not Fully Brought Over

- `/Users/allenpan/.openclaw/workspace/AGENTS.md` -> `(n/a)`: No workspace target was provided
- `/Users/allenpan/.openclaw/workspace/MEMORY.md` -> `/Users/allenpan/.hermes/memories/MEMORY.md`: No new entries to import
- `/Users/allenpan/.openclaw/workspace/USER.md` -> `/Users/allenpan/.hermes/memories/USER.md`: No new entries to import
- `/Users/allenpan/.openclaw/openclaw.json` -> `/Users/allenpan/.hermes/.env`: No Hermes-compatible messaging settings found
- `/Users/allenpan/.openclaw/openclaw.json` -> `/Users/allenpan/.hermes/.env`: All env values already present
- `/Users/allenpan/.openclaw/openclaw.json` -> `/Users/allenpan/.hermes/.env`: No Discord settings found
- `/Users/allenpan/.openclaw/openclaw.json` -> `/Users/allenpan/.hermes/.env`: No Slack settings found
- `/Users/allenpan/.openclaw/openclaw.json` -> `/Users/allenpan/.hermes/.env`: No WhatsApp settings found
- `/Users/allenpan/.openclaw/openclaw.json` -> `/Users/allenpan/.hermes/.env`: No Signal settings found
- `/Users/allenpan/.openclaw/openclaw.json` -> `/Users/allenpan/.hermes/.env`: No provider API keys found
- `/Users/allenpan/.openclaw/openclaw.json` -> `/Users/allenpan/.hermes/config.yaml`: No TTS configuration found in OpenClaw config
- `/Users/allenpan/.openclaw/exec-approvals.json` -> `/Users/allenpan/.hermes/config.yaml`: All patterns already present
- `(n/a)` -> `/Users/allenpan/.hermes/skills/openclaw-imports`: No shared OpenClaw skills directories found
- `(n/a)` -> `/Users/allenpan/.hermes/tts`: Source directory not found
- `/Users/allenpan/.openclaw/openclaw.json` -> `(n/a)`: Selected Hermes-compatible values were extracted; raw OpenClaw config was not copied.
- `/Users/allenpan/.openclaw/memory/main.sqlite` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `/Users/allenpan/.openclaw/credentials` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `/Users/allenpan/.openclaw/devices` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `/Users/allenpan/.openclaw/identity` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `(n/a)` -> `(n/a)`: No MCP servers found in OpenClaw config
- `(n/a)` -> `(n/a)`: No model providers found
- `(n/a)` -> `(n/a)`: No browser configuration found
- `(n/a)` -> `(n/a)`: No approvals configuration found
- `(n/a)` -> `(n/a)`: No memory backend configuration found
- `(n/a)` -> `(n/a)`: No UI/identity configuration found
- `(n/a)` -> `(n/a)`: No logging/diagnostics configuration found
- `/Users/allenpan/.openclaw/workspace/SOUL.md` -> `/Users/allenpan/.hermes/SOUL.md`: Target exists and overwrite is disabled
- `/Users/allenpan/.openclaw/openclaw.json` -> `/Users/allenpan/.hermes/config.yaml`: Model already set and overwrite is disabled
- `/Users/allenpan/.openclaw/workspace/skills/china-holidays` -> `/Users/allenpan/.hermes/skills/openclaw-imports/china-holidays`: Destination skill already exists
- `/Users/allenpan/.openclaw/workspace/skills/self-improvement` -> `/Users/allenpan/.hermes/skills/openclaw-imports/self-improvement`: Destination skill already exists
- `gateway.auth.token` -> `.env HERMES_GATEWAY_TOKEN`: Env var HERMES_GATEWAY_TOKEN already set
