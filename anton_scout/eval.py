"""Decoy-injection eval loop.

The scout's whole value rests on one claim: it can tell a real nugget from hype.
That claim is testable. Seed the candidate set with deliberately hollow "trends"
(real buzzwords, zero transferable technique) and genuinely-irrelevant-but-real
techniques (clever, but not for a solo local-first operator). A healthy scout puts
ALL of them in the filtered pile.

Two numbers come out:
  - decoy catch rate: fraction of planted decoys correctly kept OUT of the digest.
    If this is low, the relevance filter is a writing exercise, not a filter.
  - real recall: fraction of genuine candidates correctly kept IN. Guards against
    a scout that "passes" the eval by rejecting everything.

`label` in the candidate file is ground truth and is NEVER shown to the scout
(load_candidates strips it). Labels: "real", "decoy" (hollow), "irrelevant"
(real technique, wrong context).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import digest
from .scout import scout


def _labels(candidates_path) -> dict:
    labels = {}
    for line in Path(candidates_path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        obj = json.loads(line)
        labels[obj["id"]] = obj.get("label", "real")
    return labels


def score(cards: list[dict], labels: dict, *, threshold=digest.DEFAULT_THRESHOLD) -> dict:
    """Score already-produced cards against held-out labels. Pure + deterministic:
    the same computation whether the cards came from a live scout run or a committed
    artifact — so a real run replays offline to the identical numbers."""
    eligible_ids = {c["id"] for c in digest.select_eligible(cards, threshold)}

    should_reject = {i for i, l in labels.items() if l in ("decoy", "irrelevant")}
    should_keep = {i for i, l in labels.items() if l == "real"}

    decoys_caught = {i for i in should_reject if i not in eligible_ids}
    reals_kept = {i for i in should_keep if i in eligible_ids}

    leaked = sorted(should_reject - decoys_caught)      # decoys that slipped INTO the digest
    dropped = sorted(should_keep - reals_kept)          # real ideas wrongly filtered

    return {
        "n_candidates": len(cards),
        "decoy_catch_rate": round(len(decoys_caught) / len(should_reject), 2) if should_reject else None,
        "real_recall": round(len(reals_kept) / len(should_keep), 2) if should_keep else None,
        "leaked_decoys": leaked,
        "dropped_reals": dropped,
        "cards": cards,
    }


def run_eval(open_problems_path, candidates_path, *, backend="cli", model=None,
             threshold=digest.DEFAULT_THRESHOLD, timeout=300, samples=1) -> dict:
    """Run the live scout (optionally with self-consistency over `samples` runs),
    then score its cards against the held-out labels."""
    labels = _labels(candidates_path)
    cards = scout(open_problems_path, candidates_path,
                  backend=backend, model=model, timeout=timeout, samples=samples)
    return score(cards, labels, threshold=threshold)


def save_result(result: dict, save_path, *, meta=None, threshold=digest.DEFAULT_THRESHOLD) -> None:
    """Write the scored cards + metrics to a committed artifact for offline replay."""
    payload = {
        "meta": meta or {},
        "threshold": threshold,
        "metrics": {k: result[k] for k in
                    ("n_candidates", "decoy_catch_rate", "real_recall",
                     "leaked_decoys", "dropped_reals")},
        "cards": result["cards"],
    }
    out = Path(save_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def replay(candidates_path, cards_path, *, threshold=digest.DEFAULT_THRESHOLD) -> dict:
    """Recompute the eval offline from committed cards — no model call. The recorded
    scout outputs are scored against the labels (read fresh from the candidates file)
    by the same `score()`, so a stranger reproduces the numbers with no key."""
    labels = _labels(candidates_path)
    data = json.loads(Path(cards_path).read_text())
    return score(data["cards"], labels, threshold=threshold)


def format_report(result: dict) -> str:
    lines = [
        "Anton Scout — eval report",
        "=" * 32,
        f"candidates:        {result['n_candidates']}",
        f"decoy catch rate:  {result['decoy_catch_rate']}   (1.0 = caught every decoy)",
        f"real recall:       {result['real_recall']}   (1.0 = kept every real idea)",
    ]
    if result["leaked_decoys"]:
        lines.append(f"LEAKED decoys:     {result['leaked_decoys']}  <- discriminator is soft")
    if result["dropped_reals"]:
        lines.append(f"dropped reals:     {result['dropped_reals']}  <- too aggressive")
    if not result["leaked_decoys"] and not result["dropped_reals"]:
        lines.append("clean: every decoy caught, every real idea kept.")
    return "\n".join(lines)
