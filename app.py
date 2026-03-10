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

pdf_password = st.text_input(
    "PDF password (if required)",
    placeholder="Leave blank for unprotected PDFs",
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

        results = extract_payslip(file, provider_name, password=pdf_password)

        if results:
            n = len(results)
            suffix = f" — {n} payslips" if n > 1 else ""
            st.success(f"✓  {file.name}{suffix}")
            records.extend(results)
        else:
            st.warning(f"⚠  {file.name} — could not extract fields. Check the provider is correct and, if the PDF is password-protected, that the password field is filled in.")

    progress.progress(1.0, text="Done.")
    st.session_state["records"] = records

    if not records:
        st.error("No payslips were successfully extracted.")

# ---------------------------------------------------------------------------
# Results: dataframe preview + download + clear
# ---------------------------------------------------------------------------

records = st.session_state.get("records")

if records:
    canonical_keys = [key for key, _ in FIELDS]
    canonical_names = [name for _, name in FIELDS]
    canonical_set = set(canonical_keys)

    # Collect extra (dynamic) keys in first-seen order across all records.
    seen_extra: set[str] = set()
    extra_keys: list[str] = []
    for record in records:
        for k in record:
            if k not in canonical_set and k not in seen_extra:
                extra_keys.append(k)
                seen_extra.add(k)

    extra_names = [k.replace('_', ' ').title() for k in extra_keys]
    all_keys = canonical_keys + extra_keys
    all_names = canonical_names + extra_names

    df = pd.DataFrame(records).reindex(columns=all_keys)
    df.columns = all_names

    if extra_keys:
        # Highlight every cell in extra columns amber so they stand out.
        def _highlight_extra(data: pd.DataFrame) -> pd.DataFrame:
            styles = pd.DataFrame('', index=data.index, columns=data.columns)
            for name in extra_names:
                if name in styles.columns:
                    styles[name] = 'background-color: #FFF3CD; color: #856404'
            return styles

        st.dataframe(
            df.style.apply(_highlight_extra, axis=None),
            use_container_width=True,
        )
        n_extra = len(extra_keys)
        st.caption(
            f"⚠ {n_extra} unrecognised field{'s' if n_extra != 1 else ''} detected "
            f"(highlighted) — review and add to the schema in the next iteration if needed."
        )
    else:
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
