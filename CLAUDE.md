# Payslip Extractor — Claude Code Project Guide

## Project Overview
A local Streamlit app that accepts multiple PDF payslips, extracts structured
data using rule-based parsing (no AI, no API costs), and exports everything
into a single formatted Excel workbook for analysis.

Target users: small internal team (~5 people), same company, clean PDFs
downloaded from payroll portals.

---

## Tech Stack
- **Python 3.10+**
- **Streamlit** — UI (consistent with excel_compare project)
- **pdfplumber** — extract raw text from PDFs locally, no API calls
- **openpyxl** — build formatted Excel output
- **pandas** — intermediate data wrangling
- **re** (stdlib) — regex for field extraction within provider profiles

No external API calls. Runs entirely on the local machine. Free to operate.

---

## Project Structure
```
payslip_extractor/
├── CLAUDE.md
├── app.py                        <- Streamlit entrypoint
├── extractor.py                  <- Orchestrates PDF -> dict pipeline
├── spreadsheet.py                <- openpyxl Excel builder
├── config.py                     <- Canonical field definitions, column order
├── providers/
│   ├── __init__.py
│   ├── base.py                   <- BaseProvider abstract class
│   ├── zelt.py                   <- Zelt/Syrenis payslip profile
│   └── capium.py                 <- Capium payslip profile
└── requirements.txt
```

---

## Canonical Field Schema
These are the standardised field keys used across ALL providers.
They become the Excel column headers (bold, row 1).
Defined in config.py as an ordered list of (key, display_name) tuples.

| Field Key              | Display Name                   | Notes                     |
|------------------------|-------------------------------|---------------------------|
| provider               | Provider                      | e.g. "Zelt", "Capium"     |
| employee_name          | Employee Name                 |                           |
| employer_name          | Employer                      |                           |
| period_label           | Period                        | e.g. "Period 11", "M 10"  |
| period_date            | Pay Date                      | DD/MM/YYYY string         |
| tax_code               | Tax Code                      |                           |
| ni_number              | NI Number                     |                           |
| basic_pay              | Basic / Monthly Pay           | Gross before deductions   |
| pension_employee       | Employee Pension Contribution |                           |
| student_loan           | Student Loan Deduction        | None if not applicable    |
| ni_employee            | Employee NI                   |                           |
| paye_tax               | PAYE Tax                      |                           |
| total_deductions       | Total Deductions              |                           |
| take_home_pay          | Take Home / Net Pay           |                           |
| ni_employer            | Employer NI                   |                           |
| pension_employer       | Employer Pension              |                           |
| ytd_gross              | YTD Gross Pay                 |                           |
| ytd_taxable            | YTD Taxable Pay               |                           |
| ytd_tax_paid           | YTD Tax Paid                  |                           |
| ytd_ni_employee        | YTD Employee NI               |                           |
| ytd_pension_employee   | YTD Employee Pension          |                           |
| ytd_pension_employer   | YTD Employer Pension          |                           |

> Claude Code: always follow this column order. To add a new field, add it
> to config.py FIELDS first, then implement in all relevant provider files.

---

## Provider Profile System

### Concept
Each payroll software has a unique PDF layout. Rather than one fragile
universal parser, each provider has its own class that knows exactly how
to extract fields from that specific format.

### BaseProvider (providers/base.py)
```python
from abc import ABC, abstractmethod

class BaseProvider(ABC):
    NAME = ""  # Human-readable name shown in Streamlit selectbox

    @abstractmethod
    def extract(self, text: str) -> dict:
        """
        Accept raw text from pdfplumber.
        Return dict with keys matching config.FIELDS.
        Use None for any field not present in this format.
        Never raise — return None values for failed fields.
        """
        pass
```

### Provider Registry (providers/__init__.py)
```python
from .zelt import ZeltProvider
from .capium import CapiumProvider

PROVIDERS = {
    "Zelt": ZeltProvider,
    "Capium": CapiumProvider,
}
```

The Streamlit selectbox is populated from PROVIDERS.keys().
User selects provider once — all files in that batch use the same provider.

---

## Known Provider Formats

