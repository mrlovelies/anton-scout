"""Turn scored cards into a ranked digest.

Eligibility is deliberately strict: a card only reaches the digest if it has a
real nugget, maps to an actual gap, and clears the composite threshold. Everything
else goes to a visible "filtered" section — nothing is silently dropped, so you can
see what the scout rejected and why (this is where you catch a broken discriminator).
"""
from __future__ import annotations

DEFAULT_THRESHOLD = 6.0


def select_eligible(cards: list[dict], threshold: float = DEFAULT_THRESHOLD) -> list[dict]:
    """The cards that make the digest, best first."""
    keep = [
        c for c in cards
        if c["is_nugget"] and c["mapped_problem"] and c["composite"] >= threshold
    ]
    return sorted(keep, key=lambda c: (c["composite"], c["confidence"]), reverse=True)


def filtered_out(cards: list[dict], threshold: float = DEFAULT_THRESHOLD) -> list[dict]:
    eligible = {id(c) for c in select_eligible(cards, threshold)}
    return [c for c in cards if id(c) not in eligible]


def _reason(card: dict, threshold: float) -> str:
    if not card["is_nugget"]:
        return "no real nugget (hollow)"
    if not card["mapped_problem"]:
        return "maps to no listed gap"
    if card["composite"] < threshold:
        return f"below threshold ({card['composite']} < {threshold})"
    return "—"


def render_markdown(cards: list[dict], threshold: float = DEFAULT_THRESHOLD) -> str:
    eligible = select_eligible(cards, threshold)
    rejected = filtered_out(cards, threshold)

    out = ["# Anton Scout — discovery digest", ""]
    out.append(f"**{len(eligible)} worth stealing** · {len(rejected)} filtered · "
               f"threshold {threshold}")
    out.append("")

    if not eligible:
        out.append("_Nothing cleared the bar this run._")
    for i, c in enumerate(eligible, 1):
        s = c["scores"]
        out += [
            f"## {i}. {c['name']}  ·  {c['composite']}",
            f"**Steal this:** {c['nugget']}",
            f"**Hits:** `{c['mapped_problem']}` · **Call:** {c['buy_vs_build']} · "
            f"**Confidence:** {c['confidence']}",
            f"**Scores:** relevance {s['relevance']} · impact {s['impact']} · "
            f"effort {s['effort']}",
            f"**Why now:** {c['why_now'] or '—'}",
            f"**First step:** {c['first_step'] or '—'}",
        ]
        if c["notes"]:
            out.append(f"_{c['notes']}_")
        out.append("")

    out += ["---", "", "### Filtered out", ""]
    if not rejected:
        out.append("_(none)_")
    for c in sorted(rejected, key=lambda c: c["composite"], reverse=True):
        out.append(f"- **{c['name']}** — {_reason(c, threshold)} "
                   f"(composite {c['composite']}, {c['buy_vs_build']})")
    out.append("")
    return "\n".join(out)
