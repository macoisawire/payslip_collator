"""
app.py
Streamlit entrypoint for the Payslip Collator.
Run with: streamlit run app.py
"""

import io

import pandas as pd
import streamlit as st

from config import FIELDS
from extractor import extract_payslip
from providers import PROVIDERS
from spreadsheet import build_workbook

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

st.title("Payslip Collator")
st.caption("Upload payslips, extract key fields, and download as a single Excel workbook.")

# ---------------------------------------------------------------------------
# Provider selection + file upload
# ---------------------------------------------------------------------------

provider_name = st.selectbox("Payroll provider", list(PROVIDERS.keys()))

uploaded_files = st.file_uploader(
    "Upload payslip PDFs",
    type="pdf",
    accept_multiple_files=True,
)

# ---------------------------------------------------------------------------
# Process button
# ---------------------------------------------------------------------------

if st.button("Process", disabled=not uploaded_files):
    records = []
    total = len(uploaded_files)
    progress = st.progress(0.0, text="Starting…")

    for i, file in enumerate(uploaded_files, start=1):
        progress.progress(i / total, text=f"Processing {file.name}…")

        result = extract_payslip(file, provider_name)

        if result is not None:
            st.success(f"✓  {file.name}")
            records.append(result)
        else:
            st.warning(f"⚠  {file.name} — could not extract fields. Check the provider selection and that the PDF is not password-protected.")

    progress.progress(1.0, text="Done.")
    st.session_state["records"] = records

    if not records:
        st.error("No payslips were successfully extracted.")

# ---------------------------------------------------------------------------
# Results: dataframe preview + download button
# ---------------------------------------------------------------------------

records = st.session_state.get("records")

if records:
    keys = [key for key, _ in FIELDS]
    display_names = [name for _, name in FIELDS]

    # reindex ensures column order matches config.FIELDS regardless of dict
    # key order, and fills any missing keys with NaN rather than raising
    df = pd.DataFrame(records).reindex(columns=keys)
    df.columns = display_names

    st.dataframe(df, use_container_width=True)

    # Build the workbook in memory — no temp files on disk
    buf = io.BytesIO()
    build_workbook(records).save(buf)
    buf.seek(0)

    n = len(records)
    st.download_button(
        label=f"Download Excel ({n} payslip{'s' if n != 1 else ''})",
        data=buf,
        file_name="payslips.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
