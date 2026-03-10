"""
spreadsheet.py
Builds a formatted Excel workbook from a list of extracted payslip dicts.

Responsibilities:
- Sheet name: "Payslips"
- Row 1: display names from config.FIELDS — bold, fill colour #D9E1F2
- Rows 2+: one row per payslip, sorted by period_date ascending
- All £ fields: number format £#,##0.00
- Auto-fit column widths
- Returns an openpyxl Workbook object — does NOT save to disk
"""