### Zelt (zelt.py)
- Clean label -> value layout, consistent line structure
- Labels and values appear on same or adjacent lines
- Key labels to match: "Monthly Pay", "PAYE tax",
  "National Insurance Contribution", "Pension contribution",
  "Student Loan Deduction", "Take home pay"
- Period: "Period 11" with date range "01 Feb 26 - 28 Feb 26"
- Employee name: top-left address block, first line
- Employer name: top-right block
- YTD section clearly labelled "Year to date"
- Extraction approach: regex like r"PAYE tax\s+£([\d,]+\.\d{2})"

### Capium (capium.py)
- Table-heavy layout — values are visually in columns but pdfplumber
  extracts them as a flat stream of text, NOT in visual order
- Key labels: "Basic Pay", "PAYE Tax", "Employee NI", "Employee Pension",
  "NET PAY", "TOTAL PAY", "N.I.EMPLOYEE", "N.I.EMPLOYER",
  "PENSION EMPLOYEE", "PENSION EMPLOYER"
- YTD values appear in left column of the visual layout
- Period: "M 10" format with separate date "31/01/2026"
- Employee name includes title prefix (Mrs/Mr/Miss) — strip the title
- Extraction approach: locate anchor label in text, grab the £ value
  that appears nearby in the extracted string
- WARNING: Always inspect raw pdfplumber output before writing regex.
  Visual PDF layout does NOT match text extraction order in Capium.
  Debug command:
  python -c "import pdfplumber; p=pdfplumber.open('file.pdf'); print(repr(p.pages[0].extract_text()))"

---

## extractor.py
1. Open PDF with pdfplumber
2. Extract and join text from all pages
3. Instantiate correct provider from user's selection
4. Call provider.extract(text) -> dict
5. Inject 'provider' key into returned dict
6. Return dict (or None on failure — caller handles gracefully)

---

## spreadsheet.py
- Sheet: "Payslips"
- Row 1: display names from config.FIELDS — bold, fill #D9E1F2
- Rows 2+: one row per payslip, sorted by period_date ascending
- All £ fields: number format £#,##0.00
- Auto-fit column widths
- Returns openpyxl Workbook object — do not save to disk here

---

## app.py — Streamlit UI
1. Title and one-line description
2. Provider selectbox (populated from providers.PROVIDERS)
3. Multi-file PDF uploader
4. "Process" button
5. Progress bar + per-file result (tick or warning with reason)
6. st.dataframe preview of extracted data
7. st.download_button to download the Excel file

---

## Running Locally
```bash
pip install streamlit pdfplumber openpyxl pandas
streamlit run app.py
```

No API keys. No .env file. Completely free to run.

---

## Adding a New Provider Later
1. Get a sample PDF from the provider
2. Run the debug command above to inspect raw pdfplumber text
3. Create providers/newprovider.py inheriting BaseProvider
4. Implement extract() using regex against the raw text
5. Register in providers/__init__.py
6. Test against at least 3 real payslips before considering stable

---

## Development Rules for Claude Code
- Explain reasoning before writing extraction regex — this logic must
  be understood, not just generated
- Never mix provider logic with spreadsheet logic
- Always handle missing fields as None, never crash
- Test each provider against real raw pdfplumber output
- No AI, no API calls — this must remain free to operate
- Beginner-friendly explanations throughout — explain what and why

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately — don't keep pushing
- Write plan to `tasks/todo.md` before writing any code
- Check in on the plan before starting implementation — but keep it brief, we're time-boxed

### 2. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules that prevent the same mistake recurring
- Review `tasks/lessons.md` at the start of each session

### 3. Verification Before Done
- Never mark a task complete without proving it works
- Ask: *"Would a staff engineer approve this?"*
- Run the dev server and visually verify each step before moving on

### 4. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: implement the elegant solution instead
- Skip this for simple, obvious fixes — don't over-engineer

### 5. Autonomous Bug Fixing
- When given a bug: just fix it — no hand-holding needed
- Point at logs, errors, or broken UI — then resolve them

---

## Task Management

1. **Plan First**: Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan**: Brief check-in before implementation (don't over-discuss)
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after any correction

---

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Minimal code impact.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Only touch what's necessary. Avoid introducing bugs elsewhere.