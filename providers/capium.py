# providers/capium.py
# Provider profile for Capium payslips.
# Extraction logic to be implemented once raw pdfplumber output has been inspected.
# WARNING: Capium's visual PDF layout does NOT match pdfplumber's text extraction order.
# Always inspect raw output with the debug command in CLAUDE.md before writing regex.

from .base import BaseProvider


class CapiumProvider(BaseProvider):
    NAME = "Capium"

    def extract(self, text: str) -> dict:
        """
        Extract fields from a Capium payslip.
        Not yet implemented — returns all fields as None.
        """
        raise NotImplementedError("CapiumProvider.extract() is not yet implemented.")
