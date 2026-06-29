# Lessons Learned


These insights emerged from building and iterating on this system across dozens
of sessions:

1. **Documenting is not doing.** Writing "the agent must read X at startup" in
   CLAUDE.md doesn't make it happen. Structural enforcement (hooks that block
   tools) is the only reliable mechanism. If it's not enforced, it's optional.

2. **Exit codes lie.** Shell commands with pipes, `||`, subshells, and error
   handling masks return 0 when they shouldn't. Parse stdout with validators
   instead of trusting `$?`.

3. **Session-scope everything.** Temp files without session IDs cause mysterious
   failures when sessions resume or run concurrently. Always suffix with session ID.

4. **Tier wisely.** The split between tier1 and tier2 should be based on
   *frequency of need*, not *importance*. Critical API rules that only matter
   when doing API work belong in tier2 with an "api" trigger — not in tier1
   where they waste tokens on every session.

5. **Bound your loops.** Cross-check drift detection must be bounded (2 passes
   max, then continue). Unbounded self-healing loops can spiral when fixes
   create new drift. Fix what's safe, log the rest, move on.

6. **Gate, don't nag.** A written instruction that says "please read X first"
   is a suggestion. A PreToolUse hook that returns `permissionDecision: "deny"`
   is a gate. Gates work. Suggestions don't.

7. **Track reads, not intentions.** The sentinel tracks which files the agent
   *actually read* (via Read tool path matching), not which files it was
   *told to read*. This closes the gap between "I loaded the rules" and
   "the rules are in my context."

8. **More reasoning = worse faithfulness.** Giving the LLM more thinking
   time makes summaries *less* faithful to sources (r = -0.685). Use
   reasoning for verification, never for generation. See the
   [Anti-Hallucination Rules](../rules/anti-hallucination-rules.md).

9. **Route, don't scatter (structurally enforced).** The `on_edit.py` hook
   scans every edited file for keyword overlap with consolidated files and
   warns if content is scattered. Without this
   ([Rule Zero](../reference/rule-zero.md)), information accumulates in
   conversations and is lost at session end.

10. **Verify, don't narrate (structurally enforced).** The `on_stop.py` hook
    blocks session exit if infrastructure files were edited after the last
    verification check. The
    [4-point self-check](../reference/self-verification.md) catches what
    task completion misses.

11. **Make the loop bidirectional (structurally enforced).** The
    `cross_check.py` hook generates `write_back_suggestions` for persistent
    drift, proposing manifest updates or investigation. The
    [Self-Healing Loop](../reference/self-healing-loop.md) keeps both
    sides growing from each other.

---
