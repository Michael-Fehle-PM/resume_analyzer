# v1.0 — Initial Release

## What shipped

A working end-to-end CV analyser and job application tracker, built to solve a specific personal problem: the repetitive, manual work of tailoring a CV to each application and tracking the results.

### CV Analyser
- Upload one or more CVs as PDF (server-side text extraction via pdfplumber) or paste text directly
- Paste or auto-fetch a job description by URL (server-side fetch, bypassing browser CORS restrictions)
- AI-powered match analysis returning three scores (overall, keyword, experience) with categorised matches, partial matches, and gaps — each rated by importance
- Reorders experience bullets within each role so the most JD-relevant appear first
- Exports the reordered CV as HTML (print-ready), Markdown, or .docx

### Job Tracker
- Log applications with role, company, JD URL, date applied, status, and notes
- Six status options: Applied, Interview, Offer, Rejected, No response, Withdrawn
- Full edit and delete
- Data persists in SQLite

### Stack
FastAPI · Anthropic Claude API · pdfplumber · SQLite via SQLAlchemy · python-docx · plain HTML/CSS/JS

## Known issues addressed in v1.1
- Model string `claude-sonnet-4-20250514` returned 404 — updated to `claude-sonnet-4-6`
- PDF text extraction using pdfplumber produced ligature encoding errors (`integraƟon`, `plaƞorm`) on certain fonts — swapped to pymupdf which handles font encoding correctly
- CV reorder API call was hitting token limits and returning truncated JSON — split into two separate calls (HTML and Markdown) each within token budget
- SQLite database path used a relative reference (`./resumeapp.db`) that broke when the app was launched from a different working directory — replaced with a dynamic path derived from the file's own location, making it drive-letter independent
- Startup script `start.bat` assumed C: drive — fixed with `%~d0` and `%~dp0` to work from any drive

---

# v1.1 — Stability Fixes

## What's fixed

### Model string
Updated API model reference from `claude-sonnet-4-20250514` (404) to `claude-sonnet-4-6`.

### PDF extraction
Replaced `pdfplumber` with `pymupdf` (`fitz`). pdfplumber was producing ligature encoding errors on Calibri and similar fonts — characters like "ti", "fi", and "fl" were being rendered as `Ɵ` or `(cid:415)` rather than the correct letters. This would cause ATS systems to fail to match keywords containing those letter combinations. pymupdf handles font encoding correctly and produces clean text output.

### Token limit handling
The CV reorder endpoint was sending a single API request asking Claude to return the entire CV twice — once as HTML and once as Markdown — in a single JSON object. This regularly exceeded the token limit and returned truncated, unparseable JSON. Split into two sequential requests, each returning one format, both within the token budget.

### Database path
The SQLite connection string `sqlite:///./resumeapp.db` resolves relative to the working directory at runtime, not the application's location. When `start.bat` was launched from a different directory — or when the application lived on a removable drive that changed letter — a new empty database was created rather than finding the existing one, silently losing all tracker data. Fixed by deriving the database path from `Path(__file__).resolve().parent.parent`, making it location-independent.

### Startup script
`start.bat` used hardcoded relative paths that assumed the working directory was C:. Added `%~d0` (switch to the script's drive) and `%~dp0` (navigate to the script's directory) so the script works correctly when launched from any drive or via a desktop shortcut.

## Additional files added
- `ROADMAP.md` — documents planned v2, v3, and v4 features with rationale for sequencing
- `start.sh` — equivalent startup script for macOS/Linux
- `screenshots/` — app screenshots for README

---

# v2.0 — Semantic Scoring & Before/After Analysis

## What's new

### Semantic match scoring
Replaced the v1 Claude-based scoring with a local semantic similarity engine powered by FastEmbed. The new engine compares the *meaning* of your CV against each JD requirement rather than counting keywords — catching conceptual matches that literal matching would miss (e.g. "owned data pipeline infrastructure" matching "platform infrastructure ownership").

Scores are now consistent and reproducible: same inputs, same result every time. No API call, no cost.

### Split scoring — Summary vs Experience
The CV is now scored in two sections separately:
- **Summary score** — how well the summary's claims align with JD requirements
- **Experience score** — how well the Professional Experience section evidences those claims
- **Credibility gap** — flagged when the summary scores significantly higher than the experience, indicating the CV may be making promises the evidence doesn't fully support

### Before/after analysis
The tool now shows a baseline score on the raw CV before any optimisation, plus a predicted score after optimisation based on addressable gaps. Users see the delta upfront and can decide whether the effort is worth it before any API spend is committed.

### Gap classification
A focused Claude call classifies each gap by type:
- **Structural** — the skill genuinely doesn't exist in the candidate's background
- **Domain transfer** — the skill exists but not in the required domain; addressable with reframing
- **Keyword** — the experience exists but the vocabulary doesn't match; addressable with rewording
- **Seniority** — the skill is present at the wrong level

### Sequential three-step flow
The analysis now runs in stages with a decision gate between steps:
1. Semantic scoring (free, instant) → show scores and credibility gap
2. Gap classification (small Claude call, ~$0.004) → show before/after, gap types, recommendation
3. User decides whether to proceed → full qualitative analysis + CV reorder on request

This means users only pay for API calls when the fit is worth pursuing.

### FAQ panel
A new FAQ tab addresses the "ATS score" myth directly and explains what each score actually measures.

## Technical changes
- New: `backend/semantic_scorer.py` — FastEmbed local scoring engine
- New: `backend/gap_classifier.py` — gap classification and before/after prediction
- Updated: `main.py` — two new endpoints: `/api/semantic-score` and `/api/classify-gaps`
- Updated: `frontend/templates/index.html` — complete UI rewrite
- Updated: `requirements.txt` — added `fastembed==0.8.0`, `numpy`
- Updated: `backend/pdf_utils.py` — pymupdf version bump to 1.25.5 for Python 3.12/3.13 compatibility

