# Anton Scout — discovery digest

**8 worth adopting** · 19 filtered · threshold 6.0

## 1. Hardware-aware model autoselection  ·  8.7
**Adopt this:** Estimate per-host tok/s by blending GPU VRAM bandwidth and system-RAM bandwidth weighted by the offload fraction, then pick the largest model that clears a target throughput — calibrated against real measurements, not spec sheets.
**Hits:** `G1` · **Call:** build · **Confidence:** 0.82
**Scores:** relevance 10 · impact 8 · effort 6
**Why now:** G1's which-model-on-which-host table is hand-maintained; this is the exact automation it's missing.
**First step:** Benchmark 2-3 models per host to calibrate the bandwidth→tok/s estimator, then compare predictions to the current manual table.
_Bullseye for G1. Build in-stack: it's a small estimator, not a framework. Calibration honesty is the whole value — don't trust the model without per-host measurement._

## 2. Capability-scoped tool tokens  ·  8.55
**Adopt this:** Issue short-lived tokens that grant only named capabilities (email.read, memory.write) and gate every tool/DB access behind a capability check, with an explicit no-bypass doctrine — least-privilege for agents.
**Hits:** `G3` · **Call:** build · **Confidence:** 0.78
**Scores:** relevance 10 · impact 8 · effort 5
**Why now:** G3 is wholly unbuilt — every agent has unscoped DB access today; this is the only candidate that addresses it.
**First step:** Define a capability enum and route one agent's DB access through a token-checked wrapper before generalizing.
_Build: it's a thin in-stack layer, not a dependency. Doubles as strong G6 portfolio material (safety rails for autonomous agents)._

## 3. Prompt caching for reused system blocks  ·  8.5
**Adopt this:** Mark the stable system/preamble block as cacheable so repeated runs reuse it instead of re-paying first-token cost — KV reuse locally, native prompt cache on metered APIs.
**Hits:** `G8` · **Call:** buy · **Confidence:** 0.85
**Scores:** relevance 9 · impact 8 · effort 8
**Why now:** Usage instrumentation just landed with no baseline — this is the cheapest, highest-leverage token cut to measure first.
**First step:** Mark the stable system preamble cacheable on the T3 Claude path and enable KV reuse for the reused local preamble.
_Buy on the Claude side (native prompt caching); trivially build local KV reuse. Small local nodes 're-sending state' (per G8) is exactly what this kills._

## 4. Grammar-constrained decoding for local LLMs  ·  8.35
**Adopt this:** Constrain the sampler to a formal grammar (GBNF / JSON-schema-derived) so malformed output is structurally impossible — eliminates the parse-retry loop entirely rather than mitigating it.
**Hits:** `G4` · **Call:** buy · **Confidence:** 0.85
**Scores:** relevance 9 · impact 8 · effort 7
**Why now:** G4 is the single most direct hit; grammar constraint is the strongest known fix for small-model structured output.
**First step:** Convert the target JSON schema to GBNF and pass it to the existing llama.cpp server's grammar param on one structured endpoint; measure parse-failure rate before/after.
_Buy: GBNF ships in llama.cpp and outlines is maintained — reimplementing a grammar-constrained sampler is a major project with no upside. Pairs with c15 for fields a grammar can't fully constrain (semantics)._

## 5. Schema-validated repair for small-model JSON  ·  8.15
**Adopt this:** On schema-validation failure, feed the exact validator error back for one bounded repair pass instead of a blind retry — cheap, targeted structured-output reliability.
**Hits:** `G4` · **Call:** build · **Confidence:** 0.85
**Scores:** relevance 9 · impact 7 · effort 8
**Why now:** Direct G4 hit and near-trivial to add; catches the semantic/field errors a grammar (c2) can't, at the cost of at most one extra call.
**First step:** Wrap the structured-output call: validate against the schema, and on failure issue one repair prompt containing the validator's error message; cap at a single repair.
_Build: ~30 lines around an existing validator. Best paired with c2 (grammar guarantees parse; repair fixes semantics). Bound the repair to one pass so it never becomes an unbounded retry loop (also a G8 concern)._

