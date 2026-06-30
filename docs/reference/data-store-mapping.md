# Data Store Mapping Guide

The course modules show YAML examples by default. If you chose **SQLite** in the
setup wizard, use this guide to translate each YAML construct to its database
equivalent.

The architecture (manifest, sentinel, gates, tiers) is identical regardless of
data store. Only the **source** of rules, checks, and config changes.

---

## Config (`startup-config.yaml` → `config` table)

=== "YAML"

    ```yaml
    gates:
      block_until_tier1: true
      tier2_keyword_scan: true
      prompt_health_warnings: [40, 60, 80]

    stop:
      require_clean_repos: true
      max_retries: 8
    ```

=== "SQLite"

    ```sql
    -- Config is stored as key-value pairs
    INSERT INTO config (key, value) VALUES
      ('gates.block_until_tier1', 'true'),
      ('gates.tier2_keyword_scan', 'true'),
      ('gates.prompt_health_warnings', '[40, 60, 80]'),
      ('stop.require_clean_repos', 'true'),
      ('stop.max_retries', '8');
    ```

---

## Rules (`rules/*.md` → `rules` table)

=== "YAML"

    ```yaml
    tiers:
      tier1:
        - name: core-rules
          source: rules/core-rules.md
          description: "Project rules and conventions"
    ```

    Then create the file `rules/core-rules.md` with rule content.

=== "SQLite"

    ```sql
    INSERT INTO rules (name, content, category, tier, description)
    VALUES (
      'core-rules',
      '### project-language
    This project uses TypeScript 5.x with strict mode.

    ### test-framework
    Tests use Vitest, not Jest. Run with: pnpm test',
      'general',
      1,
      'Project rules and conventions'
    );
    ```

    No separate file needed — content lives in the `content` column.

---

## Tier 2 Rules (on-demand loading)

=== "YAML"

    ```yaml
    tiers:
      tier2:
        - name: api-rules
          triggers: ["api", "endpoint", "REST"]
          source: docs/api-rules.md
    ```

=== "SQLite"

    ```sql
    INSERT INTO rules (name, content, category, tier, triggers, description)
    VALUES (
      'api-rules',
      '### api-base-url
    Always use /api/v2/ prefix...',
      'api',
      2,
      '["api", "endpoint", "REST"]',
      'API conventions and endpoint rules'
    );
    ```

    The `triggers` column stores a JSON array. The gate hook parses it
    the same way it parses YAML triggers.

---

## Infrastructure Checks (`checks:` → `checks` table)

=== "YAML"

    ```yaml
    checks:
      - name: git-clean
        command: "git status --porcelain"
        validator: empty_output
        fail_message: "Uncommitted changes detected"
      - name: tests-pass
        command: "npm test --silent 2>&1 | tail -1"
        validator: "contains:passing"
        optional: true
    ```

=== "SQLite"

    ```sql
    INSERT INTO checks (name, command, validator, fail_message, optional)
    VALUES
      ('git-clean', 'git status --porcelain', 'empty_output',
       'Uncommitted changes detected', 0),
      ('tests-pass', 'npm test --silent 2>&1 | tail -1', 'contains:passing',
       'Tests not passing', 1);
    ```

---

## Anti-Hallucination Rules

=== "YAML"

    ```yaml
    tiers:
      tier1:
        - name: ah-rules
          source: rules/anti-hallucination-rules.md
          description: "Anti-hallucination rules"
    ```

=== "SQLite"

    ```sql
    -- Insert the full rule set as a single tier 1 entry
    INSERT INTO rules (name, content, category, tier, description)
    VALUES (
      'ah-rules',
      '## PHASE 1 — READ
    ### R1: ONE ENTITY AT A TIME
    ...(full content)...',
      'anti-hallucination',
      1,
      'Anti-hallucination rules for faithful outputs'
    );
    ```

    Or load from file:

    ```bash
    sqlite3 project.db "INSERT INTO rules (name, content, category, tier)
    VALUES ('ah-rules', readfile('rules/anti-hallucination-rules.md'),
    'anti-hallucination', 1);"
    ```

---

## Backlog (session continuity)

=== "YAML (JSON file)"

    ```json
    {
      "tasks": [
        {"item": "Add dark mode", "status": "active", "priority": 2}
      ],
      "last_session": "2024-12-15"
    }
    ```

=== "SQLite"

    ```sql
    INSERT INTO backlog (item, status, priority)
    VALUES ('Add dark mode', 'active', 2);

    -- Query active items
    SELECT item, priority FROM backlog
    WHERE status = 'active' ORDER BY priority;
    ```

    See [Session Continuity](session-continuity.md) for the full schema
    and session handoff patterns.

