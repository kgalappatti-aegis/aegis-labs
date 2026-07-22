"""The extraction prompt, shared verbatim across all providers.

Keeping this identical for every model is the whole point of a fair harness —
if you tune the prompt, re-run every model.
"""

SYSTEM = (
    "You are a cyber threat-intelligence analyst. You extract adversary "
    "Tactics, Techniques, and Procedures (TTPs) from threat reports and map "
    "them to the MITRE ATT&CK framework (Enterprise matrix)."
)

INSTRUCTIONS = """\
Read the threat-intelligence report below and identify every MITRE ATT&CK
technique that the report *explicitly supports* with described behaviour.

Rules:
- Use canonical ATT&CK technique ids (e.g. T1566, T1059.001). Prefer the most
  specific sub-technique the text supports; use the parent id if the text is
  only general.
- Only include a technique when the report describes behaviour matching it. Do
  not infer techniques that are merely plausible for the named actor/malware.
- For each technique include a short verbatim quote from the report as evidence.
- Do not include duplicate ids.

Return ONLY JSON matching this shape (no prose, no markdown fences):
{"techniques": [{"technique_id": "T####[.###]", "name": "...", "evidence": "..."}]}

REPORT:
---
%(report)s
---
"""


def build_user_prompt(report_text: str) -> str:
    return INSTRUCTIONS % {"report": report_text}
