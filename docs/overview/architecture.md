# Architecture Overview


Five hook points work together:

```mermaid
graph TD
    A[SessionStart] -->|generates| B[manifest.json + sentinel.json]
    B --> C{UserPromptSubmit}
    C -->|tier1 incomplete| D[Inject 'read files first']
    C -->|tier1 complete| E0{Infra FAILs?}
    E0 -->|YES first prompt| E1["Inject 'ACTION REQUIRED: fix FAILs'"]
    E0 -->|NO| E[Track prompt count + warn at thresholds]

    F{PreToolUse} -->|tool = Read| G[Track file read + allow]
    F -->|tier1 incomplete| H[BLOCK tool]
    F -->|tier1 complete| I{Tier 2 keyword?}
    I -->|yes| J[BLOCK: read tier2 file first]
    I -->|no| K[ALLOW tool]

    P{PostToolUse} -->|file edited| Q[Log edit to rule_log table]
    P -->|infra file edited| R[Flag for self-verification]
    P -->|scattered content detected| S["Rule Zero: warn agent"]

    L{Stop} -->|checks fail| M[Exit 2 = retry]
    L -->|self-verification + audit pass| N[Exit 0 = allow]

    style A fill:#4a90d9,color:#fff
    style E1 fill:#d9534f,color:#fff
    style H fill:#d9534f,color:#fff
    style J fill:#f0ad4e,color:#fff
    style K fill:#5cb85c,color:#fff
    style N fill:#5cb85c,color:#fff
```

**Manifest** (`manifest.json`) — lists all tier1/tier2 files with paths, sizes,
and trigger keywords. Generated fresh each session.

**Sentinel** (`startup-complete-{session}.json`) — tracks which files the agent has
read, whether tier1 is complete, and whether cross-check has run. When cross-check
detects persistent drift, it generates `write_back_suggestions` stored in the
sentinel — these propose manifest updates (e.g., corrected counts or paths) that
can be applied to keep the config in sync with reality. Session-scoped
to prevent collisions between concurrent or resumed sessions.

**PostToolUse — Rule Zero & Edit Tracking** (`on_edit.py`) — fires after every
tool use. Tracks file edits in the `rule_log` table for audit trail. When an
infrastructure file is edited, it flags the session for self-verification at
exit. Rule Zero enforcement scans edited files for scattered content (rules,
facts, or decisions embedded outside the canonical store) and warns the agent
to consolidate.

**Audit Runner** (`audit.py`) — standalone audit runner that validates project
invariants (rule counts, file integrity, config consistency). Integrated with
the stop hook at Level 4: `require_audit_pass` runs the audit checks before
allowing session exit. Can also be invoked manually for on-demand validation.

**Stop Hook — Self-Verification** (`on_stop.py`) — at Level 4, the stop hook
goes beyond clean-repo checks. `require_self_verification` blocks exit if
infrastructure files were edited after the last validation pass, forcing the
agent to re-verify before closing. Session continuity is enforced by requiring
a session summary and checking for open backlog items.
