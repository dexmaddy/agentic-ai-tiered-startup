# The Problem


Without managed startup, AI agent sessions suffer from six issues:

1. **Context waste** — loading everything every session burns tokens on rules
   that aren't needed for the current task. A 3000-line rule set costs ~4K
   tokens on every session, even when you're just fixing a typo.

2. **Rule drift** — facts, counts, and references go stale. Your project instructions
   say "58 rules" but the DB has 62. No one notices until a rule is missed.

3. **Startup chaos** — CLAUDE.md says "read these files" but there's no
   enforcement. The agent skips files, partially loads context, or starts working
   before critical rules are loaded. Writing "you must read X" in a markdown
   file is documentation, not enforcement.

4. **Information scattering** — learnings, decisions, and conventions accumulate
   in conversations and random files. When the session ends, they're lost.
   Without a routing mechanism, the knowledge base stays fragmented.

5. **Session amnesia** — every new session starts from zero. The agent doesn't
   know what was done last time, what's in progress, or what's next. Users
   re-explain context every session.

6. **Unverified completion** — the agent says "done" but the fix wasn't
   tested, the commit wasn't pushed, or the config wasn't validated.
   Generating output *feels* like completing the task, but the gap between
   "I did it" and "it's done" is where failures hide.

This architecture solves all six:

- **Tiered loading** — load what's needed, defer the rest (problems 1, 2)
- **Structural gates** — block tools until context is loaded (problem 3)
- **Drift detection** — catch stale references automatically (problem 2)
- **Rule Zero** — route scattered information to consolidated files at edit time (problem 4)
- **Session continuity** — persistent backlog and session handoff across sessions (problem 5)
- **Self-verification** — block exit until work is verified, not just narrated (problem 6)

See [What It Does For You](capabilities.md) for the full capability map.
