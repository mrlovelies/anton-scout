"""Replay test for the committed real-run artifact.

WHAT THIS GUARDS: metric-code regressions and tampering with the committed cards
file — if either drifts, the recomputed numbers stop matching the recorded ones
and CI fails, so the README's numbers and the committed artifact can't silently
diverge from the scoring code.

WHAT THIS DOES **NOT** PROVE: that the live scout re-performs. The cards are
recorded model outputs; real-recall varies run-to-run (0.55–0.73 observed) while
decoy-catch is stable at 1.0. Re-proving the model means regenerating with
`eval --backend cli`, which CI can't do offline. The artifact exists so a stranger
can verify the *scoring is honest* (labels stripped, rates correctly derived from
the cards) without a key — not to stand in for the model.
"""
from __future__ import annotations

import json
from pathlib import Path

from anton_scout import eval as eval_mod

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "candidates" / "seed.jsonl"
ARTIFACT = ROOT / "examples" / "real-run-27.json"


def test_committed_run_reproduces():
    recorded = json.loads(ARTIFACT.read_text())["metrics"]
    got = eval_mod.replay(CANDIDATES, ARTIFACT)
    assert got["decoy_catch_rate"] == recorded["decoy_catch_rate"]
    assert got["real_recall"] == recorded["real_recall"]
    assert got["leaked_decoys"] == recorded["leaked_decoys"]
    assert got["dropped_reals"] == recorded["dropped_reals"]


def test_committed_run_leaked_no_decoys():
    # The load-bearing claim: no planted decoy reached the digest in the recorded run.
    got = eval_mod.replay(CANDIDATES, ARTIFACT)
    assert got["decoy_catch_rate"] == 1.0
    assert got["leaked_decoys"] == []
