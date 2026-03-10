"""
app.py
Streamlit entrypoint for the Payslip Collator.
Run with: streamlit run app.py
"""

import io
from datetime import datetime

import pandas as pd
import streamlit as st

from config import FIELDS
from extractor import extract_payslip
from providers import PROVIDERS
from spreadsheet import build_workbook


def _clear_results():
    """Callback — wipes extracted records from session state."""
    st.session_state.pop("records", None)


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

st.title("Payslip Collator")
st.caption("Upload payslips, extract key fields, and download as a single Excel workbook.")

# ---------------------------------------------------------------------------
# Provider selection + file upload
# ---------------------------------------------------------------------------

# on_change fires before the rest of the script re-runs, so the results
# section below will already see an empty session when the provider changes.
provider_name = st.selectbox(
    "Payroll provider",
    list(PROVIDERS.keys()),
    on_change=_clear_results,
)

uploaded_files = st.file_uploader(
    "Upload payslip PDFs",
    type="pdf",
    accept_multiple_files=True,
)

if uploaded_files:
    n = len(uploaded_files)
    st.caption(f"{n} file{'s' if n != 1 else ''} selected")

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
# Results: dataframe preview + download + clear
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

    # Download and Clear sit side by side below the grid
    col_dl, col_clear = st.columns([3, 1])

    with col_dl:
        buf = io.BytesIO()
        build_workbook(records).save(buf)
        buf.seek(0)

        n = len(records)
        timestamp = datetime.now().strftime("%d_%m_%Y_%H_%M")
        file_name = f"{provider_name}_Payslips_{timestamp}.xlsx"

        st.download_button(
            label=f"Download Excel ({n} payslip{'s' if n != 1 else ''})",
            data=buf,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_clear:
        if st.button("Clear results", use_container_width=True):
            _clear_results()
            st.rerun()
