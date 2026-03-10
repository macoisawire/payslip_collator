# providers/zelt.py
# Provider profile for Zelt (Syrenis) payslips.
# Extraction logic to be implemented once raw pdfplumber output has been inspected.

from .base import BaseProvider


class ZeltProvider(BaseProvider):
    NAME = "Zelt"

    def extract(self, text: str) -> dict:
        """
        Extract fields from a Zelt payslip.
        Not yet implemented — returns all fields as None.
        """
        raise NotImplementedError("ZeltProvider.extract() is not yet implemented.")
