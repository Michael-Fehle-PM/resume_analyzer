# Roadmap

This document captures the planned development of the Resume Analyser. It's intentionally public — partly for transparency, and partly because a PM who can't articulate a roadmap probably shouldn't be building product tools.

The sequencing follows a simple principle: find the smallest thing that adds real value, ship it, then find the next smallest. Each version has a theme. Features that don't serve that theme wait for a later version, however tempting they are.

---

## What we learned from v1

No plan survives first contact with users — even when the user is yourself.

v1 shipped with a Claude-based scoring system that produces directionally useful results but isn't reproducible. Run the same CV against the same JD twice and you'll get slightly different scores. That's a problem for a tool whose core value proposition is telling you whether your CV is good enough to clear an ATS filter. You can't act confidently on a number you can't trust.

v1 also does all the optimisation work upfront — reordering bullets, generating HTML and Markdown output — before the user knows whether the effort is worth it. For a role where the gaps are structural and unfillable, that's wasted API spend and wasted time.

These aren't bugs. They're the kind of things you only discover by using the tool on real applications, against real job descriptions, under real conditions. v2 fixes them.

---

## v1 — Ship something useful
*Status: complete*

A working CV analyser and job tracker. Upload a CV, paste a JD, get a scored match analysis with matches, partials, and gaps. Download a reordered CV. Track applications in a persistent local database.

**What it does well:**
- End-to-end workflow from CV upload to reordered output
- Qualitative gap analysis with importance ratings
- Job tracker with persistent SQLite storage
- Server-side PDF extraction, JD fetching, and .docx generation

**What it doesn't do well:**
- Scores aren't reproducible or fully explainable
- No way to assess fit before committing to the full analysis
- Gap classification is binary — present or absent — with no nuance about *why* something is a gap or whether it's fixable

---

## v2 — Make the scores trustworthy
*Status: planned*

The theme for v2 is trust. A score you can't explain is a score you can't act on.

**Local ATS simulation:**
Real ATS systems don't have opinions — they count. v2 adds a keyword-frequency scoring engine that runs entirely locally, with no API call and no variability. Same inputs, same score, every time. The score is explainable because it's derived from a defined algorithm: which keywords appear in the JD, how prominently, and whether they appear in the CV.

**Three scoring modes:**
- *ATS Simulation* — local keyword matching; fast, free, reproducible
- *Recruiter View* — Claude-based qualitative assessment; the current v1 approach
- *Combined* — weighted composite of both

Showing all three simultaneously is deliberate. Where they agree, confidence is high. Where they diverge — high ATS score but low recruiter score, for example — that's a signal worth investigating. It might mean the CV is keyword-optimised but thin on substance, or well-written but missing the right vocabulary.

**Before/after analysis:**
Before any optimisation work happens, v2 will show a baseline score on the raw CV and a predicted score after optimisation. The user sees the delta — *"this could move from 68% to 84%, here's what to change"* — and decides whether the effort is worth it before any API spend is committed. For roles where the gaps are structural, this saves time and money. For roles where the fit is strong, it gives the user confidence to proceed.

**Richer gap classification:**
v1 flags gaps. v2 explains them. Each gap will be typed:

- *Structural* — the skill or experience doesn't exist in your background; no amount of reframing will close this gap
- *Domain transfer* — you have the underlying skill but not in the domain the JD requires; addressable with the right framing
- *Keyword gap* — the experience exists but the vocabulary doesn't match; addressable with targeted rewording
- *Seniority gap* — the skill is present but at the wrong level; partially addressable depending on the size of the gap

The distinction between structural and addressable gaps is the most important thing the tool can communicate. It's the difference between "don't apply" and "apply but reframe this."

**Split scoring – Summary vs Professional Experience:**
A CV summary can claim almost anything. "Experienced platform PM with a track record of delivery" costs nothing to write. The proof is in the Professional Experience section – have you actually done this, in a real role, with measurable outcomes?

v2 will score these separately:

- *Summary score* – how well the summary's claims align with the JD requirements
- *Experience score* – how well the Professional Experience section evidences those claims
- *Credibility gap* – the delta between the two; a high summary score but low experience score is a yellow flag; it suggests the CV is making promises the experience doesn't keep

This matters because ATS systems weight the summary heavily for keyword matching, while human recruiters weight the experience heavily for credibility. Showing both scores separately gives the user a clearer picture of where they stand with each audience.

