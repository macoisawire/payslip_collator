# Payslip Collator — TODO

---

## Pending stakeholder confirmation

The following fields were found in the Capium output but use abbreviations
that need confirming before they can be added to the canonical schema.

Please check with stakeholders and update this file with the answers,
then the fields can be added to config.py and capium.py.

### Fields to confirm

- [ ] **WPR Pension** — what does "WPR" stand for?
  - Proposed key: `wpr_pension`
  - Proposed display name: `WPR Pension` (or full name if known)
  - Appears as: deduction, alongside Employee NI / PAYE Tax

- [ ] **ERE Pension Pay** — what does "ERE" stand for?
  - Proposed key: `ere_pension_pay`
  - Proposed display name: `ERE Pension Pay` (or full name if known)
  - Appears as: pension-related figure

- [ ] **RAF Pay** — what does "RAF" stand for?
  - Proposed key: `raf_pay`
  - Proposed display name: `RAF Pay` (or full name if known)
  - Appears as: earnings component

### Once confirmed

For each field, add to:
1. `config.py` FIELDS list (in the appropriate earnings or deductions block)
2. `capium.py` `extract()` method using `_money(text, r'LABEL\s+£([\d,]+\.\d{2})')`
3. `capium.py` `_KNOWN_LABELS` set
4. `test_extraction.py` `EXPECTED_NONE["Capium"]` (these are optional fields)

---
