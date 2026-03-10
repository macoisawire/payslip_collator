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

# Labels already captured by extract() or that are structural document noise
# (duplicates, always-zero placeholders, layout artefacts).  Any label NOT in
# this set that carries a non-zero £ value will be returned by extra_fields().
_KNOWN_LABELS = frozenset({
    # Canonical pay components
    "Basic Pay", "SMP",
    # Canonical deductions
    "PAYE Tax", "Employee NI", "Employee Pension",
    # YTD / summary figures captured or intentionally excluded
    "TOTAL PAY", "TAXABLE PAY", "TAX",
    "N.I.EMPLOYEE", "N.I.EMPLOYER",
    "PENSION EMPLOYEE", "PENSION EMPLOYER",
    # Structural / duplicate / noise labels
    "DEDUCTIONS", "NON TAXABLE", "NATIONAL", "INSURANCE TOTAL PAY",
    # N.I'ABLE PAY — the apostrophe splits the label in the regex, producing
    # the fragment "ABLE PAY".  Both forms are excluded.
    "N.I'ABLE PAY", "ABLE PAY",
})


def _decode_cid(text: str) -> str:
    """Convert (cid:XX) sequences to their Unicode characters.
    Older Capium PDFs use CID font encoding for header labels; after decoding
    they match the same patterns used for the 2025-26 format."""
    return re.sub(r'\(cid:(\d+)\)', lambda m: chr(int(m.group(1))), text)


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
        # Older Capium PDFs (2023-24, 2024-25) encode header labels using CID
        # font sequences — decode them first so all patterns work uniformly.
        text = _decode_cid(text)
        # provider key is injected by extractor.py — not set here
        return {
            "employee_name":        self._employee_name(text),
            "employer_name":        self._employer_name(text),
            "period_label":         self._period_label(text),
            "period_date":          self._period_date(text),
            "tax_code":             self._tax_code(text),
            "ni_number":            self._ni_number(text),
            "basic_pay":            _money(text, r'Basic Pay\s+£([\d,]+\.\d{2})'),
            "smp":                  _money(text, r'SMP\s+£([\d,]+\.\d{2})'),
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
        # Title is excluded from the capture group per CLAUDE.md (strip the title).
        #
        # re.IGNORECASE: handles titles printed in all-caps (e.g. "MS" vs "Ms").
        # [\w'\xad]+: captures apostrophes (O'Sullivan) and soft hyphens (U+00AD).
        #   pdfplumber encodes the hyphen in hyphenated surnames (e.g. Capper-Smith)
        #   as \xad (soft hyphen), the same byte used as column-padding elsewhere.
        #   Adding \xad here lets "Capper\xadSmith" match as one name token;
        #   we then replace \xad with a real hyphen in the return value.
        m = re.search(
            r'(?:Mrs?|Miss|Dr|Ms)\s+([A-Z][\w\'\xad]+(?:\s+[A-Z][\w\'\xad]+)*)\s+\d{2}/\d{2}/\d{4}',
            text,
            re.IGNORECASE,
        )
        if not m:
            return None
        return m.group(1).strip().replace('\xad', '-')

    def _employer_name(self, text: str) -> str | None:
        # Line 2 sits immediately after the "EMPLOYER EMPLOYEE NAME DATE" header line.
        # We capture everything on that data line up to the first title prefix —
        # that prefix is where the employer name ends and the employee name begins.
        # re.IGNORECASE: same as _employee_name — titles may appear as "MS" not "Ms".
        m = re.search(
            r'EMPLOYER EMPLOYEE NAME DATE\n(.+?)\s+(?:Mrs?|Miss|Dr|Ms)\s+',
            text,
            re.IGNORECASE,
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
        # Tax code sits immediately before "BACS". Standard UK codes are digits
        # then a letter (e.g. "1257L"), but some codes carry a leading letter
        # prefix — e.g. "C1257L" (cumulative), "S1257L" (Scottish), "K475".
        # [A-Z]{0,2} makes the prefix optional so both forms are captured.
        # The \b word boundary still prevents a partial match against the NI
        # number earlier on the same line (tested: PK853428A cannot satisfy
        # [A-Z]{0,2}\d{3,4}[A-Z]{1,2} at a word boundary before "BACS").
        # (?:(?:M1|W1)\s+)?: some payslips include a Month 1 / Week 1 basis
        # indicator (non-cumulative emergency tax) between the tax code and BACS,
        # e.g. "C839L M1 BACS". Making it optional handles both layouts.
        return _find(text, r'\b([A-Z]{0,2}\d{3,4}[A-Z]{1,2})\s+(?:(?:M1|W1)\s+)?BACS')

    def _ni_number(self, text: str) -> str | None:
        # Line 4: "JW648535D  1257L  BACS  M 10"
        # UK NI numbers are always exactly: 2 letters + 6 digits + 1 letter.
        # Word boundaries ensure we don't partially match adjacent text.
        return _find(text, r'\b([A-Z]{2}\d{6}[A-Z])\b')

    def _total_deductions(self, text: str) -> float | None:
        # 2025-26 format: summary row "HOURS ­­ £1,561.56 £185.34"
        # \xad (U+00AD, soft hyphen) appears as column-separator padding —
        # [\s\u00ad]+ absorbs both spaces and soft hyphens.
        # Older format (2023-24, 2024-25): summary row ends "DEDUCTIONS £150.77"
        # — try the explicit label first as it is more precise.
        return (
            _money(text, r'DEDUCTIONS\s+£([\d,]+\.\d{2})')
            or _money(text, r'HOURS[\s\u00ad]+£[\d,]+\.\d{2}\s+£([\d,]+\.\d{2})')
        )

    def _take_home_pay(self, text: str) -> float | None:
        # 2025-26 format: the line before "I £1,561.56" reads "£171.68 £1,376.22"
        # "I" is Capium's Income row label — second £ on preceding line is net pay.
        # Older format (2023-24, 2024-25): structured as:
        #   "NET\nNATIONAL £89.74 £1,257.56\nPAY"
        # where the second £ value on the NATIONAL line is net pay.
        return (
            _money(text, r'£[\d,]+\.\d{2}\s+£([\d,]+\.\d{2})\nI\s+£')
            or _money(text, r'NET\nNATIONAL\s+£[\d,]+\.\d{2}\s+£([\d,]+\.\d{2})\nPAY')
        )

    def _ytd_ni_employee(self, text: str) -> float | None:
        # Older format (2023-24, 2024-25): explicitly labelled "N.I.EMPLOYEE £216.20"
        # 2025-26 format: unlabelled — appears on the line immediately after
        # "Employee Pension £41.66", anchored by that label.
        return (
            _money(text, r'N\.I\.EMPLOYEE\s+£([\d,]+\.\d{2})')
            or _money(text, r'Employee Pension\s+£[\d,]+\.\d{2}\n£([\d,]+\.\d{2})')
        )

    def extra_fields(self, text: str) -> dict:
        # Decode CID sequences first — same pre-processing as extract().
        text = _decode_cid(text)
        extras = {}
        # Scan for every "LABEL £amount" pair where LABEL starts with a capital.
        # \b after the £ amount prevents partial matches inside longer numbers.
        for m in re.finditer(r"([A-Z][A-Za-z ./'\-]+?)\s+£([\d,]+\.\d{2})\b", text):
            label = m.group(1).strip()
            if label in _KNOWN_LABELS:
                continue
            value = float(m.group(2).replace(',', ''))
            if value == 0.0:
                # Zero-value entries are structural placeholders (e.g. SAP £0.00
                # in months with no adoption pay) — skip to avoid noise.
                continue
            # Sanitise label to a valid dict key; first match wins if repeated.
            key = re.sub(r'\W+', '_', label.lower()).strip('_')
            if key not in extras:
                extras[key] = value
        return extras

    def _ytd_pension_employee(self, text: str) -> float | None:
        # Older format (2023-24, 2024-25): explicitly labelled "PENSION EMPLOYEE £177.65"
        # 2025-26 format: unlabelled — appears immediately after "SNCP £0.00",
        # anchored by that statutory pay block endpoint.
        return (
            _money(text, r'PENSION EMPLOYEE\s+£([\d,]+\.\d{2})')
            or _money(text, r'SNCP\s+£0\.00\n£([\d,]+\.\d{2})')
        )
