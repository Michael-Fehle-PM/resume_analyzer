"""
test_reorder.py — Test the reorder_cv function in isolation.
Mocks the Claude API call so no tokens are spent.

Usage:
    python test_reorder.py

Prints the markdown output to console.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the anthropic client before importing analyser
import unittest.mock as mock

MOCK_MARKDOWN = """# MICHAEL FEHLE

(917) 318-7554  |  michael.fehle@protonmail.com  |  linkedin.com/in/michaelfehle  |  github.com/Michael-Fehle-PM

## PROFESSIONAL SUMMARY

Data-driven Senior Product Manager with a decade of experience.

## AREAS OF EXPERTISE

Agile | Scrum & Sprint Planning | User Research | Data Analysis | FinTech | SaaS

## PROFESSIONAL EXPERIENCE

### Senior Product Manager  |  Military.com / Valnet	2024 – Present

*B2C/B2B2C military recruitment platform*

- Implemented analytics infrastructure driving 12% improvement in lead generation
- Led distributed team of 8 engineers through Waterfall-to-Agile transition

## SKILLS

**PM Tools**	Jira, Confluence, Aha!
**Analytics**	SQL, Mixpanel

## EDUCATION

BA European Languages & Business  ·  Leeds Metropolitan University, England
Cambridge CELTA  ·  University of Cambridge, England
"""

MOCK_HTML = "<html><body><h1>MICHAEL FEHLE</h1></body></html>"

# Create a mock message response
mock_response = mock.MagicMock()
mock_response.content = [mock.MagicMock(text=MOCK_MARKDOWN)]

mock_response_html = mock.MagicMock()
mock_response_html.content = [mock.MagicMock(text=MOCK_HTML)]

call_count = 0

def mock_create(**kwargs):
    global call_count
    call_count += 1
    # First call returns markdown, second returns HTML
    if call_count % 2 == 1:
        return mock_response
    else:
        return mock_response_html

# Patch anthropic before import
with mock.patch('anthropic.Anthropic') as mock_anthropic:
    mock_instance = mock.MagicMock()
    mock_instance.messages.create.side_effect = mock_create
    mock_anthropic.return_value = mock_instance

    import backend.analyser as analyser

    print("Testing reorder_cv function...")
    try:
        result = analyser.reorder_cv("dummy cv text", "dummy jd text")
        print("SUCCESS!")
        print(f"Keys returned: {list(result.keys())}")
        print(f"Markdown length: {len(result.get('markdown', ''))}")
        print(f"HTML length: {len(result.get('html', ''))}")
        print()
        print("=== MARKDOWN OUTPUT ===")
        print(result.get('markdown', ''))
    except Exception as e:
        import traceback
        print(f"FAILED: {e}")
        traceback.print_exc()
