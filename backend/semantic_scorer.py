"""
Semantic scoring engine for v2.
Uses FastEmbed for local, reproducible semantic similarity scoring.
No API calls, no cost, consistent results.
"""

import re
import numpy as np
from typing import Optional

# Lazy-loaded model instance – downloaded once, cached locally
_model = None


def _get_model():
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        # BAAI/bge-small-en-v1.5 – 50MB, fast, good performance for semantic similarity
        # If this proves insufficient, sentence-transformers/all-MiniLM-L6-v2 is the upgrade path
        _model = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _model


def _embed(texts: list[str]) -> np.ndarray:
    model = _get_model()
    embeddings = list(model.embed(texts))
    return np.array(embeddings)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _extract_requirements(jd_text: str) -> list[str]:
    """
    Extract individual requirements from a JD.
    Looks for bullet points, numbered lists, and sentences containing
    requirement-signal words.
    """
    requirements = []

    # Split into lines and look for bullet/list items
    lines = jd_text.split("\n")
    for line in lines:
        line = line.strip()
        # Match bullet points and numbered list items
        if re.match(r"^[\-\•\*\·\–\—\d\.]+\s+.{20,}", line):
            clean = re.sub(r"^[\-\•\*\·\–\—\d\.]+\s+", "", line).strip()
            if clean:
                requirements.append(clean)

    # If we didn't find enough bullets, fall back to sentences
    if len(requirements) < 5:
        signal_words = [
            "experience", "knowledge", "ability", "skill", "background",
            "understanding", "proven", "track record", "demonstrated",
            "expertise", "familiar", "proficient", "comfortable"
        ]
        sentences = re.split(r"[.!?]+", jd_text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 30 and any(w in sentence.lower() for w in signal_words):
                requirements.append(sentence)

    # Deduplicate and limit
    seen = set()
    unique = []
    for r in requirements:
        key = r[:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique[:30]  # Cap at 30 requirements


def _split_cv_sections(cv_text: str) -> dict[str, str]:
    """
    Split CV into Summary and Professional Experience sections.
    Returns dict with 'summary', 'experience', and 'full' keys.
    """
    summary_patterns = [
        r"(?i)(professional\s+summary|summary|profile|about me?)(.*?)(?=\n[A-Z\s]{3,}\n|\Z)",
        r"(?i)(objective)(.*?)(?=\n[A-Z\s]{3,}\n|\Z)",
    ]
    experience_patterns = [
        r"(?i)(professional\s+experience|experience|work\s+history|employment)(.*?)(?=\n[A-Z\s]{3,}\n|\Z)",
    ]

    summary = ""
    experience = ""

    for pattern in summary_patterns:
        match = re.search(pattern, cv_text, re.DOTALL)
        if match:
            summary = match.group(2).strip()[:1500]
            break

    for pattern in experience_patterns:
        match = re.search(pattern, cv_text, re.DOTALL)
        if match:
            experience = match.group(2).strip()[:3000]
            break

    # Fallback – use first 500 chars as summary, rest as experience
    if not summary and not experience:
        summary = cv_text[:500]
        experience = cv_text[500:3500]

    return {
        "summary": summary,
        "experience": experience,
        "full": cv_text[:4000]
    }


def _score_section_against_requirements(
    section_text: str,
    requirements: list[str],
    threshold_strong: float = 0.72,
    threshold_partial: float = 0.62,
) -> dict:
    """
    Score a CV section against a list of requirements.
    Returns per-requirement scores and aggregate metrics.
    """
    if not section_text.strip() or not requirements:
        return {"score": 0, "matched": [], "partial": [], "gaps": []}

    # Split section into chunks for comparison
    sentences = [s.strip() for s in re.split(r"[.\n•\-]+", section_text) if len(s.strip()) > 20]
    if not sentences:
        sentences = [section_text]

    # Embed requirements and section sentences
    all_texts = requirements + sentences
    try:
        all_embeddings = _embed(all_texts)
    except Exception as e:
        return {"score": 0, "matched": [], "partial": [], "gaps": [], "error": str(e)}

    req_embeddings = all_embeddings[:len(requirements)]
    sent_embeddings = all_embeddings[len(requirements):]

    matched = []
    partial = []
    gaps = []
    scores = []

    for i, req in enumerate(requirements):
        # Find best matching sentence in the section
        best_sim = 0.0
        for sent_emb in sent_embeddings:
            sim = _cosine_similarity(req_embeddings[i], sent_emb)
            if sim > best_sim:
                best_sim = sim

        scores.append(best_sim)

        if best_sim >= threshold_strong:
            matched.append({"requirement": req, "similarity": round(best_sim, 3)})
        elif best_sim >= threshold_partial:
            partial.append({"requirement": req, "similarity": round(best_sim, 3)})
        else:
            gaps.append({"requirement": req, "similarity": round(best_sim, 3)})

    aggregate_score = int(round(np.mean(scores) * 100)) if scores else 0

    return {
        "score": aggregate_score,
        "matched": matched,
        "partial": partial,
        "gaps": gaps,
    }


def score_cv_semantic(cv_text: str, jd_text: str) -> dict:
    """
    Main entry point for semantic scoring.
    Returns structured scores for Summary, Experience, and overall,
    plus credibility gap.
    """
    requirements = _extract_requirements(jd_text)
    sections = _split_cv_sections(cv_text)

    summary_result = _score_section_against_requirements(
        sections["summary"], requirements
    )
    experience_result = _score_section_against_requirements(
        sections["experience"], requirements
    )

    # Overall score weighted toward experience (70/30)
    overall = int(round(
        experience_result["score"] * 0.7 + summary_result["score"] * 0.3
    ))

    # Credibility gap – positive means summary overclaims vs experience
    credibility_gap = summary_result["score"] - experience_result["score"]

    return {
        "semantic_score": overall,
        "summary_score": summary_result["score"],
        "experience_score": experience_result["score"],
        "credibility_gap": credibility_gap,
        "credibility_flag": credibility_gap > 15,  # Flag if summary scores 15+ points higher
        "requirements_found": len(requirements),
        "summary_matches": summary_result.get("matched", []),
        "summary_partials": summary_result.get("partial", []),
        "summary_gaps": summary_result.get("gaps", []),
        "experience_matches": experience_result.get("matched", []),
        "experience_partials": experience_result.get("partial", []),
        "experience_gaps": experience_result.get("gaps", []),
        "error": summary_result.get("error") or experience_result.get("error"),
    }
