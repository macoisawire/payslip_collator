# providers/zelt.py
# Provider profile for Zelt (Syrenis) payslips.
#
# Layout notes from pdfplumber inspection:
#   - Line 1: "Employee Name  Employer Name" — both on the same line, split by company suffix
#   - No title prefix (Mrs/Mr) on employee name — Zelt omits it
#   - Period label is "Period 11"; date is a range "01 Feb 26 - 28 Feb 26" (not DD/MM/YYYY)
#   - Pension and student loan values carry a leading minus sign (-£) — stored as positive floats
#   - basic_pay = Monthly Pay (gross before deductions), NOT Income (which is post-pension)
#   - Employer NI and YTD taxable income share a single line; YTD employer pension and YTD tax paid share a line
#   - ytd_gross is absent — "Taxable income" is YTD taxable, not YTD gross
#   - All labelled fields in "Your details" section are clean single-value matches

import re
from datetime import datetime
from .base import BaseProvider


def _money(text: str, pattern: str) -> float | None:
    """Find pattern in text, strip £ formatting from group(1), return as float.
    Returns None if pattern does not match."""
    m = re.search(pattern, text)
    if not m:
        return None
    return float(m.group(1).replace(',', ''))


def _find(text: str, pattern: str, flags: int = 0) -> str | None:
    """Find pattern in text, return stripped group(1) string.
    Returns None if pattern does not match."""
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


class ZeltProvider(BaseProvider):
    NAME = "Zelt"

    def extract(self, text: str) -> dict:
        # provider key is injected by extractor.py — not set here
        return {
            "employee_name":        self._employee_name(text),
            "employer_name":        self._employer_name(text),
            "period_label":         self._period_label(text),
            "period_date":          self._period_date(text),
            "tax_code":             self._tax_code(text),
            "ni_number":            self._ni_number(text),
            "basic_pay":            _money(text, r'Monthly Pay\s+£([\d,]+\.\d{2})'),
            "pension_employee":     _money(text, r'Pension contribution\s+-£([\d,]+\.\d{2})'),
            "student_loan":         _money(text, r'Student Loan Deduction\s+-£([\d,]+\.\d{2})'),
            "ni_employee":          _money(text, r'National Insurance Contribution\s+£([\d,]+\.\d{2})'),
            "paye_tax":             _money(text, r'PAYE tax\s+£([\d,]+\.\d{2})'),
            "total_deductions":     _money(text, r'^Deductions\s+£([\d,]+\.\d{2})', re.MULTILINE),
            "take_home_pay":        _money(text, r'Take home pay\s+£([\d,]+\.\d{2})'),
            "ni_employer":          self._ni_employer(text),
            "pension_employer":     _money(text, r'\nPension\s+£([\d,]+\.\d{2})\s+Tax paid'),
            "ytd_gross":            None,  # Not present — Zelt only shows ytd_taxable, not ytd_gross
            "ytd_taxable":          _money(text, r'Taxable income\s+£([\d,]+\.\d{2})'),
            "ytd_tax_paid":         _money(text, r'Tax paid\s+£([\d,]+\.\d{2})'),
            "ytd_ni_employee":      _money(text, r'Employee National Insurance\s+£([\d,]+\.\d{2})'),
            "ytd_pension_employee": _money(text, r'Employee Pension Contribution\s+£([\d,]+\.\d{2})'),
            "ytd_pension_employer": _money(text, r'Employer Pension Contribution\s+£([\d,]+\.\d{2})'),
        }

    # -------------------------------------------------------------------------
    # Field extractors — each has a comment explaining the anchoring logic
    # -------------------------------------------------------------------------

    def _employee_name(self, text: str) -> str | None:
        # Line 1: "Dan McDonnell Syrenis Limited"
        # Zelt omits title prefixes, so we can't split on Mrs/Mr as Capium does.
        # Instead, we anchor on common UK company suffixes to locate where the
        # employer name starts, and capture everything before it as the employee name.
        # (.+?) is non-greedy so it stops at the earliest possible company-suffix match.
        m = re.search(
            r'^(.+?)\s+[A-Z][a-zA-Z& .]+(?:Limited|Ltd|LLP|plc|PLC|Inc)\s*$',
            text, re.MULTILINE
        )
        return m.group(1).strip() if m else None

    def _employer_name(self, text: str) -> str | None:
        # Same line 1 as employee name.
        # Capture the company-suffixed name at the end of the first line.
        # [A-Z][a-zA-Z& .]+ allows for names like "Syrenis", "Townley & Co".
        m = re.search(
            r'^[A-Z][a-z]+ [A-Z][a-z]+\s+([A-Z][a-zA-Z& .]+(?:Limited|Ltd|LLP|plc|PLC|Inc))\s*$',
            text, re.MULTILINE
        )
        return m.group(1).strip() if m else None

    def _period_label(self, text: str) -> str | None:
        # Line: "Period 11 £3,610.25"
        # We anchor on the £ that follows the period number — this ensures we
        # capture "Period 11" and not any other occurrence of the word "Period".
        return _find(text, r'(Period\s+\d+)\s+£')

    def _period_date(self, text: str) -> str | None:
        # Line: "01 Feb 26 - 28 Feb 26 You have been paid"
        # Zelt shows a date range, not a single pay date. We take the END date
        # (right side of the dash) as the canonical pay date, matching Capium's
        # convention of using the last day of the pay period.
        # strptime '%d %b %y' parses "28 Feb 26"; strftime gives "28/02/2026".
        m = re.search(r'\d{2}\s+\w{3}\s+\d{2}\s*-\s*(\d{2}\s+\w{3}\s+\d{2})', text)
        if not m:
            return None
        try:
            return datetime.strptime(m.group(1).strip(), '%d %b %y').strftime('%d/%m/%Y')
        except ValueError:
            return None

    def _tax_code(self, text: str) -> str | None:
        # "Your details" section: "Tax Code 1256L"
        # Explicit label makes this unambiguous — no risk of matching other numbers.
        return _find(text, r'Tax Code\s+(\d{3,4}[A-Z])')

    def _ni_number(self, text: str) -> str | None:
        # "Your details" section: "NI Number JR047042C"
        # Anchoring on the "NI Number" label is safer than a bare NI pattern
        # since it avoids any accidental match against the payroll code digits.
        return _find(text, r'NI Number\s+([A-Z]{2}\d{6}[A-Z])\b')

    def _ni_employer(self, text: str) -> float | None:
        # The "Employer contributions" block reads:
        #   "Employer contributions Year to date\nNational Insurance £713.11 ..."
        # "National Insurance" appears three times in the document:
        #   1. "National Insurance £713.11"        ← employer NI (this period) — WANT THIS
        #   2. "Employee National Insurance £2,980.12" ← YTD employee NI
        #   3. "Employer National Insurance £7,844.21" ← YTD employer NI
        # We anchor to the header line so we only match the first occurrence,
        # which is employer NI for the current period.
        return _money(
            text,
            r'Employer contributions Year to date\nNational Insurance\s+£([\d,]+\.\d{2})'
        )
