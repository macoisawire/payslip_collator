"""
app.py
Streamlit entrypoint for the Payslip Collator.

UI flow:
1. Title and one-line description
2. Provider selectbox (populated from providers.PROVIDERS)
3. Multi-file PDF uploader
4. "Process" button
5. Progress bar + per-file result (tick or warning with reason)
6. st.dataframe preview of extracted data
7. st.download_button to download the Excel file
"""
