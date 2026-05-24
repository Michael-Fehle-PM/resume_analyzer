"""
test_docx.py — Test the generate_docx formatter in isolation.
No API calls, no server, no cost.

Usage:
    python test_docx.py

Outputs: test_output.docx in the same folder.
Open it in Word/LibreOffice to check formatting.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Test markdown ─────────────────────────────────────────────────────────────
# This exercises every formatting case the generator needs to handle.
# Edit this string to test specific edge cases.

TEST_MARKDOWN = """# MICHAEL FEHLE

(917) 318-7554  |  michael.fehle@protonmail.com  |  linkedin.com/in/michaelfehle

## PROFESSIONAL SUMMARY

Data-driven Senior Product Manager with a decade of experience owning core data platform capabilities in B2B and B2B2C SaaS and FinTech environments. Proven track record in full P/DLC ownership, cross-functional team leadership, and shipping high-impact platform features on time. Fluent in SQL; familiar with Mixpanel.

## AREAS OF EXPERTISE

Agile · Scrum & Sprint Planning · User Research · Data Analysis · Cross-functional Leadership · Stakeholder Engagement · Product Roadmaps · Product Strategy · Wireframing · Vendor Relationships · Process Improvement · API Testing · FinTech · SaaS

## PROFESSIONAL EXPERIENCE

### Senior Product Manager – Leads Platform & SaaS  |  Military.com / Valnet	2024 – Present

*B2C/B2B2C military recruitment platform*

- Implemented analytics infrastructure giving first-ever visibility into partner campaign performance, driving 12% improvement in lead generation
- Led distributed team of 8 engineers through Waterfall-to-Agile transition, establishing consistent 2-week delivery cadence
- Re-engineered registration flow resulting in immediate 20% uptick in sign-ups
- Designed and implemented Benefits Comparison tool adopted by 37 states' Veterans Administrations
- Revamped lead administration system, removing 90% of non-core Product work and enabling business users to self-serve

### Principal Product Manager  |  Optimizely, Inc.	2021 – 2023

*B2B/B2C SaaS eCommerce optimisation platform*

- Led Asia-Pacific data-residency initiative, enabling $1m in revenue recognition and $100k+ in early bookings – delivered ahead of deadline
- Worked with data science team to develop vector search capability – 23% uplift in customer spend, increasing to 42% after 6 months
- Averted $600k in ARR churn by delivering customer-critical PII-masking project 2 weeks ahead of schedule
- Launched Real-Time Audience feature resulting in 17% increase in use of experimentation tools
- Mentored and coached 3 junior PMs in agile methodology, communications, and expectation-setting

### Product Manager  |  CrossBorder Solutions	2021

*SaaS provider of transfer pricing tax solutions*

- Raised data integrity to >95% across the data-enrichment process by developing robust QC/QA processes
- Improved accuracy of historical data by 72% through data-reprocessing initiative
- Reduced Tagging team downtime from 5 days/month to <1 by implementing pre-release testing protocols
- Reduced turnaround time for tagging requests from 10 days to 3 by developing Jira service portal

### Senior Product Manager  |  Diligent Corporation	2020

*SaaS provider of collaborative board solutions*

- Contributed to 17% increase in application sales by overhauling UI and collaborating with content teams
- Responsible for 10% increase in user engagement through user behaviour analysis
- Instrumental in retaining 96% of customers from acquired file-sharing product

### Vice President – Product Management  |  Clearpool Group, Inc.	2018 – 2019

*Independent agency broker-dealer; first PM hire*

- Decreased development cycle by 15% and reduced developer workload by 25% by creating detailed wireframes
- Increased product engagement by 12% and trading volumes by 10% through in-depth user-base analysis
- Grew customer base by 8% by collaborating with marketing/sales on materials communicating product value

### Product Manager  |  Nasdaq, Inc.	2014 – 2018

*Securities-data components of IRInsight, Nasdaq's $25m flagship IR platform*

- Reduced customer churn by 52% by developing reporting tools for tracking platform usage and revenue
- Delivered cost-savings of $50k+ by devising and implementing security symbol methodology
- Received CEO Award for development of Quote Monitor and Charting modules

## SKILLS

**PM Tools:**	Jira, Confluence, Aha!, VersionOne
**Analytics:**	SQL, Mixpanel, Postman (API testing)
**Wireframing:**	Balsamiq
**AI / Tech:**	Claude AI, Python, LLM experience (Llama)
**Productivity:**	MS Office (Excel – expert)
**Languages:**	French (strong spoken), German (strong spoken)

## EDUCATION

BA European Languages & Business  ·  Leeds Metropolitan University, England
Cambridge CELTA  ·  University of Cambridge, England
"""


def mock_reorder_cv(cv_text, jd_text):
    """Returns the test markdown directly, bypassing the API call."""
    return {"html": "", "markdown": TEST_MARKDOWN}


# Monkey-patch reorder_cv before importing generate_docx
import backend.analyser as analyser
analyser.reorder_cv = mock_reorder_cv

# Now call generate_docx with dummy inputs
print("Generating test_output.docx...")
docx_bytes = analyser.generate_docx("dummy cv", "dummy jd")

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output.docx")
with open(output_path, "wb") as f:
    f.write(docx_bytes)

print(f"Done — saved to {output_path}")
print("Open test_output.docx to check the formatting.")
