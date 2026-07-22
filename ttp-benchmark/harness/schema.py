"""Shared output schema for the TTP-extraction task.

Every provider is asked to return the same JSON shape so results are directly
comparable. The JSON Schema below is used two ways:

  * Anthropic path  -> passed to `output_config.format` (structured outputs).
  * OpenAI path     -> described in the prompt + validated after the fact.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Technique(BaseModel):
    technique_id: str = Field(..., description="Canonical MITRE ATT&CK id, e.g. T1566.001")
    name: str = Field("", description="ATT&CK technique name, if known")
    evidence: str = Field("", description="Short quote from the report supporting this id")


class TTPExtraction(BaseModel):
    techniques: list[Technique] = Field(default_factory=list)


# Hand-written JSON Schema that satisfies Anthropic strict structured-output
# rules (every property required, additionalProperties: false).
TTP_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "techniques": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "technique_id": {"type": "string"},
                    "name": {"type": "string"},
                    "evidence": {"type": "string"},
                },
                "required": ["technique_id", "name", "evidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["techniques"],
    "additionalProperties": False,
}
