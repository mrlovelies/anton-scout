"""Unit tests for the self-consistency aggregation (anton_scout.scout.aggregate).

Deterministic, no model, no network: feed synthetic per-run cards and check the
fold is median-on-scores / majority-on-votes, the composite is re-derived (not
trusted), and eligible_votes correctly counts how many runs would have kept each
candidate — the signal that keeps borderline candidates visible.
"""
from __future__ import annotations

from anton_scout.scout import aggregate, compute_composite


def _card(cid, rel, imp, eff, *, is_nugget=True, mapped="G1", confidence=0.7):
    scores = {"relevance": rel, "impact": imp, "effort": eff}
    return {
        "id": cid, "name": cid, "is_nugget": is_nugget, "nugget": "n",
        "mapped_problem": mapped, "buy_vs_build": "build", "scores": scores,
        "composite": compute_composite(scores), "confidence": confidence,
        "why_now": "", "first_step": "", "notes": "",
    }


def test_median_scores_rederived_composite_and_votes():
    runs = [[_card("x", 6, 6, 6)], [_card("x", 4, 4, 4)], [_card("x", 8, 8, 8)]]
    agg = {c["id"]: c for c in aggregate(runs)}["x"]
    assert agg["scores"] == {"relevance": 6, "impact": 6, "effort": 6}  # median of 4/6/8
    assert agg["composite"] == 6.0                                       # re-derived from medians
    assert agg["is_nugget"] is True
    assert agg["mapped_problem"] == "G1"
    # eligible at threshold 6.0 in runs with composite 6.0 and 8.0, not 4.0 -> 2 of 3
    assert agg["samples"] == {"n": 3, "eligible_votes": 2}


def test_majority_vote_flips_nugget():
    runs = [
        [_card("y", 8, 8, 8, is_nugget=False)],
        [_card("y", 8, 8, 8, is_nugget=False)],
        [_card("y", 8, 8, 8, is_nugget=True)],
    ]
    agg = {c["id"]: c for c in aggregate(runs)}["y"]
    assert agg["is_nugget"] is False              # 2 of 3 say not-a-nugget
    assert agg["samples"]["eligible_votes"] == 1  # only the one is_nugget=True run counts


def test_mode_mapping_handles_null():
    runs = [
        [_card("z", 7, 7, 7, mapped="G2")],
        [_card("z", 7, 7, 7, mapped="G2")],
        [_card("z", 7, 7, 7, mapped=None)],
    ]
    agg = {c["id"]: c for c in aggregate(runs)}["z"]
    assert agg["mapped_problem"] == "G2"
