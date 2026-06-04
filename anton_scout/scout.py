"""The scout core: candidates + open-problems -> scored, ranked cards.

The model does the judgment (extract the nugget, map it to a gap, buy-vs-build,
score the dimensions). Python does the arithmetic (the composite is DERIVED from
the dimension scores, never trusted from the model) — so a card's headline number
is always reproducible from its parts.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import llm

# Composite weights. Relevance dominates on purpose: a brilliant technique that
# doesn't hit a real gap is noise. Effort is lightly weighted and inverted
# (10 = trivial to implement).
WEIGHTS = {"relevance": 0.5, "impact": 0.35, "effort": 0.15}

SYSTEM = """\
You are a discovery scout. Your job is to find IDEAS WORTH ADOPTING for a specific
target system, and to be ruthlessly honest about which candidates are hollow.

You are given (1) the target system's OPEN-PROBLEMS doc — the only things it wants
to get better at — and (2) a list of candidate AI techniques/tools/repos. For EACH
candidate, do this:

1. EXTRACT THE NUGGET. What is the transferable *technique* underneath the candidate
   — the thing that could be reimplemented independently of the candidate's specific
   framework/package? If there is no real transferable technique (it's hype,
   buzzword soup, a repackaging of something obvious, or a VC narrative), set
   "is_nugget": false and DO NOT invent one. Fabricating a nugget is the worst
   thing you can do here.

2. MAP IT TO A GAP. Which open problem (by its Gn id) does the nugget actually
   address? If it maps to none of the listed gaps, set "mapped_problem": null —
   even if the technique is genuinely clever. Relevance is judged FOR THIS SYSTEM:
   it is a solo, local-first operator. A technique that only matters at large scale
   / for a team / for high QPS is NOT relevant here; score its relevance low.

3. BUY VS BUILD. Decide honestly: "build" (reimplement the technique in-stack),
   "buy" (just adopt the upstream dependency — sometimes that IS the right call),
   or "skip". You are explicitly allowed and encouraged to say "buy" when the
   maintained upstream clearly beats a bespoke reimplementation.

4. SCORE each dimension 1-10:
   - relevance: how directly the nugget hits a listed gap FOR THIS operator.
   - impact: how much it would improve the system if adopted.
   - effort: how easy to implement (10 = trivial, 1 = a major project).

5. CONFIDENCE 0.0-1.0: your confidence that this is a real, correctly-understood
   nugget (not a confident guess). Low confidence is fine and useful — say so.

Output ONLY a JSON array (no prose, no markdown fences). One object per candidate,
in the same order, each shaped exactly:
{
  "id": "<candidate id>",
  "name": "<short name>",
  "is_nugget": true|false,
  "nugget": "<the transferable technique, or null>",
  "mapped_problem": "G3"|null,
  "buy_vs_build": "build"|"buy"|"skip",
  "scores": {"relevance": N, "impact": N, "effort": N},
  "confidence": 0.0-1.0,
  "why_now": "<one line: why this is worth attention now, or '' if not>",
  "first_step": "<one concrete first step a human would take, or '' if skip>",
  "notes": "<terse: e.g. why it's hollow, or the buy-vs-build reasoning>"
}
"""


def _clamp(v, lo=1, hi=10, default=1):
    try:
        return max(lo, min(hi, int(round(float(v)))))
    except (TypeError, ValueError):
        return default


def compute_composite(scores: dict) -> float:
    """Derive the composite from dimension scores. Pure arithmetic, no model trust."""
    return round(sum(_clamp(scores.get(k)) * w for k, w in WEIGHTS.items()), 2)


def extract_json(text: str):
    """Pull a JSON array out of model output (handles fences / leading prose)."""
    if not text:
        return None
    t = text.strip()
    if "```" in t:
        m = re.search(r"```(?:json)?\s*(.*?)```", t, re.DOTALL)
        if m:
            t = m.group(1).strip()
    start, end = t.find("["), t.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(t[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None


def load_candidates(path) -> list[dict]:
    """Load candidates, exposing ONLY the fields the scout should see.

    Any eval-only ground-truth label (e.g. "label": "decoy") is deliberately
    stripped here so the scout never sees the answer key.
    """
    cands = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        obj = json.loads(line)
        cands.append({
            "id": obj["id"],
            "name": obj["name"],
            "summary": obj.get("summary", ""),
            "source": obj.get("source", ""),
        })
    return cands


def _build_prompt(open_problems: str, candidates: list[dict]) -> str:
    lines = [
        "## TARGET SYSTEM — OPEN PROBLEMS",
        open_problems.strip(),
        "",
        "## CANDIDATES",
        json.dumps(candidates, indent=2),
        "",
        f"Return a JSON array of exactly {len(candidates)} objects, one per candidate, "
        "in order.",
    ]
    return "\n".join(lines)


def scout(open_problems_path, candidates_path, *, backend="cli", model=None,
          timeout=300) -> list[dict]:
    open_problems = Path(open_problems_path).read_text()
    candidates = load_candidates(candidates_path)
    prompt = _build_prompt(open_problems, candidates)

    raw = llm.complete(prompt, system=SYSTEM, backend=backend, model=model, timeout=timeout)
    data = extract_json(raw)
    if data is None:
        raise ValueError(f"could not parse JSON array from model output:\n{raw[:500]}")

    by_id = {c["id"]: c for c in candidates}
    cards = []
    for item in data:
        cid = item.get("id")
        scores = item.get("scores", {}) or {}
        norm = {k: _clamp(scores.get(k)) for k in WEIGHTS}
        cards.append({
            "id": cid,
            "name": item.get("name") or (by_id.get(cid, {}).get("name", "?")),
            "is_nugget": bool(item.get("is_nugget")),
            "nugget": item.get("nugget"),
            "mapped_problem": item.get("mapped_problem"),
            "buy_vs_build": item.get("buy_vs_build", "skip"),
            "scores": norm,
            "composite": compute_composite(norm),
            "confidence": _confidence(item.get("confidence")),
            "why_now": item.get("why_now", ""),
            "first_step": item.get("first_step", ""),
            "notes": item.get("notes", ""),
        })
    return cards


def _confidence(v):
    try:
        return round(max(0.0, min(1.0, float(v))), 2)
    except (TypeError, ValueError):
        return 0.0
