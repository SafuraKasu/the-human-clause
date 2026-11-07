"""Run the Fatima scenario end to end.

    python -m backend.run_scenario --mode live      # real LLM (needs .env); live responses are cached
    python -m backend.run_scenario --mode mock      # no network: replays cache, otherwise agents fall back

Writes data/runs/<timestamp>-<mode>/{report.md, run.json, audit.jsonl}.
"""
import argparse
import time
from pathlib import Path

from backend import config
from backend.agents.orchestrator import Orchestrator, write_run
from backend.llm.client import LLMClient


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["live", "mock"], default=None, help="default: LLM_MODE from .env")
    ap.add_argument("--out", default=str(config.ROOT / "data" / "runs"))
    ap.add_argument("--no-cache", action="store_true", help="ignore cached responses (live mode)")
    args = ap.parse_args()

    kw = {"mode": args.mode} if args.mode else {}
    llm = LLMClient.from_env(**kw)
    if args.no_cache:
        llm.cache_dir = None
    print(f"mode={llm.mode} model={llm.model} fallback={llm.fallback_model or '-'}")
    run = Orchestrator(llm).run()
    out = write_run(run, Path(args.out) / f"{time.strftime('%Y%m%d-%H%M%S')}-{llm.mode}")
    t = run.totals()
    print(f"\n{t}\nreport: {out / 'report.md'}")
    return 1 if t["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
