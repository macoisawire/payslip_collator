"""
test_extraction.py
End-to-end extraction test against real payslip PDFs.

Usage:
    python test_extraction.py
"""

from pathlib import Path
from extractor import extract_payslip
from config import FIELDS

# ---------------------------------------------------------------------------
# Sample PDF paths — can be a direct .pdf file or a folder (all PDFs tested).
# Passwords — leave as empty string "" if not required.
# ---------------------------------------------------------------------------

SAMPLES = {
    "Zelt":   r"C:\Users\The McDonnells\Downloads\zelt",
    "Capium": r"C:\Users\The McDonnells\Downloads\capium",
}

PASSWORDS = {
    "Zelt":   "",
    "Capium": "07111992",
}

# Fields that are legitimately None for each provider — not counted as failures.
EXPECTED_NONE = {
    "Zelt":   {"ytd_gross"},
    "Capium": {"ni_employer", "pension_employer", "ytd_taxable", "student_loan", "ytd_pension_employer"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_pdfs(path_str: str) -> list[Path]:
    """Return all PDFs at a path — accepts a single file or a folder."""
    p = Path(path_str)
    if p.is_file() and p.suffix.lower() == ".pdf":
        return [p]
    if p.is_dir():
        pdfs = sorted(p.glob("*.pdf"))
        if not pdfs:
            print(f"  No PDF files found in folder: {p}")
        return pdfs
    with_ext = p.with_suffix(".pdf")
    if with_ext.is_file():
        return [with_ext]
    print(f"  Could not find a PDF at: {p}")
    return []


def run_test(provider_name: str, pdf_path: Path, password: str = "") -> None:
    print()
    print("=" * 65)
    print(f"  {provider_name}  —  {pdf_path.name}")
    print("=" * 65)

    with open(pdf_path, "rb") as f:
        result = extract_payslip(f, provider_name, password=password)

    if result is None:
        print("  EXTRACTION FAILED — extract_payslip() returned None.")
        return

    expected_none = EXPECTED_NONE.get(provider_name, set())

    name_w  = max(len(display) for _, display in FIELDS) + 2
    val_w   = 32
    stat_w  = 16

    header = f"  {'Field':<{name_w}} {'Value':<{val_w}} Status"
    print(header)
    print("  " + "-" * (name_w + val_w + stat_w))

    failures = []

    for key, display_name in FIELDS:
        value = result.get(key)

        if value is None:
            if key in expected_none:
                status = "— expected None"
                val_str = ""
            else:
                status = "FAIL — None"
                val_str = ""
                failures.append(display_name)
        else:
            status = "OK"
            val_str = str(value)
            if len(val_str) > val_w - 2:
                val_str = val_str[: val_w - 5] + "..."

        print(f"  {display_name:<{name_w}} {val_str:<{val_w}} {status}")

    print()
    if failures:
        print(f"  *** {len(failures)} field(s) returned None unexpectedly: ***")
        for name in failures:
            print(f"      - {name}")
    else:
        print("  All expected fields extracted successfully.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not SAMPLES:
        print("No sample paths configured — edit SAMPLES at the top of this file.")

    for provider_name, raw_path in SAMPLES.items():
        password = PASSWORDS.get(provider_name, "")
        for pdf_path in resolve_pdfs(raw_path):
            run_test(provider_name, pdf_path, password=password)

    print()
