"""
inspect_pdf.py
Diagnostic tool — inspect raw pdfplumber text before writing any regex.
Usage:
    python inspect_pdf.py path/to/payslip.pdf
    python inspect_pdf.py path/to/payslip.pdf --password DDMMYYYY
"""

import sys
import pdfplumber


def inspect(path: str, password: str = "") -> None:
    open_kwargs = {"password": password} if password else {}
    with pdfplumber.open(path, **open_kwargs) as pdf:
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
    if len(sys.argv) < 2:
        print("Usage: python inspect_pdf.py path/to/payslip.pdf [--password DDMMYYYY]")
        sys.exit(1)

    path = sys.argv[1]
    password = ""
    if "--password" in sys.argv:
        idx = sys.argv.index("--password")
        if idx + 1 < len(sys.argv):
            password = sys.argv[idx + 1]

    inspect(path, password=password)
