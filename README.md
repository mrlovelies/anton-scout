# anton-scout

A discovery scout. You feed it candidate AI techniques, it pulls the transferable
idea out of each one, checks that idea against a target system's actual open problems,
and hands back a ranked digest of what's worth adopting. It also ships an eval that
proves the thing can tell a real idea from hype.

Two things it doesn't do, on purpose. It doesn't write code, and it doesn't go find
candidates on its own (you feed them in for now). Neither of those is a corner I ran
out of time to finish. The next section is the whole reason it stops at discovery.

## Why discovery, not auto-build

The tempting version of this is a closed loop: find a technique, build it in a
sandbox, open a PR, repeat. I built the discovery half and stopped there on purpose,
because the auto-build half is where the bad failures live, and they're the kind you
don't notice until it's too late.

- **Injection that ends up as architecture.** The scout reads whatever's out there:
  READMEs, blog posts, repos. "Extract the idea and reimplement it" means a bad idea
  ("add a little telemetry beacon") can come back as clean code in your own repo.
  Nothing flags it, because it isn't a dependency anymore. It's yours. A human reading
  the diff is the only thing standing in the way.
- **Confident garbage.** Knowing a real technique from a repackaged one is a taste
  call, and an LLM will cheerfully invent a nugget where there isn't one. A person
  catches "this is just `store summaries` with a fancy name." A pipeline won't.
- **Goodhart.** The second a relevance score *gates* an automated loop, the loop
  starts optimizing the score instead of the goal. It gets worse if it also learns
  which phrasings tend to get a yes. Keep a human on the build step and the score
  stays a measurement instead of a target.

So the scout writes a digest, I read it, and I build the ones worth building in a
normal session. I'll only revisit auto-build if I'm actually drowning, meaning more
good ideas land than I can implement by hand. Until that's true, automating the easy
part (writing code) to take on the risk in the hard part (judgment) is a bad deal.

## Adopt the idea, not the dependency

Trendy stuff usually has something real buried in it, so the scout extracts instead of
sneering. It lifts the technique and scores that, not the marketing. But "always
reimplement it yourself" is its own trap. Do that forever and you end up maintaining a
shelf of half-tested clones with nobody watching their CVEs. So every candidate also
gets a buy-vs-build call, and it's allowed to say "just use the upstream, it's better."
Sometimes that's the right answer and the tool should be willing to admit it.

## How it works

```
candidates ─▶ scout ─▶ [extract nugget · map to gap · buy-vs-build · score 1-10] ─▶ digest
                │                                                                     ▲
           open_problems.md  (the scoring anchor: the only gaps that count)           │
                                                                          strict eligibility
```

- The model makes the judgment calls: the nugget, the mapping, the buy-vs-build, the
  per-dimension scores.
- Python computes the composite from those dimension scores, so the number a card
  ranks on is always reproducible from its parts. The model never hands me a final
  score to take on faith.
- A card only makes the digest if it has a real nugget, maps to an actual gap, and
  clears the bar. Everything else lands in a "filtered" section with the reason it got
  cut. Nothing disappears quietly, so if the discriminator breaks I'll see it.

## The eval loop (decoy injection)

The whole thing rests on one claim: the scout can tell a real idea from hype. That's
testable, so I test it. The candidate set has decoys (real buzzwords, no actual
technique) and irrelevant entries (genuinely clever, wrong context, like 10k-QPS
serving for a one-person setup) mixed in with the real ones. A scout that's working
throws all of them out.

```
python -m anton_scout eval
```

It reports decoy catch rate (did it drop the junk?) and real recall (did it keep the
good stuff?), and it exits non-zero if a decoy sneaks into the digest, so it doubles
as a CI gate. The answer key lives in the candidate file as labels, and those get
stripped before the scout sees anything. `load_candidates` and the eval read the file
separately, so the scout never gets handed the labels.

Last run (`--backend cli`, claude CLI, 2026-06-04) over 11 candidates, 6 of them
decoys or irrelevant, including a couple of harder ones: a "metacognition" framework
that's really just sequential prompting, and a Mixture-of-Agents technique that's real
but wrong for a solo setup.

```
decoy catch rate:  1.0   (caught every decoy, including the subtle ones)
real recall:       1.0   (kept every genuine idea)
```

A perfect score only means something if the decoys are hard, so go look at
[`candidates/seed.jsonl`](candidates/seed.jsonl) and add tougher ones. The
deterministic core (composite math, the gate, JSON parsing, label-stripping) has unit
tests under [`tests/`](tests/test_core.py) that run with no model and no network.

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

Backends. `--backend cli` (default) calls the `claude` CLI, which is free if you
already have a subscription and needs no key. `--backend api` uses the Anthropic SDK
and caches the system prompt. `--backend mock` is a dumb keyword stub so you can run
the whole pipeline offline with no auth at all. The mock isn't the real discriminator,
it only catches the obvious cases, so use cli or api for real scoring.

## Layout

| File | Role |
|---|---|
| `anton_scout/scout.py` | extract, map, score; derive the composite in Python |
| `anton_scout/digest.py` | strict eligibility, ranked render |
| `anton_scout/eval.py` | decoy-injection eval loop |
| `anton_scout/llm.py` | swappable `cli` / `api` / `mock` backend |
| `open_problems.md` | the scoring anchor (the target system's real gaps) |
| `candidates/seed.jsonl` | example candidates with labeled decoys |
| `tests/test_core.py` | unit tests for the deterministic core |
| `examples/sample-digest.md` | a real committed run, not hand-edited |

## Status & honest scope

v0.1. What works: extract, map, buy-vs-build, score, the strict-eligibility digest,
the decoy eval (1.0/1.0 on the current 11-candidate set), a unit-tested core, and
three backends. What it isn't, on purpose: it's one batched model call over candidates
you feed in. There's no crawler and no scheduler yet, which is the obvious next thing,
and there's no auto-build, which is the safety boundary from up top rather than a
missing feature. Buy-vs-build is a call the model surfaces for me to decide on, not
something the tool enforces.

Needs Python 3.10+. I built this as a focused project with AI assistance. The design
calls are the point: derive the score instead of trusting it, strip the answer key so
the eval stays honest, and keep a human on the build step.
