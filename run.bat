@echo off
cd /d "%~dp0"

echo ================================================
echo  Payslip Collator
echo ================================================
echo.
echo Checking dependencies...
pip install -r requirements.txt --quiet
echo.
echo Starting app — it will open in your browser automatically.
echo Keep this window open while using the app.
echo Close this window to stop the app.
echo.
streamlit run app.py
pause
