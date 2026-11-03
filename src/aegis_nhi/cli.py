"""Local scenario CLI: print evidence report or export JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .workflow import load_case, run_case


def main() -> None:
    parser = argparse.ArgumentParser(description="AEGIS-NHI synthetic incident investigation")
    parser.add_argument(
        "--scenario", default="data/scenarios/unauthorized_ai_agent.json"
    )
    parser.add_argument("--output", help="Optional JSON output path")
    parser.add_argument("--frequency-multiplier", type=float, default=1.0)
    parser.add_argument("--control-effectiveness", type=float, default=0.0)
    args = parser.parse_args()
    report = run_case(
        load_case(args.scenario),
        frequency_multiplier=args.frequency_multiplier,
        hypothetical_control_effectiveness=args.control_effectiveness,
    )
    content = json.dumps(report, indent=2) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"Written synthetic evidence report: {target}")
    else:
        print(content)


if __name__ == "__main__":
    main()
