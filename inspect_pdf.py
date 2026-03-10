"""
inspect_pdf.py
Diagnostic tool — inspect raw pdfplumber text before writing any regex.
Usage: python inspect_pdf.py path/to/payslip.pdf
"""

import sys
import pdfplumber


def inspect(path: str) -> None:
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            print(f"\n{'=' * 60}")
            print(f"PAGE {i} — READABLE")
            print('=' * 60)
            print(text)
            print(f"\n{'=' * 60}")
            print(f"PAGE {i} — REPR (shows exact whitespace/newlines)")
            print('=' * 60)
            print(repr(text))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python inspect_pdf.py path/to/payslip.pdf")
        sys.exit(1)
    inspect(sys.argv[1])
