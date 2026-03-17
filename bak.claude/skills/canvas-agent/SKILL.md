---
name: canvas-agent
description: Join a canvas and actively analyze it — recognize entities, generate suggestions, report findings.
allowed-tools: [Read, Bash, Glob, Grep]
version: 1.0.0
---

# Canvas Agent Skill

Join a collaborative canvas session, analyze its contents using the suggestion engine, and report structured findings.

## Arguments

| Arg | Required | Default | Description |
|-----|----------|---------|-------------|
| `<canvas-id-or-name>` | yes | — | Canvas document ID (nanoid) or name to resolve |
| `--autonomy <0\|1\|2>` | no | `1` | Analysis autonomy level (0=report only, 1=suggest, 2=suggest+act) |
| `--approve` | no | `false` | Auto-approve suggestions with confidence >= 0.85 |

## Configuration

```
BASE_URL=http://127.0.0.1:42005
AGENT_NAME=canvas-agent
AGENT_COLOR=#6b7ff5
AUTO_APPROVE_THRESHOLD=0.85
```

## Workflow

### Step 1 — Resolve Canvas

Determine whether the argument is a nanoid (starts with alphanumeric, 21 chars) or a human name.

If it looks like a name, resolve it:

```bash
curl -sf "${BASE_URL}/api/canvas" | jq -r '.data[] | select(.name == "<ARG>") | .id'
```

If no match is found, **fail immediately** with:
```
STATUS: ERROR
Canvas not found: "<ARG>"
```

Store the resolved `CANVAS_ID` and `CANVAS_NAME` for subsequent steps.

### Step 2 — Join Presence

Announce the agent on the canvas:

```bash
curl -sf "${BASE_URL}/api/canvas/${CANVAS_ID}/presence/join" \
  -X POST -H 'Content-Type: application/json' \
  -d '{"agentName":"canvas-agent","agentColor":"#6b7ff5"}'
```

If this fails, log a warning but continue — presence is non-blocking.

### Step 3 — Read State

Fetch canvas state with three parallel requests:

```bash
# Document metadata
curl -sf "${BASE_URL}/api/canvas/${CANVAS_ID}" | jq .data

# Existing entity bindings
curl -sf "${BASE_URL}/api/canvas/${CANVAS_ID}/entities" | jq .data

# Pending suggestions
curl -sf "${BASE_URL}/api/canvas/${CANVAS_ID}/suggestions?status=pending" | jq .data
```

If the document has zero elements, report `STATUS: EMPTY` and skip to Step 5.

### Step 4 — Analyze

Trigger the suggestion engine:

```bash
curl -sf "${BASE_URL}/api/canvas/${CANVAS_ID}/suggestions/analyze" \
  -X POST -H 'Content-Type: application/json' \
  -d '{"autonomy_level": <AUTONOMY>}'
```

Fetch the newly generated suggestions:

```bash
curl -sf "${BASE_URL}/api/canvas/${CANVAS_ID}/suggestions?status=pending" | jq .data
```

**If `--approve` is set:** For each suggestion with `confidence >= 0.85`:

```bash
curl -sf "${BASE_URL}/api/canvas/${CANVAS_ID}/suggestions/${SID}/approve" \
  -X POST -H 'Content-Type: application/json'
```

Track counts: total generated, total auto-approved.

### Step 5 — Report + Leave

Format the output per the contract below, then leave presence:

```bash
curl -sf "${BASE_URL}/api/canvas/${CANVAS_ID}/presence/leave" \
  -X POST -H 'Content-Type: application/json' \
  -d '{"agentName":"canvas-agent"}'
```

## Output Contract

Returns structured markdown:

- **Status line:** `STATUS: ANALYZED`, `STATUS: EMPTY`, or `STATUS: ERROR`
- **Canvas summary:** name, id, binding count, suggestion count
- **Suggestions table:** numbered findings with type, confidence, payload, status
- **Recommendations:** actionable next steps

### Success Format

```
STATUS: ANALYZED

**Canvas:** <name> (<id>)
**Bindings:** <N> existing
**Suggestions:** <N> generated (<M> auto-approved)

| # | Type | Confidence | Payload | Status |
|---|------|------------|---------|--------|
| 1 | entity_recognition | 0.92 | "Component: AuthForm" | approved |
| 2 | layout_suggestion | 0.71 | "Group related elements" | pending |

### Recommendations
- Review 1 pending suggestion below threshold
- Consider binding AuthForm to knowledge graph entity
```

### Empty Format

```
STATUS: EMPTY

**Canvas:** <name> (<id>)
**Elements:** 0

No elements to analyze. Add content to the canvas first.
```

### Error Format

```
STATUS: ERROR

**Error:** <description>
**Canvas:** <name or arg> (<id or "unresolved">)

### Troubleshooting
- Verify services are running: `bin/tkr-services.sh status`
- Check canvas exists: `curl -s http://127.0.0.1:42005/api/canvas | jq`
```

## Examples

```bash
# Analyze by name with defaults (autonomy=1, no auto-approve)
# /canvas-agent my-project-canvas

# Analyze by ID with full autonomy and auto-approval
# /canvas-agent abc123nanoidvalue --autonomy 2 --approve

# Report-only mode (no suggestions generated)
# /canvas-agent my-canvas --autonomy 0
```
