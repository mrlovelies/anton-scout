"""CLI: `python -m anton_scout scout|eval`."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import digest as digest_mod
from . import eval as eval_mod
from . import scout as scout_mod

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROBLEMS = ROOT / "open_problems.md"
DEFAULT_CANDIDATES = ROOT / "candidates" / "seed.jsonl"


def _common(p):
    p.add_argument("--problems", type=Path, default=DEFAULT_PROBLEMS,
                   help="open-problems doc (scoring anchor)")
    p.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES,
                   help="candidates JSONL")
    p.add_argument("--backend", choices=["cli", "api", "mock"], default="cli",
                   help="cli=claude CLI (free), api=Anthropic SDK, mock=offline stub")
    p.add_argument("--model", default=None)
    p.add_argument("--threshold", type=float, default=digest_mod.DEFAULT_THRESHOLD)
    p.add_argument("--timeout", type=int, default=300)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="anton_scout")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("scout", help="produce a discovery digest")
    _common(ps)
    ps.add_argument("--out", type=Path, default=None, help="write digest markdown here")

    pe = sub.add_parser("eval", help="run the decoy-injection eval")
    _common(pe)

    args = ap.parse_args(argv)

    if args.cmd == "scout":
        cards = scout_mod.scout(args.problems, args.candidates, backend=args.backend,
                                model=args.model, timeout=args.timeout)
        md = digest_mod.render_markdown(cards, args.threshold)
        if args.out:
            args.out.write_text(md)
            print(f"wrote {args.out}")
        else:
            print(md)
        return 0

    if args.cmd == "eval":
        result = eval_mod.run_eval(args.problems, args.candidates, backend=args.backend,
                                   model=args.model, threshold=args.threshold,
                                   timeout=args.timeout)
        print(eval_mod.format_report(result))
        # Non-zero exit if a decoy leaked — makes it CI-friendly.
        return 1 if result["leaked_decoys"] else 0


if __name__ == "__main__":
    sys.exit(main())
