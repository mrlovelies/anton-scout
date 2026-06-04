"""Thin LLM layer with two swappable backends.

- `cli`  (default): shells out to the `claude` CLI in headless mode (`claude -p`).
          Free on an existing Claude subscription; no API key needed.
- `api`:  uses the Anthropic SDK (needs ANTHROPIC_API_KEY). Caches the system
          block so repeated runs are cheaper.

Keeping the call behind one interface means the scout doesn't care which one it
is, and the backend is a one-line swap.
"""
from __future__ import annotations

import shutil
import subprocess


class LLMError(RuntimeError):
    pass


def complete(prompt: str, system: str | None = None, *, backend: str = "cli",
             model: str | None = None, timeout: int = 300) -> str:
    """Return the model's text completion for `prompt`."""
    if backend == "api":
        return _complete_api(prompt, system, model, timeout)
    if backend == "cli":
        return _complete_cli(prompt, system, model, timeout)
    if backend == "mock":
        return _complete_mock(prompt)
    raise LLMError(f"unknown backend: {backend!r} (use 'cli', 'api', or 'mock')")


def _complete_cli(prompt: str, system: str | None, model: str | None, timeout: int) -> str:
    claude = shutil.which("claude")
    if not claude:
        raise LLMError("`claude` CLI not found in PATH — install it or use --backend api")
    # The headless CLI takes a single prompt; fold the system preamble in.
    full = prompt if not system else f"{system}\n\n---\n\n{prompt}"
    cmd = [claude, "-p", full]
    if model:
        cmd += ["--model", model]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise LLMError(f"claude CLI timed out after {timeout}s") from e
    if r.returncode != 0:
        raise LLMError(f"claude CLI exited {r.returncode}: {(r.stderr or '')[-400:]}")
    return (r.stdout or "").strip()


def _complete_api(prompt: str, system: str | None, model: str | None, timeout: int) -> str:
    try:
        import anthropic
    except ImportError as e:
        raise LLMError("anthropic SDK not installed (`pip install anthropic`) "
                       "— or use --backend cli") from e
    client = anthropic.Anthropic()
    kwargs: dict = {
        "model": model or "claude-sonnet-4-6",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        # Cache the (stable) system block across runs — it's the big, reused part.
        kwargs["system"] = [{"type": "text", "text": system,
                             "cache_control": {"type": "ephemeral"}}]
    msg = client.messages.create(**kwargs)
    return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text").strip()


# --- Mock backend -----------------------------------------------------------
#
# A crude, deterministic keyword stub so the pipeline runs offline (no auth, no
# network) for demos and tests. It is NOT the discriminator — it only catches the
# obvious cases. Real scoring quality comes from the cli/api backends; the
# committed example digest and the README's eval numbers are from a real model run.

import json as _json

_HYPE = ("agi", "blockchain", "nft", "web3", "on-chain", "trustless", "revolutionary",
         "waitlist", "replace your", "self-aware", "metacognition", "series a", "series-a")
_SCALE = ("qps", "multi-region", "multi-tenant", "kubernetes", "rdma", "10k", "enterprise",
          "per query", "ensembl")
_GAP_HINTS = [
    (("route", "fleet", "model select", "autoselect", "tok/s", "vram"), "G1"),
    (("sqlite", "replicat", "wal", "writer"), "G2"),
    (("scope", "capabilit", "token", "least-privilege", "permission"), "G3"),
    (("structured", "grammar", "decod", "schema", "json"), "G4"),
    (("eval", "judge", "rubric", "agent", "safety"), "G6"),
]


def _complete_mock(prompt: str) -> str:
    i = prompt.find("## CANDIDATES")
    start = prompt.find("[", i if i != -1 else 0)
    candidates, _ = _json.JSONDecoder().raw_decode(prompt[start:])
    out = []
    for c in candidates:
        text = f"{c.get('name', '')} {c.get('summary', '')}".lower()
        if any(h in text for h in _HYPE):
            out.append(_card(c, is_nugget=False, gap=None, r=1, im=1, ef=5,
                             call="skip", note="mock: hollow hype, no transferable nugget"))
        elif any(s in text for s in _SCALE):
            out.append(_card(c, is_nugget=True, gap=None, r=2, im=5, ef=5,
                             call="skip", note="mock: real technique, wrong context (scale-only)"))
        else:
            gap = next((g for hints, g in _GAP_HINTS if any(h in text for h in hints)), "G1")
            out.append(_card(c, is_nugget=True, gap=gap, r=8, im=7, ef=6,
                             call="build", note="mock stub card — run cli/api for real scoring"))
    return _json.dumps(out)


def _card(c, *, is_nugget, gap, r, im, ef, call, note):
    return {
        "id": c["id"], "name": c.get("name", "?"),
        "is_nugget": is_nugget, "nugget": (c.get("summary", "")[:120] if is_nugget else None),
        "mapped_problem": gap, "buy_vs_build": call,
        "scores": {"relevance": r, "impact": im, "effort": ef},
        "confidence": 0.5, "why_now": "", "first_step": "", "notes": note,
    }
