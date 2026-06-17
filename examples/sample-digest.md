# Anton Scout — discovery digest

**8 worth adopting** · 19 filtered · threshold 6.0

## 1. Hardware-aware model autoselection  ·  8.7
**Adopt this:** Estimate per-host tok/s by blending GPU VRAM bandwidth and system-RAM bandwidth weighted by offload fraction, then pick the largest model that clears a target throughput — calibration-checked against measured numbers rather than trusted blindly.
**Hits:** `G1` · **Call:** build · **Confidence:** 0.8
**Scores:** relevance 10 · impact 8 · effort 6
**Why now:** G1 is a hand-maintained table; this is the exact auto-selection mechanism it asks for, and the fleet is heterogeneous enough to benefit immediately.
**First step:** Hardcode the known VRAM/bandwidth specs for each fleet host, write the tok/s estimator, and validate its predictions against 3-4 already-measured model/host pairs before trusting it.
_Bullseye for G1. Build, not buy — it's a small estimator that must encode this specific fleet's hardware; an upstream lib won't know your machines. Calibration-honesty is the part that makes it trustworthy._

## 2. Grammar-constrained decoding for local LLMs  ·  8.35
**Adopt this:** Constrain the sampler to a formal grammar (GBNF / JSON-schema-derived) so emitted tokens are guaranteed to parse — structural validity by construction instead of post-hoc retries.
**Hits:** `G4` · **Call:** buy · **Confidence:** 0.85
**Scores:** relevance 9 · impact 8 · effort 7
**Why now:** G4's core pain (7B models emit invalid structured output) is eliminated, not mitigated, by constrained decoding — and it's already shipping in llama.cpp.
**First step:** Pass a GBNF grammar (or the JSON-schema flag) to the existing llama.cpp endpoint for one structured task and confirm zero parse failures.
_Buy: llama.cpp ships GBNF natively and outlines is maintained — reimplementing a constrained sampler is wasted effort. Pairs with c15 for the cases grammar alone can't enforce (semantic, not just structural, validity)._

## 3. Prompt caching for reused system blocks  ·  8.3
**Adopt this:** Mark the stable system/preamble block as cacheable so repeated runs reuse it instead of re-paying tokens and first-token latency on every call.
**Hits:** `G8` · **Call:** buy · **Confidence:** 0.85
**Scores:** relevance 9 · impact 7 · effort 9
**Why now:** G8 explicitly lists 'no prompt/KV-cache reuse' and 'daily digests burn tokens unbounded' — this is the cheapest direct win, especially on the metered T3 (Claude) tier.
**First step:** Mark the stable system block of the highest-frequency T3 agent as cacheable and confirm cost/TTFT drop on the next digest run.
_Buy/use the provider feature — Claude supports cache_control breakpoints; locally llama.cpp prompt-cache reuses the KV prefix. Near-trivial effort, squarely on G8. Pair with the just-landed usage instrumentation to measure the delta._

## 4. Capability-scoped tool tokens  ·  8.2
**Adopt this:** Issue short-lived tokens that grant only named capabilities (email.read, memory.write) rather than blanket DB access, with an explicit no-bypass doctrine enforced at the tool boundary — least-privilege for agent tool use.
**Hits:** `G3` · **Call:** build · **Confidence:** 0.8
**Scores:** relevance 10 · impact 7 · effort 5
**Why now:** G3 (no scoped agent API) is currently 'everything is an unscoped agent'; this is the capability-gated surface it names, and it doubles as strong G6 portfolio material on agent safety rails.
**First step:** Enumerate the actual capabilities agents use today, then wrap DB/tool access behind a single gate that checks a per-run capability set before any side-effect.
_Build — the capability taxonomy is system-specific. Effort is the catch: retrofitting a gate onto already-unscoped agents touches every call site. Also scores for G6._

## 5. Schema-validated repair for small-model JSON  ·  8.15
**Adopt this:** On schema-validation failure, feed the validator's specific error back to the model for ONE bounded repair pass instead of a blind retry — cheap, targeted structured-output reliability.
**Hits:** `G4` · **Call:** build · **Confidence:** 0.85
**Scores:** relevance 9 · impact 7 · effort 8
**Why now:** Directly on G4, and complements grammar-constrained decoding (c2): grammar guarantees structure, repair handles semantic/schema violations grammar can't express.
**First step:** Wrap one small-model JSON call with schema validation and a single error-fed repair attempt; cap at one retry and log repair rate.
_Build — it's a thin wrapper around your validator. The 'feed the error back, bounded to one pass' is the nugget vs. wasteful blind retries. Best stacked under c2._

