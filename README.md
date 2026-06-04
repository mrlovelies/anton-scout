# anton-scout

A discovery scout: it takes candidate AI techniques, **extracts the transferable
idea**, maps each to a target system's real open problems, and produces a **ranked
digest of "ideas worth stealing"** — with an eval loop that proves its discriminator
actually works.

It surfaces ideas. It does **not** write code, and it does **not** crawl sources on
its own — candidates are fed in (a real crawler is future work). Both boundaries are
deliberate, not unfinished; the [next section](#why-discovery-not-auto-build)
explains why stopping at discovery is the point.

---

## Why discovery, not auto-build

The obvious version of this tool is a closed loop: discover a technique, auto-build
it in a sandbox, open a PR. I built the discovery half and deliberately stopped,
because the autonomous-build half concentrates three failure modes that are hard to
detect and expensive to be wrong about:

- **Injection laundered into architecture.** The scout ingests untrusted content
  (READMEs, blog posts). "Extract the idea and reimplement it" means a malicious
  *idea* — "add a lightweight telemetry beacon" — can become clean, first-party code
  that no dependency scanner flags. The human reviewer is the trust boundary.
- **Confident non-nuggets.** Telling a real technique from repackaged hype is a
  taste problem. An LLM will happily extract a plausible-sounding nugget from
  nothing. A human catches "this is just `store summaries`, dressed up."
- **Goodhart.** The moment a relevance score *gates* an autonomous loop, the loop
  optimizes the score instead of the goal — especially if it also learns which
  framings get approved. Keeping a human as the build step keeps the score a
  *measure*, not a *target*.

So: the scout produces a digest, a human picks winners and implements them in a
normal session. Auto-build is revisited only if a real trigger fires — **discovery
volume consistently exceeds the human's build throughput** (good cards routinely
left unbuilt). Until then, automating the cheap half (writing code) to risk the
expensive half (judgment) is a bad trade.

## Steal the idea, not the dependency — with a release valve

Trendy frameworks usually contain *some* real technique. The scout is an
**extractor, not a rejecter**: it lifts the transferable idea and scores that, not
the hype. But reimplementing everything in-stack is a ratchet — you'd trade
dependency-debt for a museum of half-tested clones with no CVE coverage. So every
candidate gets an explicit **buy-vs-build** call that is allowed to conclude *"just
adopt the upstream."*

## How it works

```
candidates ─▶ scout ─▶ [extract nugget · map to gap · buy-vs-build · score 1-10] ─▶ digest
                │                                                                     ▲
           open_problems.md  (the scoring anchor — the only gaps that count)          │
                                                                          strict eligibility
```

- The **model** does judgment (nugget, mapping, buy-vs-build, dimension scores).
- **Python** derives the composite from the dimension scores — the headline number
  is always reproducible from its parts, never trusted from the model.
- A card reaches the digest only if it has a real nugget, maps to an actual gap, and
  clears the threshold. Everything else goes to a visible **filtered** section —
  nothing is silently dropped.

## The eval loop (decoy injection)

The scout's value rests on one claim: it can tell a real nugget from hype. That's
testable. The candidate set is seeded with **decoys** (real buzzwords, zero
technique) and **irrelevant** entries (genuine techniques, wrong context — e.g.
10k-QPS serving for a solo operator). A healthy scout filters all of them out.

```
python -m anton_scout eval
```

Reports **decoy catch rate** (did it reject the planted junk?) and **real recall**
(did it keep the genuine ideas?). It exits non-zero if a decoy leaks into the digest
— so it works as a CI gate. The ground-truth labels live in the candidate file and
are stripped before the scout ever sees them (`load_candidates` and the eval read the
file independently — the scout never receives the answer key).

Latest run — `--backend cli` (claude CLI), 2026-06-04, over 11 candidates of which 6
are decoys/irrelevant (including subtler ones: a "metacognition" framework that's just
sequential prompting, and a Mixture-of-Agents technique that's real but wrong-context
for a solo operator):

```
decoy catch rate:  1.0   (caught every decoy, including the subtle ones)
real recall:       1.0   (kept every genuine idea)
```

A perfect score is only as meaningful as the decoys are hard — see
[`candidates/seed.jsonl`](candidates/seed.jsonl) to judge for yourself, and add
harder ones. The deterministic core (composite, gate, JSON parsing, label-stripping)
is covered by unit tests in [`tests/`](tests/test_core.py) that run with no model and
no network.

## Usage

```bash
# Produce a digest (defaults to the bundled open_problems.md + seed candidates)
python -m anton_scout scout --out digest.md

# Run the discriminator eval
python -m anton_scout eval

# See the pipeline run with zero auth (deterministic offline stub)
python -m anton_scout scout --backend mock

# Unit tests for the deterministic core (no model, no network)
python -m pytest        # or: python tests/test_core.py
```

**Backends:** `--backend cli` (default) shells out to the `claude` CLI — free on an
existing subscription, no key. `--backend api` uses the Anthropic SDK (caches the
system prompt). `--backend mock` is a deterministic keyword stub so you can run the
pipeline offline without any auth — it is **not** the discriminator (it only catches
the obvious cases); real scoring quality comes from `cli`/`api`.

## Layout

| File | Role |
|---|---|
| `anton_scout/scout.py` | extract + map + score; derive composite in Python |
| `anton_scout/digest.py` | strict eligibility + ranked render |
| `anton_scout/eval.py` | decoy-injection eval loop |
| `anton_scout/llm.py` | swappable `cli` / `api` / `mock` backend |
| `open_problems.md` | the scoring anchor (target system's real gaps) |
| `candidates/seed.jsonl` | example candidates incl. labeled decoys |
| `tests/test_core.py` | unit tests for the deterministic core |
| `examples/sample-digest.md` | a real committed run (not hand-edited) |

## Status & honest scope

v0.1. What works: extract → map → buy-vs-build → score, strict-eligibility digest, a
decoy-injection eval (1.0/1.0 on the current 11-candidate set), unit-tested core, and
three backends. What it deliberately is **not**: it's a single batched model call over
**file-fed** candidates — there's no source crawler and no scheduler yet (that's the
obvious next step), and there's no auto-build (that's an intentional safety boundary,
not a missing feature — see "Why discovery, not auto-build"). The buy-vs-build call is
a model judgment surfaced for the human, not an enforced mechanism.

Requires Python 3.10+. Built as a focused project, AI-assisted — the design decisions
(derive-don't-trust scoring, the label-stripped two-sided eval, the discovery/build
boundary) are the point.
