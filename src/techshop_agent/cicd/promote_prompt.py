"""CD script: Promote a prompt version to production.

This is the "CD" part of the Prompt CI/CD pipeline.
After the quality gate passes, this script promotes the staging prompt
to production by moving the "production" label.

Usage:
    python -m techshop_agent.cicd.promote_prompt --from-label staging --to-label production

How it works:
    1. Fetches the current prompt version for the source label (e.g., "staging")
    2. Fetches the current prompt version for the target label (e.g., "production")
    3. Creates a new version identical to the source but with the target label
    4. The agent reads by label, so the next request uses the new prompt

Why re-create instead of moving labels?
    The Langfuse Python SDK does not expose a direct "move label" API.
    The recommended pattern is to create a new identical version with the
    target label, which has the same effect: the agent's next get_prompt()
    call with label="production" returns the new content.

    Alternatively, you can move labels via the Langfuse UI which is
    the preferred approach for manual promotions.

Reference: https://langfuse.com/docs/prompt-management/features/prompt-version-control
"""

from __future__ import annotations

import argparse
import logging
import sys

from dotenv import find_dotenv, load_dotenv
from langfuse import get_client

logger = logging.getLogger(__name__)

PROMPT_NAME = "techshop-system-prompt"


def promote_prompt(
    *,
    from_label: str = "staging",
    to_label: str = "production",
    name: str = PROMPT_NAME,
) -> dict:
    """Promote a prompt from one label to another.

    Reads the prompt content from `from_label` and creates a new version
    with `to_label`, effectively "promoting" the content.

    Args:
        from_label: Source label (e.g., "staging").
        to_label: Target label (e.g., "production").
        name: Prompt name in Langfuse.

    Returns:
        Dict with promotion details.
    """
    lf_client = get_client()

    # Fetch the source prompt
    source = lf_client.get_prompt(name, label=from_label, cache_ttl_seconds=0)
    source_content = source.prompt

    if source.is_fallback:
        raise RuntimeError(
            f"Cannot promote: label '{from_label}' returned fallback prompt. "
            "Ensure the source label exists in Langfuse."
        )

    logger.info(
        "Promoting '%s' from label '%s' (v%s) to '%s'",
        name,
        from_label,
        source.version,
        to_label,
    )

    # Create new version with the target label
    lf_client.create_prompt(
        name=name,
        prompt=source_content,
        labels=[to_label, "latest"],
        type="text",
        config={
            "promoted_from": from_label,
            "source_version": source.version,
            "source": "promote-script",
        },
    )
    lf_client.flush()

    return {
        "name": name,
        "from_label": from_label,
        "to_label": to_label,
        "source_version": source.version,
        "status": "promoted",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote a prompt from one label to another (CD step)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m techshop_agent.cicd.promote_prompt --from-label staging --to-label production
  python -m techshop_agent.cicd.promote_prompt --from-label latest --to-label staging
        """,
    )
    parser.add_argument(
        "--from-label",
        default="staging",
        help="Source label to promote from (default: staging)",
    )
    parser.add_argument(
        "--to-label",
        default="production",
        help="Target label to promote to (default: production)",
    )
    parser.add_argument("--name", default=PROMPT_NAME, help="Prompt name in Langfuse")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    load_dotenv(find_dotenv(usecwd=True))

    print(f"\n🚀 Promoting prompt: {args.from_label} → {args.to_label}")

    try:
        result = promote_prompt(
            from_label=args.from_label,
            to_label=args.to_label,
            name=args.name,
        )
        print(f"✅ Promotion successful!")
        print(f"   Source: {result['from_label']} (v{result['source_version']})")
        print(f"   Target: {result['to_label']}")
    except Exception as exc:
        print(f"❌ Promotion failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
