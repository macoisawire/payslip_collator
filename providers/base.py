# providers/base.py
# Abstract base class that all provider profiles must inherit from.
# Enforces a consistent interface so extractor.py can call any provider identically.

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    NAME = ""  # Human-readable name shown in the Streamlit provider selectbox

    @abstractmethod
    def extract(self, text: str) -> dict:
        """
        Accept raw text extracted by pdfplumber from a single payslip PDF.
        Return a dict whose keys match the field keys defined in config.FIELDS.
        Use None for any field that is not present or cannot be parsed.
        Never raise an exception — return None values for failed fields instead.
        """
        pass
