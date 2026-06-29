# Architecture Overview


Four hook points work together:

```mermaid
graph TD
    A[SessionStart] -->|generates| B[manifest.json + sentinel.json]
    B --> C{UserPromptSubmit}
    C -->|tier1 incomplete| D[Inject 'read files first']
    C -->|tier1 complete| E[Track prompt count + warn at thresholds]

    F{PreToolUse} -->|tool = Read| G[Track file read + allow]
    F -->|tier1 incomplete| H[BLOCK tool]
    F -->|tier1 complete| I{Tier 2 keyword?}
    I -->|yes| J[BLOCK: read tier2 file first]
    I -->|no| K[ALLOW tool]

    L{Stop} -->|repos dirty| M[Exit 2 = retry]
    L -->|all clean| N[Exit 0 = allow]

    style A fill:#4a90d9,color:#fff
    style H fill:#d9534f,color:#fff
    style J fill:#f0ad4e,color:#fff
    style K fill:#5cb85c,color:#fff
    style N fill:#5cb85c,color:#fff
```

**Manifest** (`manifest.json`) — lists all tier1/tier2 files with paths, sizes,
and trigger keywords. Generated fresh each session.

**Sentinel** (`startup-complete-{session}.json`) — tracks which files the agent has
read, whether tier1 is complete, and whether cross-check has run. Session-scoped
to prevent collisions between concurrent or resumed sessions.