**Semantic similarity engine:**
Scoring uses [FastEmbed](https://github.com/qdrant/fastembed) for local semantic similarity matching – comparing the meaning of CV sections against JD requirements rather than counting keywords. This catches conceptual matches that keyword frequency would miss (e.g. "owned data pipeline infrastructure" matching "platform infrastructure ownership") and produces consistent, reproducible scores without any API call.

FastEmbed was chosen over the more widely-used `sentence-transformers` library for v2 because it has a significantly smaller footprint (~50MB model vs 80MB+ model + 200MB–2GB torch dependency). If FastEmbed proves insufficient for later use cases – particularly if GPU-accelerated inference becomes relevant – migrating to `sentence-transformers` with PyTorch is a straightforward swap and will be evaluated for v3+.

**No new database tables required for v2.** All scoring is in-memory. The database work comes in v3.

---

## v2.1 — Boilerplate filtering
*Status: planned*

**The problem v2.1 solves:**
The semantic scoring engine penalises candidates for not matching generic JD filler — phrases like "strong communication skills", "fast-paced environment", "team player", and "competitive benefits" that appear in virtually every job posting and carry no real signal about role fit. When all identified gaps are boilerplate artifacts, a low baseline score is misleadingly pessimistic.

**The fix:**
A static boilerplate filter runs before requirement extraction, stripping common filler phrases from the JD before scoring. This means the semantic engine only measures match against requirements that actually differentiate the role — producing a more honest and actionable score.

**Implementation:**
A curated stoplist of ~50-100 common boilerplate phrases in , applied to the extracted requirements before embedding. Transparent, fast, and easy to extend. If the static list proves insufficient, v3 will evaluate a semantic boilerplate detection approach that self-calibrates against a boilerplate template embedding.

**Expected impact:**
Roles where gaps are predominantly boilerplate artifacts should see baseline scores rise by 10-15 points, bringing them into alignment with the AI Assessment scores and the gap classifier's recommendation.

---

## v3 — Generate supporting materials
*Status: planned*

The theme for v3 is output. v1 and v2 do the analytical work — scoring, gap classification, reordering. v3 turns that analysis into the materials the user actually submits: a tailored summary and a cover letter.

Both are tied to a specific analysis run in v3. The user uploads a CV, runs the analysis, and then generates supporting materials from the results already in context. No separate uploads, no separate flow. Standalone versions — where the Summary Builder and Cover Letter Generator work without a prior analysis — are deferred to v4.

**Summary builder:**
Generates a tailored professional summary drawing from the submitted CV, the JD, and the gap classification results. Shows predicted ATS score impact before the user commits to the wording. Tone and length selectable.

**Cover letter generator:**
Draws from the submitted CV, JD, and gap classification. Addresses gaps proactively based on gap type — structural gaps handled differently from keyword gaps. Tone and length selectable. The user's personal connection to the role or company can be optionally added.

---

## v4 — Make the tool know the user
*Status: planned*

The theme for v4 is personalisation. v1–v3 treat every analysis as stateless. v4 introduces persistent user knowledge.

**Skills bank:**
A persistent career repository — upload CVs going back as far as you choose, and the bank accumulates every skill and capability you have ever demonstrated. The bank is cumulative; it remembers which CVs have already been processed and does not re-scrape duplicates.

The bank operates on two deliberate principles:
- *The bank is what you can claim; the CV is where you demonstrated it.* Role boundaries are always respected — skills stay attributed to the role where they were earned.
- *Visibility rules apply.* The bank may know about roles not on the submitted CV. Those roles inform the confidence of a claim but cannot be cited directly. Only evidence visible on the submitted CV surfaces in output.

The bank also identifies skill threads — capabilities that span multiple roles and deepen over time. Where those roles are visible on the CV, the thread can be referenced. Where they are not, the thread is a confidence signal for the tool, not a claim for the user to make.

**Manual skill entry:**
Not everything worth claiming appears on a CV. Skills built outside professional work — a language, a qualification, a tool learned independently — belong in the bank too. Manual entries require:
- Skill name and category
- Source: professional / non-professional / self-taught
- Proficiency: expert / proficient / familiar
- Whether it currently appears on a CV

Non-professional skills surface in the Skills section of the CV only. They are never inserted into Professional Experience. This is not just a design decision — it is an ethical one.

**Gap analysis against the bank:**
With the bank in place, gap analysis becomes more precise:
- Skill in bank, on submitted CV → strong match
- Skill in bank from a different CV version → keyword gap: worth adding to this CV
- Skill manually added, not on any CV → omission gap: you have this but have not documented it anywhere
- Skill not in bank at all → structural gap: you genuinely do not have this

**Standalone Summary Builder and Cover Letter Generator:**
In v3 these tools are tied to a specific analysis run. In v4 they become standalone — drawing from the skills bank directly, without requiring a prior analysis. The user can generate a summary or cover letter for any role at any time.

---

## v4 — Reduce friction
*Status: ideas*

Features that would be useful but don't belong in earlier versions because they're not foundational — they're polish.

- **Auto-populate tracker** — when an analysis is run, pre-fill a tracker entry with role, company, and JD URL; one click to confirm
- **Application analytics** — success rate by role type, score distribution over time, response rate by application channel
- **Skills bank export** — download your skills bank as PDF or Markdown
- **Multi-user support** — authentication layer enabling the tool to serve more than one user; requires moving from SQLite to Postgres

---

## What's not on the roadmap

A few things were considered and deliberately excluded:

**Automatic CV generation from scratch** — the tool generates a *reordered draft*, not a finished document. The user always owns the final polish. Removing that step would produce CVs that are optimised for ATS but not reviewed by the person whose career they represent. That's not a trade-off worth making.

**Hosted service with shared infrastructure** — running this as a multi-tenant SaaS would require storing users' CV data on a server. A CV contains some of the most sensitive personal and professional data a person has. Until there's a serious security and privacy architecture in place, the tool stays local.

**Integration with job boards** — scraping job boards at scale raises legal and ethical questions that aren't worth navigating for a personal tool. JD fetching by URL is sufficient.
