"""
extractor.py
Orchestrates the PDF -> list[dict] pipeline for a payslip file.

Each page is treated as an independent payslip, so a multi-page PDF
produces one dict per page rather than one combined dict.
"""

import pdfplumber
from providers import PROVIDERS


def extract_payslip(file_obj, provider_name: str, password: str = "") -> list[dict]:
    """
    Extract fields from a payslip PDF, one record per page.

    Args:
        file_obj:      File-like object from Streamlit uploader (BytesIO-compatible).
                       pdfplumber accepts these directly — no temp file needed.
        provider_name: Key from providers.PROVIDERS, e.g. "Zelt" or "Capium".
        password:      Optional PDF password. Only passed to pdfplumber when
                       non-empty so unprotected files are unaffected.

    Returns:
        List of dicts (one per payslip page), each with keys matching config.FIELDS
        and 'provider' injected. Returns an empty list on total failure or if no
        pages matched — caller is responsible for surfacing the error.
    """
    try:
        provider_class = PROVIDERS.get(provider_name)
        if provider_class is None:
            print(f"Warning: unknown provider '{provider_name}' — skipping file.")
            return []

        open_kwargs = {"password": password} if password else {}
        provider = provider_class()
        results = []

        with pdfplumber.open(file_obj, **open_kwargs) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if not text.strip():
                    continue  # skip blank / cover pages

                result = provider.extract(text)
                if result is None:
                    continue  # page didn't match this provider's layout

                result["provider"] = provider_name
                result.update(provider.extra_fields(text))
                results.append(result)

        if not results:
            print(f"Warning: provider '{provider_name}' matched no pages — skipping file.")

        return results

    except Exception as e:
        print(f"Warning: failed to extract payslip — {e}")
        return []
