"""
extractor.py
Orchestrates the PDF -> dict pipeline for a single payslip file.
"""

import pdfplumber
from providers import PROVIDERS


def extract_payslip(file_obj, provider_name: str, password: str = "") -> dict | None:
    """
    Extract fields from a single payslip PDF.

    Args:
        file_obj:      File-like object from Streamlit uploader (BytesIO-compatible).
                       pdfplumber accepts these directly — no temp file needed.
        provider_name: Key from providers.PROVIDERS, e.g. "Zelt" or "Capium".
        password:      Optional PDF password. Only passed to pdfplumber when
                       non-empty so unprotected files are unaffected.

    Returns:
        Dict with keys matching config.FIELDS, with 'provider' injected.
        Returns None on any failure — caller is responsible for surfacing the error.
    """
    try:
        provider_class = PROVIDERS.get(provider_name)
        if provider_class is None:
            print(f"Warning: unknown provider '{provider_name}' — skipping file.")
            return None

        open_kwargs = {"password": password} if password else {}
        with pdfplumber.open(file_obj, **open_kwargs) as pdf:
            # Join all pages with a newline so multi-page payslips form one
            # continuous string. Provider regex can still anchor on \n boundaries.
            pages_text = [page.extract_text() or "" for page in pdf.pages]
            text = "\n".join(pages_text)

        provider = provider_class()
        result = provider.extract(text)

        if result is None:
            print(f"Warning: provider '{provider_name}' returned None — skipping file.")
            return None

        # Inject provider name here so individual providers don't need to set it
        result["provider"] = provider_name

        # Merge any bonus fields found by the provider's generic scanner.
        # These appear as extra columns to the right of the canonical schema.
        result.update(provider.extra_fields(text))
        return result

    except Exception as e:
        print(f"Warning: failed to extract payslip — {e}")
        return None
