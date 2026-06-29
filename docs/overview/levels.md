# Implementation Levels

## Quick Start (Level 1)

The simplest useful version — manifest + tier1 loading, no gates.

### 1. Install

```bash
# Copy hooks to your project
mkdir -p .agent/hooks
cp hooks/on_session_start.py .agent/hooks/
cp hooks/validators.py .agent/hooks/

# Install dependency
pip install pyyaml
```

### 2. Create your config

Copy `config.example.yaml` to your project root as `startup-config.yaml`:

```yaml
tiers:
  tier1:
    - name: project-rules
      source: docs/rules.md
      description: "Core project rules and conventions"
    - name: infra-report
      type: checks
      description: "Infrastructure health"

checks:
  - name: git-clean
    command: "git status --porcelain"
    validator: empty_output
  - name: tests-pass
    command: "npm test --silent 2>&1 | tail -1"
    validator: "contains:passing"
    optional: true

gates:
  block_until_tier1: false    # Level 1: no blocking
```

### 3. Add the hook

Add to your `.agent/settings.json` (or copy from `examples/level-1-minimal/`):

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python3 .agent/hooks/on_session_start.py",
        "timeout": 60000
      }]
    }]
  }
}
```

### 4. Start a session

the agent sees this output at session start:

```
STARTUP: 2 OK, 0 FAIL
Manifest: /tmp/manifest-abc123.json
Tier 1: 2 files (45 lines)
ACTION REQUIRED: Read manifest, then read all Tier 1 files.
  - /tmp/tier1-project-rules-abc123.md (30 lines, project-rules)
  - /tmp/tier1-infra-report-abc123.md (15 lines, infra-report)
```

Add to your project instructions:

```markdown
## Level 2: Add Gates

Level 1 relies on the agent voluntarily reading files. Level 2 **enforces** it —
the agent cannot use any tool except Read until all tier1 files are loaded.

### What changes

1. **PreToolUse gate** — blocks Bash, Write, Edit, Agent, etc. until tier1 is
   complete. Only Read is allowed (so the agent can load the files).
2. **UserPromptSubmit gate** — injects "read files first" into the agent's context
   if tier1 is incomplete. Also tracks prompt count and warns at thresholds.

### Install

```bash
cp hooks/gate_check.py .agent/hooks/
cp hooks/on_prompt_submit.py .agent/hooks/
```

Update `startup-config.yaml`:

```yaml
gates:
  block_until_tier1: true      # NOW ENFORCED
  prompt_health_warnings: [40, 60, 80]
```

Copy settings from `examples/level-2-gated/settings.json` or add the
PreToolUse and UserPromptSubmit hooks to your existing settings.

### How it works

1. SessionStart generates tier1 files + writes sentinel with `stage: "tier1_pending"`
2. the agent tries to use Bash → PreToolUse gate reads sentinel → tier1 incomplete → **DENIED**
3. the agent reads tier1 files → gate_check tracks each Read in sentinel
4. All tier1 files read → sentinel updated to `stage: "complete"`
5. the agent tries Bash again → gate checks sentinel → tier1 complete → **ALLOWED**

The UserPromptSubmit hook adds a second layer: if the agent somehow ignores the
PreToolUse denial, the prompt gate injects a message saying "read files first"
that the agent sees before composing its response.

---

## Level 3: On-Demand Tier 2

Not all rules are needed every session. Tier 2 files load **only when relevant
keywords appear** in the agent's tool calls.

### What changes

Add tier2 definitions with trigger keywords to your config:

```yaml
tiers:
  tier2:
    - name: api-rules
      triggers: ["api", "endpoint", "REST", "swagger"]
      source: docs/api-rules.md

    - name: deploy-guide
      triggers: ["deploy", "CI", "pipeline", "release"]
      source: docs/deploy-guide.md
```

### How it works

1. the agent runs `Bash("curl api.example.com/...")` 
2. PreToolUse gate scans the command text for tier2 triggers
3. Finds "api" matches the `api-rules` trigger → **DENIES** with message:
   "Tier 2 files triggered — read before proceeding: api-rules"
4. the agent reads the file → gate tracks it → next tool call is allowed

**Keyword scanning is limited** to prevent false positives:
- Only scans specific JSON fields (command, file_path, prompt, description)
- Only scans the first N characters of each field (default: 120)
- Case-insensitive matching

### Cross-Check Drift Detection

After tier1 loads, run a single drift check comparing expected vs actual state.
This catches stale references before they cause problems.

Add a script that checks your project's invariants:

```python
# Example: verify rule count in docs matches actual count
expected = manifest["expected_counts"]["rules"]
actual = len(list(Path("rules/").glob("*.md")))
if expected != actual:
    print(f"DRIFT: rules count {expected} in manifest vs {actual} on disk")
```

The cross-check runs once per session (tracked by `cross_check_done` in sentinel).

---

## Level 4: Full Architecture

### Stop Hook

Block session exit until cleanup is done:

```bash
cp hooks/on_stop.py .agent/hooks/
```

```yaml
stop:
  require_clean_repos: true
  require_transcript: false
  max_retries: 8
```

The stop hook returns exit code 2 (retry) when checks fail. the agent sees the
failure message and can fix the issue (e.g., commit uncommitted files). After
max retries, it exits cleanly to avoid trapping the user.

### Output-Based Validators

Shell exit codes lie. A piped command like `git status | grep -v node_modules`
returns 0 even when there are uncommitted files (because grep succeeded). The
validator registry parses stdout instead:

| Validator | Passes when |
|-----------|-------------|
| `empty_output` | stdout is empty (whitespace-only) |
| `not_empty` | stdout has content |
| `contains:text` | stdout contains text (case-insensitive) |
| `equals:text` | stdout exactly equals text (stripped) |
| `regex:pattern` | regex matches anywhere in stdout |

Add custom validators by extending `validators.py`:

```python
VALIDATORS["my_check"] = lambda stdout: (
    int(stdout.strip()) > 0,
    stdout.strip()
)
```

### Session-Scoped Isolation

All temp files include the session ID suffix (`-{SESSION_ID}`). This prevents:
- Concurrent sessions overwriting each other's state
- Resumed sessions reading stale sentinel from a previous run
- Race conditions between multiple AI coding agents instances

---
