# Module 1: The Problem

**Time:** 10 minutes
**Goal:** Understand the six problems that unmanaged AI sessions create,
and diagnose which ones affect your project.

---

## The Six Problems

### Problem 1: Context Waste

Every AI agent session has a finite context window. Everything the agent
reads — files, command output, your messages — consumes tokens from that
window. When the window fills, older content is compressed or lost.

**The waste pattern:**
```
Session starts
  → the agent reads 3000 lines of rules (costs ~4K tokens)
  → User asks to fix a typo
  → 4K tokens wasted on rules that weren't needed
```

Multiply this by every session, and you're burning significant context
budget on rules that only matter 20% of the time.

**The fix:** Load rules in tiers — essential rules always, specialized
rules only when the task needs them.

### Problem 2: Rule Drift

Your project has facts that change: table counts, API endpoints, version
numbers, team conventions. These facts live in your instructions file, memory files,
or rule documents.

**The drift pattern:**
```
Week 1: CLAUDE.md says "58 rules in the system"
Week 3: You added 4 more rules
Week 5: CLAUDE.md still says "58 rules"
         The agent trusts the stale number
         References the wrong rule count in outputs
```

Drift is invisible until it causes a mistake. By then, you don't know
how many other facts are stale.

**The fix:** Generate rule files from a single source of truth (config
file or database) at session start. Detect drift automatically.

### Problem 3: Startup Chaos

You write "the agent must read these files at startup" in your instructions file. The agent
reads it. Then:

- Reads 4 of 6 files and starts working
- Reads the files but in the wrong order
- Skips reading entirely because the user asked a question first
- Reads the files but context compaction later loses them

**The chaos pattern:**
```
CLAUDE.md: "Always read rules/core.md before any task"
Reality:   the agent read it in 3 of 10 sessions
           In 2 sessions, it was lost to context compaction
           In 5 sessions, the agent started working immediately
```

Writing instructions in a markdown file is documentation, not enforcement.
There's no mechanism to guarantee the agent follows them.

**The fix:** Structural enforcement — hooks that physically block the agent
from using tools until the rules are loaded.

### Problem 4: Information Scattering

Learnings and decisions accumulate in conversations and random files,
lost at session end. Without routing, knowledge stays fragmented.

**The scattering pattern:**
```
Session 1: Agent discovers the API needs auth headers
           → mentioned in conversation, never saved
Session 5: Agent hits the same API without auth
           → wastes 15 minutes rediscovering the same fix
```

Without a routing mechanism, insights stay trapped in the session
that produced them.

**The fix:** Route learnings to a persistent store (DB or structured files)
at the point of discovery, not as an afterthought at session end.

### Problem 5: Session Amnesia

Every new session starts from zero. The agent doesn't know what was done
last time or what's next. Users re-explain context every session.

**The amnesia pattern:**
```
Session 1: Agent fixes 3 of 5 bugs, notes the remaining 2
Session 2: Agent asks "what would you like me to work on?"
           → User re-explains the project, the 5 bugs, which 3 are done
           → 10 minutes of context re-establishment before any work
```

Without session continuity, every session restarts from zero regardless
of how much progress was made.

**The fix:** Persistent backlog and session summaries that carry state
across sessions automatically.

### Problem 6: Unverified Completion

The agent says "done" but the fix wasn't tested, the commit wasn't
pushed, or the config wasn't validated. Generating output feels like
completing the task.

**The unverified pattern:**
```
Agent: "I've fixed the bug and updated the tests"
Reality: The fix was applied but tests weren't run
         The commit was staged but not pushed
         The config was edited but not validated
```

Without exit checks, the session ends with a false sense of completion.

**The fix:** Stop hook that verifies actual completion — clean repos,
passing tests, saved state — before allowing session exit.

---

## Diagnose Your Project

### Exercise 1: Count the Waste (5 minutes)

Open your project instructions. Estimate:

1. **Total lines of instructions:** ___
2. **Lines needed for a typical session:** ___
3. **Waste ratio:** (1 - line 2/line 1) × 100 = ____%

If your waste ratio is over 40%, tiered loading will save significant
context budget.

### Exercise 2: Find the Drift (3 minutes)

Search your project instructions for any numbers, versions, or counts:

```bash
grep -E "[0-9]+" CLAUDE.md | head -20
```

For each number: is it still correct? Check the actual source.

Common drift candidates:
- Rule counts ("58 rules" → actually 62 now)
- API endpoints ("v2" → project moved to v3)
- Team conventions ("use Jest" → migrated to Vitest)

### Exercise 3: Test the Enforcement (2 minutes)

Start a fresh AI agent session and immediately ask a question
(don't mention startup or rules). Does the agent:

- [ ] Read your rule files before answering? → You're already enforced
- [ ] Answer directly, skipping rule files? → You need gates
- [ ] Read some files but not all? → You need tracking + gates

---

## Key Takeaway

| Problem | Symptom | Solution |
|---------|---------|----------|
| Context waste | High token usage, rules loaded but not needed | Tiered loading (Module 3) |
| Rule drift | Stale numbers in instructions, wrong facts in output | Generated files + drift detection (Module 5) |
| Startup chaos | Inconsistent behavior across sessions | Structural gates (Module 4) |
| Information scattering | Learnings lost between sessions, same mistakes repeated | Persistent store + routing (Module 5) |
| Session amnesia | Re-explaining context every session, no continuity | Backlog + session summaries (Module 5) |
| Unverified completion | Agent says "done" but work isn't actually complete | Stop hook + exit checks (Module 5) |

Most projects have all six. The architecture in this course solves
them together — each module adds a layer of defense.

---

**Next:** [Module 2 — Architecture Concepts](module-2-architecture.md)
