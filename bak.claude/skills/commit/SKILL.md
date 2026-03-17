---
name: commit
description: Analyzes staged changes for atomic commits, generates conventional commit messages, detects when changes should be split, and guides users through quality commit workflows.
allowed-tools: [Bash, Grep, Read, Glob]
source: tkr-kit
version: 2.0.0
---

# Commit Analysis & Guidance

> **Layer 1 — Capability.** This is a skill. It encapsulates commit analysis, splitting, and message generation. It does NOT orchestrate agents or fan out work. It produces structured output that agents and commands can parse.

## Composition

| Layer | Component | Status |
|-------|-----------|--------|
| L3 Command | _none yet_ | could orchestrate multi-repo or batch commit workflows |
| L2 Agent | _none yet_ | could wrap this for automated commit pipelines |
| **L1 Skill** | **`commit` (this file)** | **provides commit analysis and message generation** |

## When to Use

- User has staged changes and wants to commit
- User asks about commit message format
- User has many changes and needs splitting guidance
- User mentions conventional commits, atomic commits, or commit hygiene
- Agent invokes this skill as part of a commit pipeline

## Core Responsibilities

1. **Splitting Analysis** — detect when staged changes should be multiple commits
2. **Message Generation** — create conventional commit messages
3. **Scope Detection** — identify affected modules and appropriate scopes
4. **Type Classification** — determine commit type (feat, fix, refactor, etc.)

## Instructions

### Step 1: Get Staged Changes

Stage all changes.

```bash
git diff --cached --stat
git diff --cached --name-only
```

### Step 2: Group by Scope

Analyze file paths to identify scopes:

| Path Pattern | Scope |
|---|---|
| `core/*` | follows subdomain (e.g., `planning`, `hooks`, `search`) |
| `services/*` | follows service name (e.g., `koji`, `observability`) |
| `mcp/tools/*` | `mcp` or follows tool name |
| `dashboard/*` | `dashboard` |
| `.claude/skills/*` | `skills` |
| `.claude/commands/*` | `commands` |
| `.claude/agents/*` | `agents` |
| `**/tests/**` or `**/__tests__/**` | follows source scope |
| `*.md` (docs) | `docs` |
| `*.json` (config) | `config` or follows context |

### Step 3: Detect Change Types

For each file group, analyze the diff:

```bash
git diff --cached [file]
```

| Signal | Type |
|---|---|
| New file created | `feat` |
| New exports added | `feat` |
| Error handling added/fixed | `fix` |
| Edge case handling | `fix` |
| Test file only | `test` |
| Comments/docs only | `docs` |
| Rename/restructure | `refactor` |
| Formatting only | `style` |
| Build/config changes | `chore` or `build` |

### Step 4: Evaluate Cohesion

Changes are **cohesive** (single commit) when:
- Same scope AND same type
- Test files paired with implementation they test
- Config changes directly supporting code changes
- Related files in a single feature addition

Changes should be **split** when:
- Multiple unrelated scopes (e.g., `auth` + `ui` + `api`)
- Mixed types (e.g., `feat` + `fix` + `refactor`)
- Independent changes bundled together
- Tests for existing code mixed with new features

### Step 5: Generate Output

Format results per the Output Contract below.

## Splitting Thresholds

| Condition | Recommendation |
|---|---|
| ≤5 files, single scope | No split needed |
| 6-10 files, mixed scopes | Suggest analysis |
| >10 files | Strongly recommend analysis |
| >20 files | Require split or explicit override |
| >500 lines changed | Consider splitting regardless |
| Multiple commit types | Always recommend split |

## Commit Message Format

### Conventional Commits Structure

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Type Reference

| Type | When to Use |
|---|---|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code change without behavior change |
| `test` | Adding/updating tests |
| `chore` | Maintenance, deps, build |
| `perf` | Performance improvement |
| `ci` | CI/CD changes |
| `build` | Build system changes |
| `revert` | Reverting previous commit |

### Scope Guidelines

- Use lowercase
- Keep concise (1-2 words)
- Match directory/module name
- Omit if change spans entire codebase

### Description Guidelines

- Imperative mood ("add" not "added")
- No period at end
- ≤50 characters for subject line
- Explain what and why, not how

### Examples

**Good:**
```
feat(auth): add OAuth2 provider support
fix(api): handle rate limit errors gracefully
refactor(core): extract embedding service
test(github): add device flow tests
docs(readme): update installation steps
```

**Bad:**
```
Updated files           # No type, vague
fix: Fixed the bug      # Redundant, past tense
feat(authentication-module): Added new feature for users to login  # Too long, past tense
```

## Output Contract

> This contract is the interface between layers. If an agent (L2) wraps this skill, it will parse these formats to build its report. Do not change this structure without updating any corresponding agent.

### Split Recommended

```
STATUS: SPLIT_RECOMMENDED

**Analysis:** [N] files staged (+[add]/-[del])
**Commits:** [N] recommended

| # | Type | Scope | Message | Files |
|---|------|-------|---------|-------|
| 1 | feat | auth | add OAuth2 provider support | 3 (+120/-0) |
| 2 | test | auth | add OAuth2 provider tests | 2 (+85/-0) |
| 3 | docs | readme | update auth setup instructions | 1 (+12/-3) |

### Execution Plan
1. `git reset HEAD .`
2. `git add [files] && git commit -m "[message]"`
...
```

### No Split Needed

```
STATUS: COHESIVE

**Analysis:** [N] files staged (+[add]/-[del])
**Scope:** [scope]
**Type:** [type]
**Message:** [type]([scope]): [description]

[body explaining what and why]
```

### Nothing Staged

```
STATUS: EMPTY

**Error:** No staged changes found
**Hint:** Stage changes with `git add <files>` before running /commit
```

## Integration: /commit Command

```
/commit              # Standard commit with analysis
/commit --analyze    # Explicit split analysis only
/commit --force      # Skip split analysis
/commit --quick      # Minimal checks
/commit --full       # All quality checks
```

## Post-Commit: Context YAML Update

After a successful commit, update `_context-kit.yml` if the changes affect project structure.

### Identify Affected Sections

Map committed files to context sections:

| File Pattern | Context Section |
|---|---|
| `package.json`, `*.lock` | deps |
| New/deleted files, directories | struct |
| `*.vue`, `*.css` | design |
| Route files, API handlers | api |
| Config files, `.env*` | config |
| Import structure changes | relations |
| Test files | testing |
| TODO/FIXME changes | issues |
| Entry points, exports | nav |

### When to Skip Context Update

- Only `.md` documentation files changed (unless README)
- Only test files changed with no new patterns
- Commit was a revert
- User explicitly requests `--no-context-update`

## Best Practices

1. **Atomic commits** — each commit is a single logical change
2. **Bisectable history** — each commit builds and passes tests
3. **Clear messages** — future readers understand why
4. **Appropriate scope** — not too broad, not too narrow
5. **Test pairing** — tests with the code they test
6. **Config separation** — config changes can often be separate commits
