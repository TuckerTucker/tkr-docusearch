---
name: planning
description: Unified planning system — manage products, capabilities, features, stories, slices, specs, and expansion
allowed-tools: [Read, Write, Glob, Grep, Bash, Task]
source: tkr-kit
version: 2.0.0
---

# /planning Command

> **Layer 3 — Thin Dispatcher.** This command parses `/planning <domain> <action>` and delegates to the planning skill (L1). It contains no business logic, no fan-out, and no aggregation — the skill handles everything. This is not an orchestration command; it's a CLI entry point.

## Stack Position

| Layer | Component | Relationship |
|-------|-----------|-------------|
| **L3 Command** | **`planning` (this file)** | **parses args, delegates to skill** |
| L2 Agent | _deferred_ | not needed until parallel multi-feature orchestration |
| L1 Skill | `planning` | manages hierarchy, expands artifacts, tracks status |

Unified entry point for all planning operations. Invokes the planning skill with structured arguments.

## Usage

```
/planning <domain> <action> [args]
/planning status
```

## Domains and Actions

### Product

```
/planning product create "Product Name"
/planning product list
/planning product get [id]
/planning product update [id]
/planning product delete [id]
/planning product summary [id]
```

### Capability

```
/planning capability create [product-id] "Capability Name"
/planning capability list [product-id]
/planning capability get [id]
/planning capability update [id]
/planning capability delete [id]
/planning capability spec [id]
/planning capability validate [id]
/planning capability deps [id]
```

### Feature

```
/planning feature create "Feature Name"
/planning feature list
/planning feature get [id]
/planning feature update [id]
/planning feature delete [id]
/planning feature summary [id]
```

### Story (Interaction Stories)

```
/planning story create [feature-id] "Story Title"
/planning story list [feature-id]
/planning story get [id]
/planning story update [id]
/planning story delete [id]
/planning story by-slice [slice-id]
```

### Slice

```
/planning slice create [feature-id]
/planning slice list [feature-id]
/planning slice get [id]
/planning slice update [id]
/planning slice suggest [capability-id|feature-id]
```

### Spec

```
/planning spec create [feature-id] [slice-number]
/planning spec list [feature-id]
/planning spec get [feature-id] [slice-number]
/planning spec update [id]
/planning spec generate [feature-id] [slice-number]
```

### Expand

```
/planning expand stories [feature-id]
/planning expand slices [feature-id]
/planning expand specs [feature-id]
/planning expand patterns [feature-id]
```

### Status

```
/planning status
/planning status [id]
```

## Context Inference

Arguments in `[brackets]` are optional when context is unambiguous:

- **Single product** → used automatically
- **Single feature** → used automatically
- **Name match** → `"auth"` resolves to the entity containing "auth" if unique
- **Conversation context** → recently discussed entities are preferred
- **Ambiguous** → presents numbered options

## Implementation

When this command is invoked, parse `$ARGUMENTS` to determine:
1. **Domain** — first word (product, capability, feature, story, slice, spec, expand, status)
2. **Action** — second word (create, list, get, update, delete, etc.)
3. **Arguments** — remaining words (IDs, names in quotes, flags)

Then follow the planning skill instructions for the resolved domain and action.

### Argument Resolution

1. Parse domain and action from `$ARGUMENTS`
2. If domain is `status` with no further args → show full dashboard
3. If an ID-like argument is present → use it directly
4. If a quoted string is present → treat as name (for create) or search term
5. If no ID or name → apply context inference rules
6. If still ambiguous → ask user to clarify

### Reading the Skill

Before executing, read the planning skill for domain-specific guidance:
- `.claude/skills/planning/SKILL.md` — domain routing, algorithms, schema references
- `.claude/skills/planning/expansion-levels.md` — for expand operations
- `.claude/skills/planning/cross-cutting.md` — for pattern detection
- `.claude/skills/planning/status-tracking.md` — for status transitions and queries

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/planning product create "X"` | Create new product |
| `/planning capability spec <id>` | Generate 13-section capability spec |
| `/planning feature create "X"` | Create new feature |
| `/planning story list <feature-id>` | List interaction stories for a feature |
| `/planning expand stories` | Generate stories from feature extension |
| `/planning slice suggest <id>` | Suggest slices from capability/feature |
| `/planning expand slices` | Generate slices from feature inventory |
| `/planning expand specs` | Generate specs for ready slices |
| `/planning expand patterns` | Detect cross-cutting concerns |
| `/planning status` | Show planning dashboard |

## Examples

```
/planning product create "tkr-kit"
/planning capability create "Planning System" --layer domain
/planning feature create "Unified Planning Skill"
/planning expand stories
/planning expand slices
/planning expand specs
/planning story list
/planning status
/planning slice suggest
/planning spec generate 3
```
