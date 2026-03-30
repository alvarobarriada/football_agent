from __future__ import annotations

import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

load_dotenv()

GUARDRAIL_NAME = "football-agent-guardrail"
COMPETITOR_BRANDS = ["sofascore", "whoscored", "statsbomb", "opta", "wyscout", "instat"]
BLOCKED_WORDS = [{"text": brand} for brand in COMPETITOR_BRANDS]


def create_guardrail(region: str | None = None) -> tuple[str, str]:
    """Create the Bedrock guardrail and return (guardrail_id, version)."""
    bedrock = boto3.client(
        "bedrock",
        region_name=region or os.getenv("AWS_REGION", "eu-west-1"),
    )

    response = bedrock.create_guardrail(
        name=GUARDRAIL_NAME,
        description="Guardrail para el agente de MaldinIA",
        contentPolicyConfig={
            "filtersConfig": [
                {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "NONE"},
                {"type": "INSULTS", "inputStrength": "MEDIUM", "outputStrength": "MEDIUM"},
                {"type": "HATE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
                {"type": "SEXUAL", "inputStrength": "HIGH", "outputStrength": "HIGH"},
                {"type": "VIOLENCE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
            ]
        },
        wordPolicyConfig={"wordsConfig": BLOCKED_WORDS},
        sensitiveInformationPolicyConfig={
            "piiEntitiesConfig": [
                {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "BLOCK"},
                {"type": "EMAIL", "action": "BLOCK"},
                {"type": "PHONE", "action": "BLOCK"},
                {"type": "AWS_ACCESS_KEY", "action": "BLOCK"},
                {"type": "AWS_SECRET_KEY", "action": "BLOCK"},
            ]
        },
        blockedInputMessaging="No puedo procesar tu consulta por razones de seguridad.",
        blockedOutputsMessaging="Lo siento, no puedo proporcionar esa informacion.",
    )

    guardrail_id = response["guardrailId"]
    version = response["version"]
    print(f"Guardrail creado: {guardrail_id}")
    print(f"Version: {version}")
    print(f"Añade al .env: BEDROCK_GUARDRAIL_ID={guardrail_id}")
    return guardrail_id, version

# Para comprobar si existe guardarraíl o, en su defecto, crearlo.
# Si se crea así, recuerda luego meterlo en .env
"""
# Bedrock Guardrails
BEDROCK_GUARDRAIL_ID="(generado por este script))"
BEDROCK_GUARDRAIL_VERSION="DRAFT"
"""
def ensure_guardrail(region: str | None = None) -> str:
    """Return the guardrail ID, creating it and persisting to .env if missing."""
    guardrail_id = os.getenv("BEDROCK_GUARDRAIL_ID")
    if guardrail_id:
        return guardrail_id

    print("BEDROCK_GUARDRAIL_ID no encontrado en .env — creando guardrail...")
    guardrail_id, _ = create_guardrail(region=region)

    env_path = Path(__file__).parents[2] / ".env"
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        if "BEDROCK_GUARDRAIL_ID" not in content:
            with env_path.open("a", encoding="utf-8") as f:
                f.write(f"\nBEDROCK_GUARDRAIL_ID={guardrail_id}\n")
            print(f"BEDROCK_GUARDRAIL_ID guardado en {env_path}")

    os.environ["BEDROCK_GUARDRAIL_ID"] = guardrail_id
    return guardrail_id


if __name__ == "__main__":
    create_guardrail()
