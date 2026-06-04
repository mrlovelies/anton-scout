"""anton-scout — a discovery scout for emerging AI techniques.

Reads candidate AI techniques, extracts the transferable nugget, maps each to a
target system's open problems, and produces a ranked digest — with an eval loop
(decoy injection) and anti-fabrication guardrails.

It surfaces ideas worth stealing. It does NOT write code, and it does NOT crawl
sources on its own (candidates are fed in). A human picks the winners and
implements them. (See README for why those boundaries are deliberate.)
"""
__version__ = "0.1.0"
