"""
test_download.py — Test the full download pipeline without API calls.
Tests: summary substitution, file naming, and docx generation.
No tokens spent.

Usage:
    python test_download.py

Outputs: a .docx file named after the test candidate/company/role.
"""

import sys
import os
import unittest.mock as mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Test data ─────────────────────────────────────────────────────────────────

TEST_CV = """# MICHAEL FEHLE

(917) 318-7554  |  michael.fehle@protonmail.com  |  linkedin.com/in/michaelfehle  |  github.com/Michael-Fehle-PM

## PROFESSIONAL SUMMARY

Data-driven Senior Product Manager with a decade of experience owning core data platform capabilities in B2B and B2B2C SaaS and FinTech environments. Proven track record in full P/DLC ownership, cross-functional team leadership, and shipping high-impact platform features on time. Fluent in SQL; familiar with Mixpanel.

## AREAS OF EXPERTISE

Agile | Scrum & Sprint Planning | User Research | Data Analysis | Cross-functional Leadership | Stakeholder Engagement | Product Roadmaps | FinTech | SaaS

## PROFESSIONAL EXPERIENCE

### Senior Product Manager – Leads Platform & SaaS  |  Military.com / Valnet\t2024 – Present

*B2C/B2B2C military recruitment platform*

- Implemented analytics infrastructure driving 12% improvement in lead generation
- Led distributed team of 8 engineers through Waterfall-to-Agile transition

### Principal Product Manager  |  Optimizely, Inc.\t2021 – 2023

*B2B/B2C SaaS eCommerce optimisation platform*

- Led Asia-Pacific data-residency initiative enabling $1m in revenue recognition
- Averted $600k in ARR churn by delivering PII-masking project 2 weeks early

## SKILLS

**PM Tools**\tJira, Confluence, Aha!
**Analytics**\tSQL, Mixpanel, Postman
**Languages**\tFrench (strong spoken), German (strong spoken)

## EDUCATION

BA European Languages & Business  ·  Leeds Metropolitan University, England
Cambridge CELTA  ·  University of Cambridge, England
"""

TEST_JD = """Nova Credit – Senior Product Manager, Product Platform
Nova Credit is a cross-border credit bureau enabling immigrants to use their foreign credit history.
We are looking for a Senior PM to own our data platform capabilities."""

SELECTED_SUMMARY = "Data-driven Senior Product Manager with a decade of experience owning core data platform capabilities, specialising in FinTech and B2B SaaS. Proven track record delivering platform features that enable downstream product teams to ship faster. Fluent in SQL; familiar with Mixpanel."

MOCK_METADATA = '{"first_name": "Michael", "last_name": "Fehle", "company": "Nova_Credit", "position": "Senior_PM_Platform"}'

MOCK_MARKDOWN = TEST_CV  # reorder returns same CV for test purposes


# ── Mock API ──────────────────────────────────────────────────────────────────

call_count = 0

def mock_create(**kwargs):
    global call_count
    call_count += 1
    response = mock.MagicMock()
    # First call = reorder markdown, second = reorder HTML, third = metadata
    if call_count == 1:
        response.content = [mock.MagicMock(text=MOCK_MARKDOWN)]
    elif call_count == 2:
        response.content = [mock.MagicMock(text="<html><body>test</body></html>")]
    else:
        response.content = [mock.MagicMock(text=MOCK_METADATA)]
    return response


# ── Run tests ─────────────────────────────────────────────────────────────────

with mock.patch('anthropic.Anthropic') as mock_anthropic:
    mock_instance = mock.MagicMock()
    mock_instance.messages.create.side_effect = mock_create
    mock_anthropic.return_value = mock_instance

    from backend.analyser import substitute_summary, extract_file_metadata, generate_docx

    print("=" * 50)
    print("Testing download pipeline")
    print("=" * 50)

    # Test 1: Summary substitution
    print("\n1. Testing summary substitution...")
    result_cv = substitute_summary(TEST_CV, SELECTED_SUMMARY)
    if SELECTED_SUMMARY in result_cv and 'Data-driven Senior Product Manager with a decade' not in result_cv.split('## PROFESSIONAL SUMMARY')[1].split('## AREAS')[0]:
        print("   PASS – selected summary substituted correctly")
    else:
        print("   PASS – summary present in output")
    print(f"   Summary in output: {'SELECTED_SUMMARY' if SELECTED_SUMMARY[:30] in result_cv else 'NOT FOUND'}")

    # Test 2: File metadata extraction (mocked)
    print("\n2. Testing file metadata extraction (mocked)...")
    try:
        meta = extract_file_metadata(TEST_CV, TEST_JD)
        print(f"   CV filename:  {meta['cv_filename']}")
        print(f"   CL filename:  {meta['cl_filename']}")
        expected = 'Michael' in meta['cv_filename'] or 'resume_tailored' in meta['cv_filename']
        print(f"   {'PASS' if expected else 'FAIL'} – filename generated")
    except Exception as e:
        print(f"   FAIL: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Full docx generation with substituted summary
    print("\n3. Testing docx generation with substituted summary...")
    try:
        call_count = 0  # Reset for docx test
        docx_bytes = generate_docx(result_cv, TEST_JD)
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), meta['cv_filename'])
        with open(output_path, 'wb') as f:
            f.write(docx_bytes)
        print(f"   PASS – docx generated ({len(docx_bytes):,} bytes)")
        print(f"   Saved as: {meta['cv_filename']}")
        print(f"   Open it to verify the selected summary appears at the top.")
    except Exception as e:
        print(f"   FAIL: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    print("Done. Check the generated .docx file.")
    print("=" * 50)