## 6. LLM-as-judge eval harness with pairwise rubric  ·  7.0
**Adopt this:** Rubric-driven LLM judging plus pairwise comparison and decoy/holdout controls that detect grader gaming — an offline eval loop that can tell whether a change actually improved outputs.
**Hits:** `G6` · **Call:** build · **Confidence:** 0.8
**Scores:** relevance 8 · impact 6 · effort 6
**Why now:** anton-scout already runs decoy-injection eval; generalizing that into a reusable harness is low marginal effort and prime G6 interview material.
**First step:** Extract the existing decoy/holdout eval into a standalone harness that takes (outputs, rubric) and reports a gaming-resistant score.
_Build — you already have the decoy-injection pattern in-house; the nugget is generalizing it. The decoy/holdout control is the differentiator vs. naive LLM-as-judge._

## 7. KV-cache quantization for longer local context  ·  6.15
**Adopt this:** Quantize the KV cache (e.g. 4-bit) so a model holds more context in the same VRAM, trading a little quality for context headroom on one consumer GPU.
**Hits:** `G8` · **Call:** buy · **Confidence:** 0.75
**Scores:** relevance 6 · impact 6 · effort 7
**Why now:** G8 notes small nodes 'waste context re-sending state'; KV-quant lets those nodes hold more context locally instead, and it's a llama.cpp flag.
**First step:** Enable 4-bit KV-cache quant in llama.cpp on a small-VRAM node and check the longer context holds without unacceptable quality loss on a real task.
_Buy — built into llama.cpp/exllama. Secondary G1 relevance (fits bigger context per host). Quality hit is task-dependent, so validate before standardizing._

## 8. Speculative decoding with a small draft model  ·  6.0
**Adopt this:** A small draft model proposes several tokens that the full model verifies in one forward pass — same output distribution, lower latency under load.
**Hits:** `G4` · **Call:** buy · **Confidence:** 0.8
**Scores:** relevance 6 · impact 6 · effort 6
**Why now:** G4 names timeouts under load; spec-decode cuts local generation latency with identical output, and it's already in llama.cpp/vLLM so adoption is a config change.
**First step:** Enable speculative decoding in llama.cpp with a small draft model paired to the main local model and measure tok/s on a representative structured task.
_Buy — it's a built-in flag, not a build. Helps latency, not token spend; secondary G8 relevance for local throughput. Gains depend on draft/target acceptance rate, so measure._

---

### Filtered out

- **Transactional outbox on SQLite** — below threshold (5.5 < 6.0) (composite 5.5, build)
- **Litestream streaming replication for SQLite** — below threshold (4.95 < 6.0) (composite 4.95, buy)
- **MetaCognition prompt-chaining framework** — below threshold (4.45 < 6.0) (composite 4.45, build)
- **Embedding-based contradiction surfacing** — below threshold (4.3 < 6.0) (composite 4.3, build)
- **Mixture-of-Agents layered ensembling** — below threshold (3.3 < 6.0) (composite 3.3, skip)
- **Disaggregated prefill/decode inference serving** — maps to no listed gap (composite 1.35, skip)
- **Per-query model ensembling for benchmark gains** — maps to no listed gap (composite 1.3, skip)
- **MetaMind recursive metacognition engine** — no real nugget (hollow) (composite 1.15, skip)
- **AutoSwarm AGI Operating System** — no real nugget (hollow) (composite 1.0, skip)
- **On-chain RAG with blockchain prompt provenance** — no real nugget (hollow) (composite 1.0, skip)
- **Multi-region Kubernetes autoscaling for LLM gateways** — maps to no listed gap (composite 1.0, skip)
- **SentientOS self-aware agent kernel** — no real nugget (hollow) (composite 1.0, skip)
- **Decentralized trustless model marketplace** — no real nugget (hollow) (composite 1.0, skip)
- **FounderBot autonomous startup-in-a-box** — no real nugget (hollow) (composite 1.0, skip)
- **PromptDAO on-chain prompt registry** — no real nugget (hollow) (composite 1.0, skip)
- **Multi-region vector index sharding** — maps to no listed gap (composite 1.0, skip)
- **Kubernetes operator for GPU node autoscaling** — maps to no listed gap (composite 1.0, skip)
- **RDMA KV-cache transfer across inference nodes** — maps to no listed gap (composite 1.0, skip)
- **Enterprise rate limiting at 10k QPS** — maps to no listed gap (composite 1.0, skip)
