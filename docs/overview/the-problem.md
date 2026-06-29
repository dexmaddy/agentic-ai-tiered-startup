# The Problem


Without managed startup, AI agent sessions suffer from three issues:

1. **Context waste** — loading everything every session burns tokens on rules
   that aren't needed for the current task. A 3000-line rule set costs ~4K
   tokens on every session, even when you're just fixing a typo.

2. **Rule drift** — facts, counts, and references go stale. Your project instructions
   says "58 rules" but the DB has 62. No one notices until a rule is missed.

3. **Startup chaos** — CLAUDE.md says "read these files" but there's no
   enforcement. the agent skips files, partially loads context, or starts working
   before critical rules are loaded. Writing "you must read X" in a markdown
   file is documentation, not enforcement.

This architecture solves all three with **tiered loading** (load what's needed),
**structural gates** (block tools until context is loaded), and **drift detection**
(catch stale references automatically).
