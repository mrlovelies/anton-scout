"""CLI: `python -m anton_scout scout|eval`."""
from __future__ import annotations

import argparse
import json
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
    p.add_argument("--samples", type=int, default=1,
                   help="self-consistency: run the model N times and fold the runs "
                        "(median dimension scores, majority votes) to stabilize borderline cards")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="anton_scout")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("scout", help="produce a discovery digest")
    _common(ps)
    ps.add_argument("--out", type=Path, default=None, help="write digest markdown here")
    ps.add_argument("--from-cache", type=Path, default=None,
                    help="render the digest from a committed cards artifact (no model call)")

    pe = sub.add_parser("eval", help="run the decoy-injection eval")
    _common(pe)
    pe.add_argument("--save", type=Path, default=None,
                    help="record real-backend scored cards to a committed artifact")
    pe.add_argument("--from-cache", type=Path, default=None,
                    help="replay saved cards offline (no model) — reproduces the metrics")

    args = ap.parse_args(argv)

    if args.cmd == "scout":
        if args.from_cache is not None:
            cards = json.loads(args.from_cache.read_text())["cards"]
        else:
            cards = scout_mod.scout(args.problems, args.candidates, backend=args.backend,
                                    model=args.model, timeout=args.timeout, samples=args.samples)
        md = digest_mod.render_markdown(cards, args.threshold)
        if args.out:
            args.out.write_text(md)
            print(f"wrote {args.out}")
        else:
            print(md)
        return 0

    if args.cmd == "eval":
        if args.from_cache is not None:
            result = eval_mod.replay(args.candidates, args.from_cache, threshold=args.threshold)
        else:
            result = eval_mod.run_eval(args.problems, args.candidates, backend=args.backend,
                                       model=args.model, threshold=args.threshold,
                                       timeout=args.timeout, samples=args.samples)
            if args.save is not None:
                eval_mod.save_result(result, args.save,
                                     meta={"backend": args.backend, "model": args.model,
                                           "threshold": args.threshold},
                                     threshold=args.threshold)
        print(eval_mod.format_report(result))
        # Non-zero exit if a decoy leaked — makes it CI-friendly.
        return 1 if result["leaked_decoys"] else 0


if __name__ == "__main__":
    sys.exit(main())
