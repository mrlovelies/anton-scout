---
name: scout
description: |
  Discovery scout for AI techniques worth adopting. Gathers candidate techniques
  (you paste them, or I web-search a topic you name), extracts the transferable
  idea from each, scores it against YOUR system's real open problems, and returns
  a ranked digest of what's worth building — backed by anton-scout's decoy-injection
  eval. It stops at discovery on purpose: it never writes the code, and you decide
  what to build.

  TRIGGERS: "/scout", "scout for <topic>", "find techniques to improve the infra",
  "what's worth adopting for <system>", "any new approaches for <open problem>",
  "scout these candidates", "run a discovery pass".
  Do NOT trigger for: building/implementing a technique (that's a normal session —
  the scout deliberately stops before the build step), or pure factual lookups.
version: 1.0.0
---

# Scout — find AI techniques worth adopting

Wraps the [anton-scout](https://github.com/mrlovelies/anton-scout) discovery tool. The
job: turn "there's a lot of AI noise out there" into "here are the 3 ideas actually worth
building for *my* open problems, ranked, with the hype filtered out." It produces a
digest for a human to act on — it never builds anything itself.

**The boundary is the point.** The scout finds and scores; it does not auto-build and it
does not crawl-and-reimplement on its own. A bad idea extracted and reimplemented as clean
code in your own repo is the failure mode it refuses to risk. You stay on the build step.

Repo lives at `~/wkspaces/anton-scout`. Run everything from there.

## Step 1 — Anchor: what are we scouting against?

The scout scores candidates against an **open-problems doc** — the only gaps that count.
Default: `~/wkspaces/anton-scout/open_problems.md` (Alex's real infra gaps: fleet model
routing, multi-writer SQLite, scoped agent API, local structured output, personal-vs-
shippable drift, portfolio signal, creative tooling).

Before scouting, glance at that file. If the infra has moved on, **update the open-problems
doc first** — a stale anchor scores against gaps you've already closed. Ask Alex one
question if it's unclear which gaps are live right now.

## Step 2 — Gather candidates

The scout does not find candidates on its own (a deliberate boundary). Two ways in:

- **Alex pastes them** — repos, blog posts, papers, "this technique I keep seeing." Best
  signal, since he's already filtered.
- **I web-search a topic he names** — e.g. "scout for local-LLM routing." I gather 5–12
  recent, real candidates (name + one-line summary + source URL). I am the gatherer here;
  the scout is still the scorer, and Alex still decides — the no-auto-build boundary holds.

Write the candidates to a temp JSONL in anton-scout's format (one object per line):

```json
{"id": "c1", "name": "<short name>", "summary": "<2-3 sentences: what the technique actually is>", "source": "<url or repo>"}
```

Keep summaries concrete and free of marketing — the scout extracts the *technique*, so
give it the technique, not the pitch.

## Step 3 — Run the scout

```bash
cd ~/wkspaces/anton-scout
python -m anton_scout scout --candidates /tmp/scout-candidates.jsonl --backend cli
# add  --problems <path>  to score against a different open-problems doc
# --backend cli uses the claude CLI (free); --backend mock is offline/no-LLM
```

It returns a ranked digest: per candidate, the extracted nugget, which open problem it
maps to, a buy-vs-build call, and a 1–10 composite (derived from the model's dimension
scores, never taken on faith). Only candidates with a real nugget that map to an actual
gap and clear the threshold make the digest.

## Step 4 — Present it, and hand back the decision

Show the ranked digest plainly. Lead with what cleared the bar and why; note what got
filtered and why (hype, wrong-context, or "just use the upstream"). Then stop and let
Alex pick what to build — the scout's whole stance is that the human keeps the build step.

Optional: `python -m anton_scout eval --backend cli` runs the decoy-injection eval (does
the scorer still tell a real idea from hype?) — worth it if the candidate set was large or
the calls felt off.
