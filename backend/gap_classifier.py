"""
Gap classification for v2.
Uses a small, focused Claude call to classify gaps as:
- Structural: skill/experience genuinely absent
- Domain transfer: skill present, wrong domain
- Keyword: experience exists, vocabulary mismatch
- Seniority: skill present at wrong level

Also predicts post-optimisation score based on addressable gaps.
"""

import json
import re
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


def _clean_json(raw: str) -> str:
    raw = re.sub(r"```json|```", "", raw).strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    return match.group(0) if match else raw


def classify_gaps(
    cv_text: str,
    jd_text: str,
    gaps: list[dict],
    current_score: int,
) -> dict:
    """
    Classify gaps and predict post-optimisation score.
    Sends only the gap list to Claude – not the full CV/JD – to minimise token usage.
    """
    if not gaps:
        return {
            "classified_gaps": [],
            "predicted_score": current_score,
            "addressable_count": 0,
            "structural_count": 0,
            "recommendation": "Strong match – proceed with optimisation.",
        }

    gap_list = "\n".join([f"- {g['requirement']}" for g in gaps[:15]])

    prompt = f"""You are a senior PM career coach. A candidate is applying for this role.

JOB DESCRIPTION SUMMARY (first 800 chars):
{jd_text[:800]}

CANDIDATE CV SUMMARY (first 600 chars):
{cv_text[:600]}

GAPS IDENTIFIED (requirements not well matched in the CV):
{gap_list}

CURRENT SEMANTIC MATCH SCORE: {current_score}/100

For each gap, classify it as one of:
- structural: the candidate genuinely does not have this experience; no reframing will close it
- domain_transfer: the candidate has the underlying skill but not in this specific domain; addressable with reframing
- keyword: the experience likely exists but the CV uses different vocabulary; addressable with rewording
- seniority: the skill is present but at the wrong level; partially addressable

Then predict the score after optimisation, assuming all non-structural gaps are addressed.

Return ONLY this JSON, no preamble:
{{
  "classified_gaps": [
    {{"requirement": "...", "type": "structural|domain_transfer|keyword|seniority", "rationale": "brief reason", "addressable": true|false}}
  ],
  "predicted_score": <0-100>,
  "addressable_count": <number>,
  "structural_count": <number>,
  "recommendation": "one sentence recommendation on whether to proceed"
}}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = message.content[0].text
    return json.loads(_clean_json(raw))