---

## Cross-Check (drift detection)

=== "YAML"

    ```yaml
    cross_check:
      expected_counts:
        rules: 12
      verify_command: "find rules/ -name '*.md' | wc -l"
    ```

=== "SQLite"

    ```sql
    INSERT INTO config (key, value) VALUES
      ('cross_check.expected_counts', '{"rules": 12}'),
      ('cross_check.verify_command',
       'sqlite3 project.db "SELECT COUNT(*) FROM rules"');
    ```

---

## Session Summaries (`session_summaries` table — DB mode only)

The `session_summaries` table tracks what happened in each session and
enables continuity across sessions. It is created by `--init-db` and
queried by both the startup hook (to show "Continue From Last Session")
and the stop hook (to enforce `require_session_summary`).

=== "SQLite"

    ```sql
    CREATE TABLE IF NOT EXISTS session_summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT,
        completed_items TEXT,       -- JSON array of strings
        next_items TEXT,            -- JSON array of strings
        session_date DATE DEFAULT CURRENT_DATE,
        duration_minutes INTEGER,
        prompt_count INTEGER
    );

    -- Insert a session summary
    INSERT INTO session_summaries (topic, completed_items, next_items)
    VALUES (
      'Added auth middleware',
      '["Implemented JWT validation", "Added rate limiting"]',
      '["Write auth tests", "Update API docs"]'
    );

    -- Query last session for continuity
    SELECT topic, completed_items, next_items
    FROM session_summaries ORDER BY id DESC LIMIT 1;
    ```

This table has no YAML equivalent — session handoff in YAML mode uses a
JSON file (see [Session Continuity](session-continuity.md) for both
approaches).

---

## Hook Script Differences

| Aspect | YAML | SQLite |
|--------|------|--------|
| Script | `on_session_start.py` | `on_session_start_db.py` (renamed by wizard) |
| Config source | `startup-config.yaml` | `config` table |
| Rules source | Markdown files on disk | `rules` table `content` column |
| Dependencies | PyYAML | None (sqlite3 is Python stdlib) |
| Init command | Create YAML manually | `python3 on_session_start.py --init-db project.db` |
| Rule grouping | One file per source | Auto-grouped by `category` column |
| Truncation guard | N/A (files are read whole) | Stop hook verifies stored length matches source |

### Hook Script Naming

The repository contains two startup hook scripts:

- **`on_session_start.py`** — The YAML variant. Reads config from
  `startup-config.yaml` and rules from Markdown files on disk.
- **`on_session_start_db.py`** — The database variant. Reads config from
  the `config` table and rules from the `rules` table. Supports both
  SQLite and PostgreSQL via auto-detection of the connection string.

When the setup wizard runs with SQLite or PostgreSQL, it copies
`on_session_start_db.py` into your project's hooks directory and
**renames it to `on_session_start.py`** so that `settings.json` always
points to the same script name regardless of data store. If you set up
hooks manually without the wizard, use the `_db` variant directly and
rename it yourself, or update your `settings.json` command to reference
`on_session_start_db.py`.

Everything downstream of the SessionStart hook (manifest, sentinel, gates,
tier2 triggers, cross-check, stop hook) works identically regardless of
data store. The only difference is where the data comes from.

---

## PostgreSQL Limitations

!!! warning "PostgreSQL is experimental"

PostgreSQL support is present in the database variant hook script
(`on_session_start_db.py`) and uses auto-detection: if `AGENT_DB_PATH`
starts with `postgresql://` or `postgres://`, the script connects via
`psycopg2` instead of `sqlite3`. Schema creation and basic rule/config
reads work, but **several hook features silently skip PostgreSQL**:

| Feature | Hook | Behavior with PostgreSQL |
|---------|------|--------------------------|
| Session summary enforcement | `on_stop.py` | Skipped — no exit gate check |
| No-truncation verification | `on_stop.py` | Skipped — no length verification on exit |
| Edit logging to `rule_log` | `on_edit.py` | Skipped — edits are not recorded |
| Fact-reference staleness check | `gate_check.py` | Skipped — no stale-fact warnings |

These features use `sqlite3` directly (Python stdlib) and guard against
PostgreSQL with `not db_path.startswith("postgresql")`. The setup wizard
marks PostgreSQL as experimental and notes it is not yet tested in
production. If you need these features, use SQLite.

---

## When to Graduate from YAML to SQLite

See [Data Store & Platforms](../overview/data-and-platforms.md) for the
full comparison and pain signals that indicate it's time to migrate.
