# Payslip Collator

An internal tool for processing payslips in bulk. Upload multiple PDF payslips, extract key fields automatically, and download everything as a single formatted Excel workbook for analysis.

Runs entirely on your local machine — no internet connection required, no data leaves your computer.

---

## What it does

- Accepts multiple payslip PDFs at once
- Extracts fields including pay, deductions, NI, pension, and year-to-date figures
- Collates everything into one Excel file with consistent column headers
- Supports **Capium** and **Zelt** payslip formats

---

## Requirements

- **Python 3.10 or later** — download from [python.org](https://www.python.org/downloads/)
  - During installation, tick **"Add Python to PATH"** — this is required

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
2. Click **Browse files** and select one or more payslip PDFs
3. Click **Process**
4. Review the preview table — any files that failed to extract will show a warning
5. Click **Download Excel** to save the collated workbook

The downloaded file is named `Provider_Payslips_DD_MM_YYYY_HH_MM.xlsx`.

---

## Supported providers

| Provider | Format |
|----------|--------|
| Capium   | Standard Capium PDF payslip |
| Zelt     | Zelt / Syrenis PDF payslip  |

---

## Troubleshooting

**"streamlit is not recognised"** — Python was not added to PATH during installation. Reinstall Python and tick "Add Python to PATH".

**A file shows a warning and is skipped** — check that the correct provider is selected for those PDFs. Each batch must use a single provider.

**Fields show blank in the output** — the PDF may be a scanned image rather than a text-based PDF. This tool requires text-based PDFs downloaded directly from your payroll portal.
