# Anton Scout — discovery digest

**5 worth stealing** · 4 filtered · threshold 6.0

## 1. Grammar-constrained decoding for local LLMs  ·  8.85
**Steal this:** Constrain the sampler to a formal grammar (GBNF / JSON-schema-derived) so malformed structured output is impossible by construction, eliminating parse-retry loops and the latency they add under load.
**Hits:** `G4` · **Call:** buy · **Confidence:** 0.88
**Scores:** relevance 9 · impact 9 · effort 8
**Why now:** G4 is exactly unreliable structured output + timeouts on 7B-class models; grammar constraint solves both the validity and the wasted-retry latency.
**First step:** If already on llama.cpp, pass a GBNF grammar (or a JSON-schema-to-GBNF conversion) on one structured-output call path and compare schema-adherence + latency vs the current retry approach.
_Buy, don't build: GBNF ships in llama.cpp and outlines is maintained — a bespoke constrained sampler is a needless reimplementation. Caveat: grammar guarantees syntactic validity, not semantic correctness; constrained decoding can also distort token distributions, so check output quality not just parseability._

## 2. Hardware-aware model autoselection  ·  8.55
**Steal this:** Estimate per-host tok/s by blending GPU VRAM bandwidth with system-RAM bandwidth weighted by offload fraction, then pick the largest model that clears a throughput floor — driven by measured calibration rather than a static spec sheet.
**Hits:** `G1` · **Call:** build · **Confidence:** 0.82
**Scores:** relevance 10 · impact 8 · effort 5
**Why now:** Directly replaces the hand-maintained which-model-on-which-machine table that G1 names as the gap.
**First step:** Microbenchmark tok/s for 2-3 models at known offload fractions on each fleet host, then fit the bandwidth-blend formula against those measured points to check the estimate tracks reality before wiring it into routing.
_Bespoke build is correct: the value is the local calibration data, not the upstream package. Risk is over-trusting the analytic model — keep it calibration-honest as the summary claims; verify the throughput estimate against measured runs._

## 3. Capability-scoped tool tokens  ·  8.2
**Steal this:** Issue agents short-lived tokens that grant only named capabilities (email.read, memory.write) instead of blanket DB access, plus an explicit forbidden-bypass doctrine — least-privilege as a mediated tool surface rather than direct access.
**Hits:** `G3` · **Call:** build · **Confidence:** 0.8
**Scores:** relevance 10 · impact 7 · effort 5
**Why now:** G3 explicitly wants a capability-gated surface; everything currently has unscoped DB access, so this is the missing layer named verbatim.
**First step:** Enumerate the 5-8 capabilities agents actually use today, then put one read path behind a scoped token and prove the unscoped path can be removed without breaking it.
_Build: it's a thin in-stack mediation layer, not a dependency to adopt. Doubles as strong G6 portfolio material (safety rails for autonomous agents). Honest impact caveat for a solo operator — the threat model is mostly self-inflicted agent mistakes, not adversaries, so value is containment/blast-radius, not security-against-attacker._

## 4. LLM-as-judge eval harness (pairwise + anti-gaming)  ·  7.35
**Steal this:** Rubric-driven LLM judging with pairwise comparison plus decoy/holdout controls that detect grader gaming — a reusable offline eval loop you can run without ground-truth labels.
**Hits:** `G6` · **Call:** build · **Confidence:** 0.78
**Scores:** relevance 8 · impact 7 · effort 6
**Why now:** G6 wants demonstrable eval loops; the decoy/holdout anti-gaming controls are the part that makes this credible rather than a naive judge.
**First step:** Stand up a 20-item holdout with known-good/known-bad decoys and confirm the judge ranks them correctly before trusting it on real outputs.
_Build the harness in-stack (it's a pattern, not a product) but reuse a prompt/eval lib for plumbing if convenient. The anti-gaming controls are what elevate this above generic LLM-as-judge; without them it's hollow. Strong portfolio signal._

## 5. Litestream streaming SQLite replication  ·  6.15
**Steal this:** Stream the SQLite WAL continuously to a replica/object store for point-in-time recovery, and lean on that to enforce a single-writer discipline without swapping the database engine.
**Hits:** `G2` · **Call:** buy · **Confidence:** 0.62
**Scores:** relevance 6 · impact 6 · effort 7
**Why now:** G2 wants safer replication without a heavy migration, and Litestream is the canonical low-friction answer.
**First step:** Point Litestream at the DB on the one machine designated as writer and restore from the replica on a throwaway host to confirm PITR works end-to-end.
_Buy — a maintained tool with a real test suite beats a bespoke WAL shipper. But partial fit: Litestream gives recovery + a single-writer story, it does NOT reconcile concurrent multi-writer writes, which is the actual clobber risk in G2. It also runs as an always-on process, brushing the no-new-daemons anti-goal. It de-risks G2 rather than fully solving it; the real fix is writer discipline._

---

### Filtered out

- **Disaggregated prefill/decode inference serving** — maps to no listed gap (composite 1.35, skip)
- **AutoSwarm AGI Operating System** — no real nugget (hollow) (composite 1.0, skip)
- **On-chain RAG with blockchain prompt provenance** — no real nugget (hollow) (composite 1.0, skip)
- **Multi-region Kubernetes autoscaling for LLM gateways** — maps to no listed gap (composite 1.0, skip)
