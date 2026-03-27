"""CLI entry point: python -m techshop_agent.evaluation"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from .runner import run_evaluation


def main() -> None:
    """CLI entry point for running evaluations."""
    parser = argparse.ArgumentParser(
        description="Run TechShop Agent evaluation suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m techshop_agent.evaluation --label staging
  python -m techshop_agent.evaluation --label staging --threshold 0.8
  python -m techshop_agent.evaluation --label production --json
        """,
    )
    parser.add_argument(
        "--label",
        default="staging",
        help="Langfuse prompt label to evaluate (default: staging)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Minimum score threshold for quality gate (default: 0.7)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output results as JSON instead of human-readable",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Load environment
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv(usecwd=True))

    print(f"\n🧪 Running evaluation against label: {args.label}")
    print(f"   Threshold: {args.threshold:.0%}\n")

    result = run_evaluation(label=args.label, threshold=args.threshold)

    if args.output_json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.summary())

    # Exit with appropriate code for CI/CD
    sys.exit(0 if result.passes_threshold(args.threshold) else 1)


if __name__ == "__main__":
    main()
