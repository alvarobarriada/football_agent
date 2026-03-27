"""Quality Gate: Evaluate a prompt version before promotion.

This is the quality gate in the Prompt CI/CD pipeline.
It runs the evaluation suite against a prompt label and exits with
code 0 (pass) or 1 (fail) based on the threshold.

Usage:
    python -m techshop_agent.cicd.evaluate_prompt --label staging
    python -m techshop_agent.cicd.evaluate_prompt --label staging --threshold 0.8

How it works:
    1. Fetches the prompt for the given label from Langfuse
    2. Runs the TechShop agent with that prompt against the eval dataset
    3. Applies scope adherence, hallucination, and quality evaluators
    4. Checks if all average scores meet the threshold
    5. Returns exit code 0 (pass) or 1 (fail) for CI/CD

This script calls techshop_agent.evaluation.run_evaluation() which uses
Langfuse's run_experiment API. All results are automatically tracked in
Langfuse for comparison across runs.

Reference: https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from dotenv import find_dotenv, load_dotenv


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate a prompt label (quality gate for CI/CD)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m techshop_agent.cicd.evaluate_prompt --label staging
  python -m techshop_agent.cicd.evaluate_prompt --label staging --threshold 0.8
  python -m techshop_agent.cicd.evaluate_prompt --label staging --json
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
        help="Minimum score for quality gate (default: 0.7)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output JSON results",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    load_dotenv(find_dotenv(usecwd=True))

    from techshop_agent.evaluation import run_evaluation

    print(f"\n🔍 Quality Gate — evaluating label: {args.label}")
    print(f"   Threshold: {args.threshold:.0%}\n")

    result = run_evaluation(label=args.label, threshold=args.threshold)

    if args.output_json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.summary())

    if result.passes_threshold(args.threshold):
        print("\n✅ Quality gate PASSED — prompt is ready for promotion")
        sys.exit(0)
    else:
        print("\n❌ Quality gate FAILED — prompt needs improvement")
        sys.exit(1)


if __name__ == "__main__":
    main()
