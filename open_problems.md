# Open Problems — the scout's scoring anchor

The scout maps every candidate technique to one of these gaps, or downranks it.
Novelty alone is never enough. The target is a **solo, local-first AI platform**:
one operator, a heterogeneous local GPU fleet, no team, no cloud-scale traffic.
Relevance is judged for *that* operator — techniques that only pay off at large
scale or for a team are not relevant here.

## Governing principle: adopt the idea, not the dependency (with a release valve)

Trendy frameworks usually have *some* real nugget worth extracting. So the scout is
an **extractor, not a rejecter**: it lifts the transferable technique and scores
*that*, not the framework's hype. But "reimplement it in-stack" must not be a
ratchet — every candidate gets an explicit **buy-vs-build** call that is allowed to
say *"just adopt the upstream."* Sometimes the maintained dependency, with its test
suite and CVE feed, beats a bespoke clone.

## Gaps

- **G1 — Fleet model-routing is hand-maintained.** Which local model runs on which
  machine is a manual table. Hardware-aware auto-selection (VRAM/bandwidth → tok/s)
  would pick the right model per host automatically.
- **G2 — Multi-writer SQLite risk.** A single SQLite DB syncs across several
  machines; concurrent writes can clobber. Want safer replication / single-writer
  discipline without a heavy database migration.
- **G3 — No scoped agent API.** Everything is an agent with direct, unscoped DB
  access. A capability-gated surface (least-privilege tool tokens) is unbuilt.
- **G4 — Local small-model structured output.** Small local models (7B-class) are
  unreliable at emitting valid structured output and time out under load. Want
  higher schema-adherence and lower latency.
- **G5 — Personal-vs-shippable drift.** Tension between local personal
  customizations and the clean, shippable version of the platform causes repo drift.
- **G6 — AI-engineering portfolio signal.** Techniques worth demonstrating as
  portfolio/interview material: agent architectures, eval loops, retrieval, and
  safety rails for autonomous systems.
- **G7 — Creative tooling.** Improvements to the operator's domain tools (audio /
  audition workflow): recording, processing, structured export.

## Anti-goals (auto-downrank; never the recommendation)

Narrowed to the genuinely costly part — *framework-as-dependency, not
framework-as-teacher*:

- Wholesale dependency adoption to replace a working subsystem.
- New always-on services / daemons on a stable daily-driver.
- Bleeding-edge deps that add upgrade / supply-chain surface for marginal gain.
- Scale-only techniques (high-QPS, multi-tenant, multi-region) — wrong context.
- Anything that turns a stable daily-driver into a thrashing science project.
