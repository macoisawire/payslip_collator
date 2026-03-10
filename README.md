# Payslip Collator

An internal tool for processing payslips in bulk. Upload multiple PDF payslips, extract key fields automatically, and download everything as a single formatted Excel workbook for analysis.

Runs entirely on your local machine — no internet connection required, no data leaves your computer.

---

## What it does

- Accepts multiple payslip PDFs at once
- Extracts fields including pay, deductions, NI, pension, and year-to-date figures
- Collates everything into one Excel file with consistent column headers
- Supports **Capium** and **Zelt** payslip formats
- Handles password-protected PDFs

---

## Requirements

- **Python 3.10 or later** — download from [python.org](https://www.python.org/downloads/)
  - During installation, tick **"Add Python to PATH"**

---

## Installation

1. Download or clone this repository to your computer
2. That's it — the first time you run the app it will install everything else automatically

---

## Running the app

Double-click **`run.bat`** in the folder.

- Dependencies install automatically on first run (takes about 30 seconds)
- The app opens in your default browser
- Keep the black command window open while using the app — closing it stops the app

---

## Creating a desktop shortcut

So you can launch the app without navigating to the folder each time:

1. Right-click `run.bat`
2. Select **Send to → Desktop (create shortcut)**
3. The shortcut on your desktop will open the app directly

---

## How to use

1. Select your **payroll provider** (Capium or Zelt) from the dropdown
2. If your PDFs are password-protected, enter the password in the **PDF password** field
3. Click **Browse files** and select one or more payslip PDFs
4. Click **Process**
5. Review the preview table — any files that failed to extract will show a warning
6. Click **Download Excel** to save the collated workbook
7. Use **Clear results** to reset and start a new batch

The downloaded file is named `Provider_Payslips_DD_MM_YYYY_HH_MM.xlsx`.

---

## Supported providers

| Provider | Format | Password format |
|----------|--------|-----------------|
| Capium   | Standard Capium PDF payslip | Date of birth — `DDMMYYYY` e.g. `07111992` |
| Zelt     | Zelt / Syrenis PDF payslip  | None required |

---

## Troubleshooting

**"streamlit is not recognised"** — Python itself is not on PATH. Reinstall Python from [python.org](https://www.python.org/downloads/) and tick **"Add Python to PATH"** on the first installer screen.

**A file shows a warning and is skipped** — check that the correct provider is selected. If the PDF is password-protected, make sure the password field is filled in before clicking Process.

**Fields show blank in the output** — the PDF is likely a scanned image rather than a text-based PDF. This tool requires text-based PDFs downloaded directly from your payroll portal. PDFs that have been printed to PDF will not work.

**Wrong values extracted** — ensure you are using the original PDF downloaded from the payroll portal, not a copy that has been printed, re-saved, or modified.
