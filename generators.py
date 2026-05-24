"""
v3 generators — Summary Builder and Cover Letter Generator.
Both operate on the reordered CV and analysis results from a completed analysis run.
Neither generates from a raw, unoptimised CV.
"""

import anthropic
import json
import re

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


def _clean(raw: str) -> str:
    return re.sub(r"```json|```", "", raw).strip()


def build_summary(
    reordered_cv: str,
    jd_text: str,
    gap_classification: dict,
    tone: str = "professional",
    existing_summary: str = "",
) -> dict:
    """
    Generate a tailored professional summary from the reordered CV and JD.
    Returns multiple options at different lengths so the user can choose.
    
    tone: "professional" | "confident" | "conversational"
    """

    addressable = [
        g for g in gap_classification.get("classified_gaps", [])
        if g.get("addressable") and g.get("type") in ("keyword", "domain_transfer")
    ]
    addressable_text = "\n".join([f"- {g['requirement']} ({g['type']})" for g in addressable[:5]])

    existing_note = f"\nExisting summary for reference (do not copy, use as context only):\n{existing_summary[:500]}" if existing_summary else ""

    prompt = f"""You are an expert CV writer and senior PM career coach.

Write THREE versions of a professional summary for this candidate — short (2 sentences), standard (3 sentences), and full (4 sentences). 
Each must:
- Lead with the candidate's strongest platform/domain positioning for this specific role
- Incorporate keywords from the JD naturally, not forcibly
- Avoid age signals (no "X years of experience", use "extensive" or "career-long" instead)
- Be written in third-person-free style (no "I" but also no "He/She/They") — declarative statements only
- Not overclaim on gaps — if a skill is a domain transfer, frame it as transferable, not identical
- Tone: {tone}

Addressable gaps to weave in subtly where honest:
{addressable_text if addressable_text else "None identified"}
{existing_note}

Return ONLY this JSON, no preamble:
{{
  "short": "2-sentence summary",
  "standard": "3-sentence summary", 
  "full": "4-sentence summary",
  "ats_note": "brief note on which keywords from the JD are included and why"
}}

JOB DESCRIPTION (first 1000 chars):
{jd_text[:1000]}

REORDERED CV:
{reordered_cv[:3000]}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = message.content[0].text
    return json.loads(_clean(raw))


def build_cover_letter(
    reordered_cv: str,
    jd_text: str,
    gap_classification: dict,
    summary: str,
    tone: str = "formal",
    length: str = "standard",
    personal_note: str = "",
) -> dict:
    """
    Generate a cover letter from the reordered CV, JD, gap classification, and summary.
    
    tone: "formal" | "confident" | "conversational"
    length: "short" (3 paragraphs) | "standard" (4 paragraphs) | "full" (5 paragraphs)
    personal_note: optional personal connection to the role/company to include
    """

    structural_gaps = [
        g for g in gap_classification.get("classified_gaps", [])
        if not g.get("addressable") or g.get("type") == "structural"
    ]
    addressable_gaps = [
        g for g in gap_classification.get("classified_gaps", [])
        if g.get("addressable") and g.get("type") != "structural"
    ]

    structural_text = "\n".join([f"- {g['requirement']}: {g['rationale']}" for g in structural_gaps[:3]])
    addressable_text = "\n".join([f"- {g['requirement']} ({g['type']}): {g['rationale']}" for g in addressable_gaps[:5]])

    para_count = {"short": 3, "standard": 4, "full": 5}.get(length, 4)

    personal_instruction = f"\nInclude this personal connection naturally in one paragraph:\n{personal_note}" if personal_note else ""

    prompt = f"""You are an expert CV writer and senior PM career coach.

Write a {tone} cover letter in {para_count} paragraphs for this candidate applying to this role.

Structure:
- Paragraph 1: Opening — genuine hook, why this role specifically, lead with strongest platform/domain fit
- Paragraph 2: Evidence — 2-3 specific, quantified achievements from the reordered CV most relevant to this JD
- Paragraph 3: {"Address domain gaps head-on — frame as transferable discipline, not identical experience. Be honest, not defensive." if structural_gaps else "Additional evidence or context that strengthens the application"}
{"- Paragraph 4: Personal connection / mission alignment" if para_count >= 4 and personal_note else "- Paragraph 4: Forward-looking close" if para_count >= 4 else ""}
{"- Paragraph 5: Clean, confident close" if para_count >= 5 else ""}

Rules:
- Never use the word "honestly" (implies everything else is dishonest)
- Never start a sentence with "I am writing to..."
- Tone: {tone}
- Use en-dashes (–) not em-dashes
- Address gaps directly, not apologetically
- Do not reproduce the summary verbatim — the cover letter should complement it, not repeat it
{personal_instruction}

Structural gaps to address (genuine absences — be honest, reframe as learning curve not disqualifier):
{structural_text if structural_text else "None — no structural gaps identified"}

Addressable gaps (these can be reframed confidently):
{addressable_text if addressable_text else "None identified"}

CANDIDATE SUMMARY:
{summary}

JOB DESCRIPTION (first 1200 chars):
{jd_text[:1200]}

REORDERED CV:
{reordered_cv[:3000]}

Return ONLY this JSON, no preamble:
{{
  "cover_letter": "full cover letter text with paragraph breaks as \\n\\n",
  "subject_line": "suggested email subject line",
  "key_points": ["3-4 bullet points summarising the main arguments made"]
}}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = message.content[0].text
    result = json.loads(_clean(raw))
    return result
