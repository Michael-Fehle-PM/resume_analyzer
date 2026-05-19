# Resume Analyser

A personal tool I built to solve a real problem: the tedious, repetitive work of tailoring a CV to each job application.

As a product manager in active job search, I found myself manually cross-referencing job descriptions, reordering bullet points, and trying to guess how well my experience matched what a recruiter's ATS system was looking for. So I built a tool to do that analytical work for me — freeing up time to focus on the parts that actually require human judgement.

![Resume Analyser screenshot](screenshots/analyser.png)

---

## The problem

Job searching PMs face a specific workflow problem:

- Every application ideally needs a tailored CV with the most relevant experience surfaced first
- ATS systems screen out candidates before a human ever reads the CV
- Manually reordering bullets and cross-referencing JDs is time-consuming and inconsistent
- Tracking applications, interview notes, and follow-ups across a job search is scattered and fragile

Most tools solve one of these. This solves all of them in one place.

---

## What it does

### CV Analyser
- Upload one or more CVs as PDF (server-side text extraction)
- Paste or auto-fetch a job description by URL
- AI-powered match analysis returns:
  - Three scores: overall match, keyword match, experience match
  - Categorised **matches**, **partial matches**, and **gaps** — each rated by importance
  - A plain-English summary assessment
- Reorders experience bullets within each role so the most JD-relevant appear first
- Exports the reordered CV as **HTML** (print-to-PDF ready), **Markdown**, or **.docx**

### Job Tracker
- Log applications with role, company, JD URL, date, and status
- Six status options: Applied, Interview, Offer, Rejected, No response, Withdrawn
- Add and update interview notes and feedback
- Full edit and delete
- Data persists locally via SQLite — no cloud, no account, no data sharing

![Job Tracker screenshot](screenshots/tracker.png)

---

## Product decisions worth noting

**Why a webapp rather than a script?**
A CLI tool would have been faster to build, but the insight/action loop — upload CV, read analysis, download reordered output — is inherently visual. A UI makes the workflow faster and the output more immediately usable.

**Why server-side rather than client-side API calls?**
Browser-based API calls expose keys and are blocked by CORS on most job boards. Server-side calls solve both problems and allow proper PDF extraction, which the browser can't do reliably.

**Why SQLite?**
For a personal tool running locally, SQLite is zero-config and perfectly sufficient. The schema and ORM layer (SQLAlchemy) mean it's a one-line change to switch to Postgres if the tool were ever hosted or multi-user.

**Why both HTML and Markdown output?**
Different users have different next steps. HTML is immediately printable to PDF. Markdown drops cleanly into Word via Pandoc or Google Docs for users who want to polish the formatting before sending.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| AI | Anthropic Claude API (claude-sonnet-4-6) |
| PDF extraction | pdfplumber |
| Database | SQLite via SQLAlchemy |
| .docx generation | python-docx |
| HTTP client | httpx |
| Frontend | Plain HTML, CSS, JavaScript (no framework) |

---

## Requirements

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

> **Important:** Each user must supply their own Anthropic API key. The key is stored locally in a `.env` file that is git-ignored and never committed. It is never shared, logged, or transmitted anywhere other than directly to the Anthropic API.
>
> Anthropic API usage is pay-as-you-go. A typical analysis costs approximately $0.02–0.05. You can set a spend cap in the [Anthropic console](https://console.anthropic.com/) to avoid surprises. A $5 credit covers 100–250 analyses.

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/resume-analyser.git
cd resume-analyser
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> If any packages fail on Python 3.14 (wheels not yet published for the newest release), try Python 3.12 instead:
> ```bash
> python3.12 -m venv .venv
> ```

### 4. Add your API key

```bash
cp .env.example .env
```

Open `.env` and replace `your_api_key_here` with your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=sqlite:///./resumeapp.db
```

### 5. Run

```bash
uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

---

## Project structure

```
resume-analyser/
├── main.py                    # FastAPI app and all routes
├── backend/
│   ├── analyser.py            # Claude API calls — analysis, reorder, skills scrape
│   ├── pdf_utils.py           # Server-side PDF text extraction
│   └── database.py            # SQLAlchemy models and DB initialisation
├── frontend/
│   ├── templates/
│   │   └── index.html         # Single-page UI — no framework
│   └── static/
│       └── favicon.png
├── screenshots/               # Add your own screenshots here
├── requirements.txt
├── .env.example               # Safe to commit — contains no real credentials
├── .gitignore                 # Ensures .env and .db are never committed
└── README.md
```

---

## Deploying (optional)

The app runs perfectly as a local tool. If you want to access it from anywhere:

1. Push the repo to GitHub
2. Connect to [Railway](https://railway.app) or [Render](https://render.com) — both detect FastAPI automatically
3. Set `ANTHROPIC_API_KEY` in the platform's environment variables dashboard
4. Deploy

To use Postgres instead of SQLite in production, update `DATABASE_URL`:
```
DATABASE_URL=postgresql://user:password@host/dbname
```
No code changes required — SQLAlchemy handles the rest.

---

## Security notes

- The `.env` file is git-ignored and will never be committed
- The SQLite database file is also git-ignored
- API keys are passed directly to the Anthropic API and are never logged or stored
- The app runs locally by default — no data leaves your machine except the CV/JD text sent to the Anthropic API for analysis

---

## Other tools in this repo

This repo also contains a set of lightweight data utilities built for similar reasons — tools I needed, built quickly:

- **Messy data parser** — normalises and structures inconsistently formatted input data
- **Data generator** — generates realistic test datasets for development and QA
- **Data analyser** — quick statistical profiling of tabular data

These reflect the same philosophy as the resume analyser: identify a friction point, build the minimum useful tool, move on.

---

## Licence

MIT — use it, fork it, improve it.
