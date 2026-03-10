# config.py
# Single source of truth for field keys and display names.
# Column order in the Excel output is determined by the order of this list.
# To add a new field: add it here first, then implement in all relevant providers.

FIELDS = [
    ("provider",              "Provider"),
    ("employee_name",         "Employee Name"),
    ("employer_name",         "Employer"),
    ("period_label",          "Period"),
    ("period_date",           "Pay Date"),
    ("tax_code",              "Tax Code"),
    ("ni_number",             "NI Number"),
    ("basic_pay",             "Basic / Monthly Pay"),
    ("pension_employee",      "Employee Pension Contribution"),
    ("student_loan",          "Student Loan Deduction"),
    ("ni_employee",           "Employee NI"),
    ("paye_tax",              "PAYE Tax"),
    ("total_deductions",      "Total Deductions"),
    ("take_home_pay",         "Take Home / Net Pay"),
    ("ni_employer",           "Employer NI"),
    ("pension_employer",      "Employer Pension"),
    ("ytd_gross",             "YTD Gross Pay"),
    ("ytd_taxable",           "YTD Taxable Pay"),
    ("ytd_tax_paid",          "YTD Tax Paid"),
    ("ytd_ni_employee",       "YTD Employee NI"),
    ("ytd_pension_employee",  "YTD Employee Pension"),
    ("ytd_pension_employer",  "YTD Employer Pension"),
]