## Known issues addressed in v2.0.1
- Scoring thresholds needed tightening — items in the 0.55–0.62 similarity range were being classified as partial matches rather than gaps, suppressing gap surfacing for roles with diffuse domain mismatch
- Recommendation text was returning "Strong match" for moderate scores when no gaps were identified — misleading for roles where the issue is domain vocabulary distance rather than missing skills

---

# v2.1 — Scoring Calibration

## What's fixed

### Tightened semantic scoring thresholds
The partial match threshold was too generous (0.55), causing items with weak similarity to be classified as partial matches rather than gaps. This suppressed gap surfacing for roles with diffuse domain vocabulary mismatch — the scenario where nothing scores strongly but nothing is explicitly flagged either.

Updated thresholds:
- Strong match: 0.75 → 0.72 (slightly more generous)
- Partial match floor: 0.55 → 0.62 (raises the bar, pushes weak partials into gaps)

### Score-aware recommendations when no gaps are found
The "no gaps" early return was always returning "Strong match — proceed with optimisation" regardless of the actual score. This produced contradictory output: a 65 baseline with a "Strong match" recommendation.

Recommendations are now score-aware:
- **78+, no gaps** → "Strong semantic match — proceed with optimisation"
- **65–77, no gaps** → "Moderate match — likely a diffuse domain vocabulary mismatch; consider mirroring JD vocabulary more explicitly"
- **Below 65, no gaps** → "Low match — domain may be too distant for effective optimisation"

## Calibration notes
These threshold changes were informed by running real applications through the tool:
- A rejected application (Placements.io) scored 57 baseline — consistent with the rejection
- A strong pending application (Nova Credit) scored 45 baseline due to domain vocabulary distance, with 6 addressable gaps pushing the predicted score to 72
- A moderate fit application (JustWorks) scored 65 with no gaps under v2.0, correctly reclassified as diffuse domain mismatch under v2.0.1 with a predicted ceiling of 82

The tool is now better at distinguishing between "you don't have the skills" and "you have the skills but the vocabulary doesn't match."

---

# v3.0 — Supporting Materials Generator

## What's new

### Summary Builder (Step 4)
Appears after the full analysis completes. Generates three versions of a tailored professional summary from the reordered CV and JD — short (2 sentences), standard (3 sentences), and full (4 sentences). Each version:
- Leads with the candidate's strongest positioning for the specific role
- Incorporates JD keywords naturally
- Avoids age signals
- Includes an ATS note explaining which keywords were included and why

The user selects their preferred version before proceeding to the cover letter.

### Cover Letter Generator (Step 5)
Appears after the user selects a summary. Generates a cover letter drawing from the reordered CV, selected summary, JD, and gap classification. Features:
- Tone selector: Professional / Confident & Direct / Conversational
- Length selector: Short (3 paragraphs) / Standard (4 paragraphs) / Full (5 paragraphs)
- Optional personal connection field — mission alignment, personal experience with the company's product, referral context etc.
- Addresses gaps proactively based on gap type — structural gaps handled differently from keyword gaps
- Copy to clipboard or download as .txt
- Suggested email subject line included
- Key arguments summary shown below the letter

Both generators are tied to the current analysis run. They operate on the reordered CV, not the raw uploaded CV. Standalone versions (without requiring a prior analysis) are planned for v4.

### Improved .docx output
Complete rewrite of the docx generator to match a professional CV template:
- Calibri font throughout
- Teal section headers (#1D6E72) with bottom border
- Job title lines: bold title | mid-colour company, date right-aligned via tab stop
- Sub-labels: 9pt italic mid-colour
- Symbol font bullet character matching Word default
- Areas of Expertise rendered as single pipe-separated line — no bullets
- Skills section: bold label, left tab at 1620 twips, no colons
- Education: bold degree, tab at 3150 twips, plain institution — no bullets, no separator character
- Contact line: email, LinkedIn, and GitHub rendered as clickable blue hyperlinks
- Spacing matched precisely to template measurements

### Test scripts
Two zero-cost test scripts for the most fragile parts of the codebase:
- `test_docx.py` — tests the docx generator with hardcoded markdown; no API calls; outputs `test_output.docx` for visual inspection
- `test_reorder.py` — tests the reorder_cv function with a mocked API response; no tokens spent; confirms function logic and output structure

### Developer utilities
- `activate.bat` — double-click to open a terminal with `.venv312` already active

## Technical changes
- New: `backend/generators.py` — Summary Builder and Cover Letter Generator
- New: `test_docx.py`, `test_reorder.py`, `activate.bat`
- Updated: `main.py` — two new endpoints: `/api/build-summary` and `/api/build-cover-letter`
- Updated: `backend/analyser.py` — complete `generate_docx` rewrite; strict markdown formatting rules in reorder prompt; split two-call reorder confirmed
- Updated: `frontend/templates/index.html` — Steps 4 and 5 added; appears only after Step 3 completes

## Known issues addressed in v3.0
- Double-brace escaping bug in `reorder_cv` caused `unhashable type: dict` error — fixed
- Model string reverted to old dated value — corrected to `claude-sonnet-4-6`
- `max_tokens` reset to 1000 in generated files — corrected to 4096 throughout

## Known issues for v3.1
- Selected summary not carried through to CV download — download still uses original summary
- Progress indicator scrolls off screen once all steps are visible
- No tone selector explanations for Summary Builder or Cover Letter Generator
- Download file naming is generic — not role/company specific
- Full accordion step flow with sticky headers not yet implemented — see ROADMAP.md for full spec
