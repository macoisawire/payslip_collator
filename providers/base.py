# providers/base.py
# Abstract base class that all provider profiles must inherit from.
# Enforces a consistent interface so extractor.py can call any provider identically.

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    NAME = ""  # Human-readable name shown in the Streamlit provider selectbox
    EXCLUDED_FIELDS: frozenset[str] = frozenset()  # Field keys omitted from this provider's export

    @abstractmethod
    def extract(self, text: str) -> dict:
        """
        Accept raw text extracted by pdfplumber from a single payslip PDF.
        Return a dict whose keys match the field keys defined in config.FIELDS.
        Use None for any field that is not present or cannot be parsed.
        Never raise an exception — return None values for failed fields instead.
        """
        pass

    def extra_fields(self, text: str) -> dict:
        """
        Scan for monetary fields not captured by extract().

        Returns an empty dict by default. Providers may override this to return
        any labelled £ values found in the PDF that fall outside the canonical
        schema. Keys returned here appear as bonus columns to the right of the
        standard columns in both the preview table and the Excel download,
        highlighted in amber for review.
        """
        return {}
