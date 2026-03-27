"""CI script: Push a prompt version to Langfuse.

This is the "CI" part of the Prompt CI/CD pipeline.
It reads a prompt file and creates a new immutable version in Langfuse
with the specified labels.

Usage:
    python -m techshop_agent.cicd.push_prompt \\
        --file prompts/system_prompt.txt \\
        --labels staging latest

    python -m techshop_agent.cicd.push_prompt \\
        --content "Eres Alex, asistente de TechShop..." \\
        --labels staging

How it works:
    1. Reads the prompt content from a file or --content argument
    2. Connects to Langfuse using environment variables
    3. Creates a new immutable version with the specified labels
    4. Prints the created version details

This script is designed to run in CI/CD pipelines (GitHub Actions, GitLab CI)
as well as locally from the terminal.

Reference: https://langfuse.com/docs/prompt-management/features/prompt-version-control
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langfuse import get_client

logger = logging.getLogger(__name__)

# Prompt name — matches the convention in prompt_provider.py
PROMPT_NAME = "techshop-system-prompt"


def push_prompt(
    content: str,
    labels: list[str],
    *,
    name: str = PROMPT_NAME,
    config: dict | None = None,
) -> dict:
    """Create a new prompt version in Langfuse.

    Args:
        content: The prompt text (may contain {{variables}}).
        labels: Labels to assign (e.g., ["staging", "latest"]).
        name: Prompt name in Langfuse.
        config: Optional metadata dict.

    Returns:
        Dict with version info: name, labels, content_length.
    """
    lf_client = get_client()

    lf_client.create_prompt(
        name=name,
        prompt=content,
        labels=labels,
        type="text",
        config=config or {},
    )
    lf_client.flush()

    logger.info("Created prompt '%s' with labels %s", name, labels)
    return {
        "name": name,
        "labels": labels,
        "content_length": len(content),
        "status": "created",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Push a prompt version to Langfuse (CI step)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From a file
  python -m techshop_agent.cicd.push_prompt --file prompts/system_prompt.txt --labels staging latest

  # Inline content
  python -m techshop_agent.cicd.push_prompt --content "Eres Alex..." --labels staging

  # With metadata
  python -m techshop_agent.cicd.push_prompt --file prompts/v2.txt --labels staging --author "dev-team"
        """,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="Path to prompt text file")
    group.add_argument("--content", type=str, help="Prompt content inline")
    parser.add_argument(
        "--labels",
        nargs="+",
        default=["staging", "latest"],
        help="Labels to assign (default: staging latest)",
    )
    parser.add_argument("--name", default=PROMPT_NAME, help="Prompt name in Langfuse")
    parser.add_argument("--author", default="ci-pipeline", help="Author metadata")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    load_dotenv(find_dotenv(usecwd=True))

    # Read content
    if args.file:
        if not args.file.exists():
            print(f"❌ File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        content = args.file.read_text(encoding="utf-8")
        print(f"📄 Read prompt from: {args.file} ({len(content)} chars)")
    else:
        content = args.content
        print(f"📝 Using inline content ({len(content)} chars)")

    result = push_prompt(
        content=content,
        labels=args.labels,
        name=args.name,
        config={"author": args.author, "source": "ci-pipeline"},
    )

    print(f"✅ Prompt pushed successfully")
    print(f"   Name:   {result['name']}")
    print(f"   Labels: {result['labels']}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
