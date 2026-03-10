"""
extractor.py
Orchestrates the PDF -> dict pipeline for a single payslip file.

Responsibilities:
1. Open the PDF with pdfplumber
2. Extract and join text from all pages into a single string
3. Instantiate the correct provider class based on the user's selection
4. Call provider.extract(text) to get a field dict
5. Inject the 'provider' key into the returned dict
6. Return the dict, or None on failure (caller handles gracefully)
"""
