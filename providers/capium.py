# providers/capium.py
# Provider profile for Capium payslips.
#
# Layout notes from pdfplumber inspection:
#   - Line 2: "Employer Name  Title FirstName Surname  DD/MM/YYYY" — all on one line, no delimiter
#   - Line 4: "NI_NUMBER  TAX_CODE  BACS  M 10" — period label follows BACS
#   - \xad (soft hyphen, U+00AD) appears as column padding on the HOURS summary row
#   - Several YTD values are unlabelled standalone £ lines; we only extract ones we can verify
#   - ni_employer, pension_employer, ytd_taxable, ytd_pension_employer are absent from this format

import re
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


class CapiumProvider(BaseProvider):
    NAME = "Capium"

    def extract(self, text: str) -> dict:
        # provider key is injected by extractor.py — not set here
        return {
            "employee_name":        self._employee_name(text),
            "employer_name":        self._employer_name(text),
            "period_label":         self._period_label(text),
            "period_date":          self._period_date(text),
            "tax_code":             self._tax_code(text),
            "ni_number":            self._ni_number(text),
            "basic_pay":            _money(text, r'Basic Pay\s+£([\d,]+\.\d{2})'),
            "pension_employee":     _money(text, r'Employee Pension\s+£([\d,]+\.\d{2})'),
            "student_loan":         None,  # Not present in Capium format
            "ni_employee":          _money(text, r'Employee NI\s+£([\d,]+\.\d{2})'),
            "paye_tax":             _money(text, r'PAYE Tax\s+£([\d,]+\.\d{2})'),
            "total_deductions":     self._total_deductions(text),
            "take_home_pay":        self._take_home_pay(text),
            "ni_employer":          None,  # Not present in Capium format
            "pension_employer":     None,  # Not present in Capium format
            "ytd_gross":            _money(text, r'TOTAL PAY\s+£([\d,]+\.\d{2})'),
            "ytd_taxable":          None,  # N.I'ABLE PAY is present but is NI-able earnings, not taxable pay
            "ytd_tax_paid":         _money(text, r'\nTAX\s+£([\d,]+\.\d{2})'),
            "ytd_ni_employee":      self._ytd_ni_employee(text),
            "ytd_pension_employee": self._ytd_pension_employee(text),
            "ytd_pension_employer": None,  # Not present in Capium format
        }

    # -------------------------------------------------------------------------
    # Field extractors — each has a comment explaining the anchoring logic
    # -------------------------------------------------------------------------

    def _employee_name(self, text: str) -> str | None:
        # Line 2: "Townley & Co Ltd  Mrs Amy Louise McDonnell  31/01/2026"
        # The employee name starts with a title prefix (Mrs/Mr/Miss/Dr/Ms).
        # We match from the title through all capitalised name words, stopping
        # just before the DD/MM/YYYY date that ends the line.
        # This correctly excludes the employer name before the title.
        m = re.search(
            r'((?:Mrs?|Miss|Dr|Ms)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\d{2}/\d{2}/\d{4}',
            text
        )
        return m.group(1).strip() if m else None

    def _employer_name(self, text: str) -> str | None:
        # Line 2 sits immediately after the "EMPLOYER EMPLOYEE NAME DATE" header line.
        # We capture everything on that data line up to the first title prefix —
        # that prefix is where the employer name ends and the employee name begins.
        m = re.search(
            r'EMPLOYER EMPLOYEE NAME DATE\n(.+?)\s+(?:Mrs?|Miss|Dr|Ms)\s+',
            text
        )
        return m.group(1).strip() if m else None

    def _period_label(self, text: str) -> str | None:
        # Line 4: "JW648535D  1257L  BACS  M 10"
        # The period is "M 10" (month 10). We anchor to "BACS" because it always
        # appears immediately before the period label and is unambiguous.
        return _find(text, r'BACS\s+(M\s+\d+)')

    def _period_date(self, text: str) -> str | None:
        # The pay date "31/01/2026" appears on the header line (line 2).
        # It is the only DD/MM/YYYY formatted date in the document, so a
        # bare date pattern is sufficient and safe.
        return _find(text, r'(\d{2}/\d{2}/\d{4})')

    def _tax_code(self, text: str) -> str | None:
        # Line 4: "JW648535D  1257L  BACS  M 10"
        # Tax code is a 3–4 digit number immediately followed by a letter,
        # sitting just before "BACS". The \b word boundary prevents partial
        # matches inside the NI number (which also contains digits) earlier
        # on the same line.
        return _find(text, r'\b(\d{3,4}[A-Z])\s+BACS')

    def _ni_number(self, text: str) -> str | None:
        # Line 4: "JW648535D  1257L  BACS  M 10"
        # UK NI numbers are always exactly: 2 letters + 6 digits + 1 letter.
        # Word boundaries ensure we don't partially match adjacent text.
        return _find(text, r'\b([A-Z]{2}\d{6}[A-Z])\b')

    def _total_deductions(self, text: str) -> float | None:
        # The summary row reads: "£324.20  HOURS  ­­  £1,561.56  £185.34"
        # \xad (U+00AD, soft hyphen) appears between HOURS and the gross figure
        # as column-separator padding — [\s\u00ad]+ absorbs both spaces and
        # soft hyphens so the pattern doesn't break on them.
        # The value after the gross pay figure (£1,561.56) is total deductions.
        # Cross-check: PAYE £102.60 + NI £41.08 + Pension £41.66 = £185.34 ✓
        return _money(text, r'HOURS[\s\u00ad]+£[\d,]+\.\d{2}\s+£([\d,]+\.\d{2})')

    def _take_home_pay(self, text: str) -> float | None:
        # The line before "I £1,561.56" reads: "£171.68  £1,376.22"
        # "I" is Capium's row label for Income — it marks the end of the pay summary.
        # The second £ value on the preceding line is the net pay.
        # Cross-check: £1,561.56 gross - £185.34 deductions = £1,376.22 ✓
        return _money(text, r'£[\d,]+\.\d{2}\s+£([\d,]+\.\d{2})\nI\s+£')

    def _ytd_ni_employee(self, text: str) -> float | None:
        # After "Employee Pension £41.66\n" the very next line is "£458.06" —
        # this is the YTD employee NI figure (unlabelled in the PDF).
        # We anchor on the Employee Pension line above it since that label is
        # unambiguous; the standalone £ value on the immediately following line
        # is reliably the YTD NI employee figure.
        # Plausibility: period NI £41.08 × ~11 periods ≈ £452–458 ✓
        return _money(text, r'Employee Pension\s+£[\d,]+\.\d{2}\n£([\d,]+\.\d{2})')

    def _ytd_pension_employee(self, text: str) -> float | None:
        # After the statutory pay block (SAP/SPP/SSP/SMP/SNCP — all £0.00),
        # "SNCP £0.00\n" is the last entry before the YTD pension employee figure.
        # We anchor on "SNCP £0.00\n" because it's the most stable endpoint of
        # that block; the standalone £ value immediately after is YTD pension.
        # Plausibility: £41.66/month × ~10 periods ≈ £416–432 ✓
        return _money(text, r'SNCP\s+£0\.00\n£([\d,]+\.\d{2})')
