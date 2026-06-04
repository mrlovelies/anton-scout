"""Unit tests for the deterministic core — no model, no network.

These cover the logic the digest's credibility rests on: the composite is derived
(not trusted from the model), the eligibility gate is strict, JSON is parsed
defensively, and the eval's ground-truth label is genuinely stripped before the
scout sees a candidate. Run: `python -m pytest` (or `python tests/test_core.py`).
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # runnable as `pytest` or `python tests/test_core.py`

from anton_scout import digest, llm, scout


def test_composite_is_derived_from_weights():
    assert scout.compute_composite({"relevance": 10, "impact": 10, "effort": 10}) == 10.0
    # 9*.5 + 9*.35 + 8*.15 = 4.5 + 3.15 + 1.2 = 8.85
    assert scout.compute_composite({"relevance": 9, "impact": 9, "effort": 8}) == 8.85


def test_composite_clamps_bad_model_output():
    # out-of-range / missing dims are coerced into [1,10], never crash
    got = scout.compute_composite({"relevance": 99, "impact": 0, "effort": None})
    assert got == round(10 * 0.5 + 1 * 0.35 + 1 * 0.15, 2)


def test_extract_json_handles_fences_and_prose():
    assert scout.extract_json('```json\n[{"a": 1}]\n```') == [{"a": 1}]
    assert scout.extract_json('sure, here: [{"a": 1}] done') == [{"a": 1}]
    assert scout.extract_json("not json at all") is None


def test_eligibility_gate_is_strict():
    cards = [
        {"id": "keep", "is_nugget": True, "mapped_problem": "G1", "composite": 8.0, "confidence": 0.9},
        {"id": "hollow", "is_nugget": False, "mapped_problem": "G1", "composite": 9.0, "confidence": 0.9},
        {"id": "no_gap", "is_nugget": True, "mapped_problem": None, "composite": 9.0, "confidence": 0.9},
        {"id": "low", "is_nugget": True, "mapped_problem": "G2", "composite": 5.0, "confidence": 0.9},
    ]
    assert [c["id"] for c in digest.select_eligible(cards, threshold=6.0)] == ["keep"]


def test_eligible_sorted_by_composite_then_confidence():
    cards = [
        {"id": "lo", "is_nugget": True, "mapped_problem": "G1", "composite": 7.0, "confidence": 0.5},
        {"id": "hi", "is_nugget": True, "mapped_problem": "G1", "composite": 8.0, "confidence": 0.5},
    ]
    assert [c["id"] for c in digest.select_eligible(cards, 6.0)] == ["hi", "lo"]


def test_load_candidates_strips_ground_truth_label():
    # The eval's answer key must never reach the model.
    line = '{"id": "x", "name": "N", "summary": "s", "source": "src", "label": "decoy"}\n'
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        f.write(line)
        path = f.name
    try:
        cands = scout.load_candidates(path)
    finally:
        os.unlink(path)
    assert cands == [{"id": "x", "name": "N", "summary": "s", "source": "src"}]
    assert "label" not in cands[0]


def test_pipeline_runs_offline_with_mock_backend():
    # End-to-end through the mock backend: no auth, no network.
    cards = scout.scout(ROOT / "open_problems.md", ROOT / "candidates" / "seed.jsonl",
                        backend="mock")
    assert len(cards) >= 5
    assert all(isinstance(c["composite"], float) for c in cards)
    # The cartoonish hype decoy is caught even by the crude stub heuristic.
    by_id = {c["id"]: c for c in cards}
    assert by_id["c6"]["is_nugget"] is False


def test_mock_backend_returns_parseable_json_array():
    prompt = "## CANDIDATES\n" + json.dumps([{"id": "c1", "name": "X", "summary": "", "source": ""}])
    data = scout.extract_json(llm.complete(prompt, backend="mock"))
    assert isinstance(data, list) and data[0]["id"] == "c1"


if __name__ == "__main__":
    # Allow running without pytest installed.
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
