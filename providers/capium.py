# providers/capium.py
# Provider profile for Capium payslips.
#
# Layout notes from pdfplumber inspection:
#   - Line 2: "Employer Name  Title FirstName Surname  DD/MM/YYYY" — all on one line, no delimiter
#   - Line 4: "NI_NUMBER  TAX_CODE  BACS  M 10" — period label follows BACS
#   - \xad (soft hyphen, U+00AD) appears as column padding on the HOURS summary row
#   - Several YTD values are unlabelled standalone £ lines; we only extract ones we can verify
#   - pension_employer, ytd_taxable, ytd_pension_employer are absent from this format
#   - ni_employer is unlabelled: first £ value on the line just above the "I £gross" row

import re
from .base import BaseProvider

# Labels already captured by extract() or that are structural document noise
# (duplicates, always-zero placeholders, layout artefacts).  Any label NOT in
# this set that carries a non-zero £ value will be returned by extra_fields().
_KNOWN_LABELS = frozenset({
    # Canonical pay components
    "Basic Pay", "SMP",
    # Canonical earnings extras (now in schema)
    "Car Allowance", "On Call", "Kit Pay", "Holiday Exchange",
    "Salary Adj", "Salary Maternity Adj", "Salary Maternity ADJ", "SMP Top Up",
    "ERE Pension Pay", "RAF Pay", "Carers Leave",
    # Canonical deductions (now in schema)
    "Healthcare", "Child Healthcare", "Postgraduate Loan",
    "Car Salary Sacrifice", "Pension Payment", "WPR Pension",
    # RAF = Refer a Friend bonus — earning, kept positive, excluded from double-count
    "RAF",
    # Canonical deductions
    "PAYE Tax", "Employee NI", "Employee Pension", "Student Loan",
    # salary_adj appears with both capitalisation variants in Capium PDFs
    "Salary adj",
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
    Also handles accounting-negative notation: (£168.60) → -168.60.
    Returns None if pattern does not match in either form."""
    m = re.search(pattern, text)
    if m:
        return float(m.group(1).replace(',', ''))
    # Try accounting-negative variant: insert \( before £ and \) after the
    # capture group.  The two replacements are precise string operations:
    #   £(  →  \(£(   adds the opening bracket requirement before the currency
    #   \.\d{2})  →  \.\d{2})\)   adds the closing bracket requirement after
    #                               the capture group (first occurrence only)
    neg = pattern.replace('£(', r'\(£(', 1)
    if neg != pattern:
        neg = neg.replace(r'\.\d{2})', r'\.\d{2})\)', 1)
        m = re.search(neg, text)
        if m:
            return -float(m.group(1).replace(',', ''))
    return None


def _find(text: str, pattern: str, flags: int = 0) -> str | None:
    """Find pattern in text, return stripped group(1) string.
    Returns None if pattern does not match."""
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def _deduct(text: str, pattern: str) -> float | None:
    """Extract a monetary value and return it as negative (deduction sign convention).
    Handles both plain values (Employee NI £0.00) and accounting-negative brackets
    ((£168.60)) — both become negative, consistent with deductions column convention."""
    val = _money(text, pattern)
    return -abs(val) if val is not None else None


class CapiumProvider(BaseProvider):
    NAME = "Capium"

    # Fields excluded from the Capium export per client request (March 2026).
    # These columns are suppressed in both the preview table and the Excel download.
    EXCLUDED_FIELDS: frozenset[str] = frozenset({
        "pension_employee",
        "ytd_gross",
        "ytd_taxable",
        "ytd_tax_paid",
        "ytd_ni_employee",
        "ytd_pension_employee",
        "ytd_pension_employer",
    })

    def extract(self, text: str) -> dict:
        # Older Capium PDFs (2023-24, 2024-25) encode header labels using CID
        # font sequences — decode them first so all patterns work uniformly.
        text = _decode_cid(text)
        # Some Capium PDF font variants map the pound sign glyph to U+00FA (ú, 0xfa)
        # instead of the standard U+00A3 (£, 0xa3).  Normalise here so all £
        # patterns match regardless of which encoding the PDF uses.
        text = text.replace('\xfa', '\xa3')
        # Pre-compute total_deductions so we can apply -abs() cleanly in the dict.
        _td = self._total_deductions(text)
        # provider key is injected by extractor.py — not set here
        return {
            "employee_name":        self._employee_name(text),
            "employer_name":        self._employer_name(text),
            "period_label":         self._period_label(text),
            "period_date":          self._period_date(text),
            "tax_code":             self._tax_code(text),
            "ni_number":            self._ni_number(text),
            # Earnings — positive values
            "basic_pay":            _money(text, r'Basic Pay\s+£([\d,]+\.\d{2})'),
            "smp":                  _money(text, r'SMP\s+£([\d,]+\.\d{2})'),
            "car_allowance":        _money(text, r'Car Allowance\s+£([\d,]+\.\d{2})'),
            "on_call":              _money(text, r'On Call\s+£([\d,]+\.\d{2})'),
            "kit_pay":              _money(text, r'Kit Pay\s+£([\d,]+\.\d{2})'),
            "holiday_exchange":     _money(text, r'Holiday Exchange\s+£([\d,]+\.\d{2})'),
            "salary_adj":           _money(text, r'(?i)Salary Adj\s+£([\d,]+\.\d{2})'),
            "salary_maternity_adj": self._salary_maternity_adj(text),
            "smp_top_up":           _money(text, r'SMP Top Up\s+£([\d,]+\.\d{2})'),
            "ere_pension_pay":      _money(text, r'ERE Pension Pay\s+£([\d,]+\.\d{2})'),
            "raf_pay":              _money(text, r'RAF Pay\s+£([\d,]+\.\d{2})'),
            "carers_leave":         _money(text, r'Carers Leave\s+£([\d,]+\.\d{2})'),
            # Deductions — stored as negative values (deduction sign convention)
            "pension_employee":     None,  # Excluded from Capium export (client request, March 2026)
            "student_loan":         _deduct(text, r'Student Loan\s+£([\d,]+\.\d{2})'),
            "healthcare":           _deduct(text, r'Healthcare\s+£([\d,]+\.\d{2})'),
            "child_healthcare":     _deduct(text, r'Child Healthcare\s+£([\d,]+\.\d{2})'),
            "postgraduate_loan":    _deduct(text, r'Postgraduate Loan\s+£([\d,]+\.\d{2})'),
            "car_salary_sacrifice": _deduct(text, r'Car Salary Sacrifice\s+£([\d,]+\.\d{2})'),
            "pension_payment":      _deduct(text, r'Pension Payment\s+£([\d,]+\.\d{2})'),
            "wpr_pension":          _deduct(text, r'WPR Pension\s+£([\d,]+\.\d{2})'),
            "ni_employee":          _deduct(text, r'Employee NI\s+£([\d,]+\.\d{2})'),
            "paye_tax":             _deduct(text, r'PAYE Tax\s+£([\d,]+\.\d{2})'),
            "total_deductions":     -abs(_td) if _td is not None else None,
            "take_home_pay":        self._take_home_pay(text),
            "ni_employer":          self._ni_employer(text),
            "pension_employer":     None,  # Not present in Capium format
            "ytd_gross":            None,  # Excluded from Capium export (client request, March 2026)
            "ytd_taxable":          None,  # Excluded from Capium export (client request, March 2026)
            "ytd_tax_paid":         None,  # Excluded from Capium export (client request, March 2026)
            "ytd_ni_employee":      None,  # Excluded from Capium export (client request, March 2026)
            "ytd_pension_employee": None,  # Excluded from Capium export (client request, March 2026)
            "ytd_pension_employer": None,  # Excluded from Capium export (client request, March 2026)
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
        # Tax code sits immediately before "BACS". Four structural families:
        #
        #   Prefixed K-codes (e.g. "K296", "K18", "CK459", "SK296"):
        #            optional letter + K + digits, no trailing letter.
        #            Matched by:  [A-Z]?K\d{1,4}
        #
        #   D-codes (e.g. "D0", "D1", "SD0", "SD1"):
        #            optional letter + D + 1-2 digits, no trailing letter.
        #            Matched by:  [A-Z]?D\d{1,2}
        #
        #   Pure-letter codes (e.g. "BR", "NT", "SBR"):
        #            2-3 uppercase letters, no digits at all.
        #            Matched by:  [A-Z]{2,3}
        #
        #   Standard (e.g. "1257L", "0T", "45T", "S1257L", "793T"):
        #            optional 0-2 letter prefix + 1-4 digits + exactly 1 trailing letter.
        #            Matched by:  [A-Z]{0,2}\d{1,4}[A-Z]
        #
        # K and D alternatives come first so their leading letter is not consumed
        # by [A-Z]{0,2} and then fail for lack of a trailing letter.
        #
        # Basis indicator (M1/W1): non-cumulative payslips print the Month 1 / Week 1
        # basis indicator as a separate token between the tax code and BACS:
        #   "793T M1 BACS"  →  group(1)="793T"  group(2)="M1"
        # group(2) is a capturing group so we can append it without a space:
        #   "793T" + "M1" = "793TM1"
        # When no basis indicator is present group(2) is None and only group(1) is returned.
        m = re.search(r'\b([A-Z]?K\d{1,4}|[A-Z]?D\d{1,2}|[A-Z]{2,3}|[A-Z]{0,2}\d{1,4}[A-Z])\s+((?:M1|W1)\s+)?BACS', text)
        if not m:
            return None
        code = m.group(1)
        basis = m.group(2).strip() if m.group(2) else ''
        return code + basis

    def _ni_number(self, text: str) -> str | None:
        # Line 4: "JW648535D  1257L  BACS  M 10"
        # UK NI numbers are always exactly: 2 letters + 6 digits + 1 letter.
        # Word boundaries ensure we don't partially match adjacent text.
        return _find(text, r'\b([A-Z]{2}\d{6}[A-Z])\b')

    def _salary_maternity_adj(self, text: str) -> float | None:
        # In Capium's two-column layout, pdfplumber pairs a gross item (left column)
        # and a deduction item (right column) on the same visual line.  When
        # "Salary Maternity Adj" is a DEDUCTION it appears alone at the start of
        # its line — no earnings label precedes it on that row.  When it is an
        # EARNING it is followed by a deduction label on the same line.
        #
        # Detection: if the label starts a line (re.MULTILINE ^) → Deductions column
        # → return negative.  Otherwise → Gross Pay column → return positive.
        val = _money(text, r'(?i)Salary Maternity ADJ\s+£([\d,]+\.\d{2})')
        if val is None:
            return None
        if re.search(r'(?mi)^Salary Maternity ADJ\s', text):
            return -abs(val)
        return val

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

    def _ni_employer(self, text: str) -> float | None:
        # Mirror of _take_home_pay — captures the FIRST £ value on the two-value
        # line immediately above the "I £gross" row, where the second value is net pay.
        # 2025-26 format: "£1,499.32 £6,250.90\nI £11,222.33"
        #                   ↑ employer NI  ↑ net pay
        # Older format: "NET\nNATIONAL £89.74 £1,257.56\nPAY"
        #                               ↑ employer NI  ↑ net pay
        return (
            _money(text, r'£([\d,]+\.\d{2})\s+£[\d,]+\.\d{2}\nI\s+£')
            or _money(text, r'NET\nNATIONAL\s+£([\d,]+\.\d{2})\s+£[\d,]+\.\d{2}\nPAY')
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
        # Same pre-processing as extract().
        text = _decode_cid(text)
        text = text.replace('\xfa', '\xa3')
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
        # Second pass: accounting-negative (£168.60) values — brackets mean negative.
        for m in re.finditer(r"([A-Z][A-Za-z ./'\-]+?)\s+\(£([\d,]+\.\d{2})\)", text):
            label = m.group(1).strip()
            if label in _KNOWN_LABELS:
                continue
            value = -float(m.group(2).replace(',', ''))
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