## 6. LLM-as-judge eval harness with pairwise rubric  ·  7.0
**Adopt this:** Rubric-driven LLM judging plus pairwise comparison and decoy/holdout controls to catch grader gaming — an offline eval loop with built-in anti-gaming validity checks.
**Hits:** `G6` · **Call:** build · **Confidence:** 0.8
**Scores:** relevance 8 · impact 6 · effort 6
**Why now:** G6 wants demonstrable eval loops; anton-scout already runs decoy-injection eval, so this is directly on-mission and extends existing work.
**First step:** Add a pairwise mode to the existing decoy eval so two candidate outputs are judged head-to-head against the rubric, not just scored absolutely.
_Build: the harness already exists in-repo; this is an incremental extension, not a new dependency. Decoy/holdout control is the part that gives the eval credibility._

## 7. KV-cache quantization for longer local context  ·  6.15
**Adopt this:** Quantize the KV cache (e.g. 4-bit) so a model holds longer context in the same VRAM, trading a little quality for headroom on a single consumer GPU.
**Hits:** `G8` · **Call:** buy · **Confidence:** 0.72
**Scores:** relevance 6 · impact 6 · effort 7
**Why now:** More usable context on existing consumer GPUs without buying hardware — relieves the context-pressure side of G8/G1.
**First step:** Enable 4-bit KV-cache quant in llama.cpp on the longest-context node and measure the quality delta.
_Buy: it's a built-in flag. It's VRAM headroom, not token-count reduction — adjacent to G8's context goal and to G1 fit, not a direct cost cut._

## 8. Speculative decoding with a small draft model  ·  6.0
**Adopt this:** A small draft model proposes several tokens that the full model verifies in one forward pass — lower latency, bit-identical output.
**Hits:** `G4` · **Call:** buy · **Confidence:** 0.78
**Scores:** relevance 6 · impact 6 · effort 6
**Why now:** Free latency win that helps small models meet timeouts under load (the latency half of G4).
**First step:** Enable speculative decoding in llama.cpp/vLLM with a small draft model on one host and measure tok/s.
_Buy: built into llama.cpp/vLLM. Cuts latency, not token cost or schema-adherence — so it eases G4 timeouts but isn't a structured-output fix._

---

### Filtered out

- **Transactional outbox on SQLite** — below threshold (5.15 < 6.0) (composite 5.15, build)
- **Embedding-based contradiction surfacing** — below threshold (5.15 < 6.0) (composite 5.15, build)
- **MetaCognition prompt-chaining** — below threshold (4.45 < 6.0) (composite 4.45, build)
- **Litestream streaming replication for SQLite** — below threshold (4.1 < 6.0) (composite 4.1, buy)
- **Mixture-of-Agents ensembling** — maps to no listed gap (composite 2.65, skip)
- **MetaMind recursive metacognition engine** — no real nugget (hollow) (composite 2.3, skip)
- **Per-query model ensembling for benchmark gains** — maps to no listed gap (composite 2.3, skip)
- **Enterprise rate limiting at 10k QPS** — maps to no listed gap (composite 2.15, skip)
- **Disaggregated prefill/decode inference serving** — maps to no listed gap (composite 1.5, skip)
- **Multi-region Kubernetes autoscaling for LLM gateways** — maps to no listed gap (composite 1.15, skip)
- **Multi-region vector index sharding** — maps to no listed gap (composite 1.15, skip)
- **Kubernetes operator for GPU node autoscaling** — maps to no listed gap (composite 1.15, skip)
- **AutoSwarm AGI Operating System** — no real nugget (hollow) (composite 1.0, skip)
- **On-chain RAG with blockchain prompt provenance** — no real nugget (hollow) (composite 1.0, skip)
- **SentientOS self-aware agent kernel** — no real nugget (hollow) (composite 1.0, skip)
- **Decentralized trustless model marketplace** — no real nugget (hollow) (composite 1.0, skip)
- **FounderBot autonomous startup-in-a-box** — no real nugget (hollow) (composite 1.0, skip)
- **PromptDAO on-chain prompt registry** — no real nugget (hollow) (composite 1.0, skip)
- **RDMA KV-cache transfer across inference nodes** — maps to no listed gap (composite 1.0, skip)
