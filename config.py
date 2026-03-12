# config.py
# Single source of truth for field keys and display names.
# Column order in the Excel output is determined by the order of this list.
# To add a new field: add it here first, then implement in all relevant providers.

FIELDS = [
    # Identity / header
    ("provider",              "Provider"),
    ("employee_name",         "Employee Name"),
    ("employer_name",         "Employer"),
    ("period_label",          "Period"),
    ("period_date",           "Pay Date"),
    ("tax_code",              "Tax Code"),
    ("ni_number",             "NI Number"),

    # Earnings / gross pay
    ("basic_pay",             "Basic / Monthly Pay"),
    ("smp",                   "SMP"),
    ("car_allowance",         "Car Allowance"),
    ("on_call",               "On Call"),
    ("kit_pay",               "Kit Pay"),
    ("holiday_exchange",      "Holiday Exchange"),
    ("salary_adj",            "Salary Adjustment"),
    ("salary_maternity_adj",  "Salary Maternity Adjustment"),
    ("smp_top_up",            "SMP Top Up"),

    # Deductions
    ("pension_employee",      "Employee Pension Contribution"),
    ("student_loan",          "Student Loan Deduction"),
    ("healthcare",            "Healthcare"),
    ("child_healthcare",      "Child Healthcare"),
    ("postgraduate_loan",     "Postgraduate Loan"),
    ("car_salary_sacrifice",  "Car Salary Sacrifice"),
    ("pension_payment",       "Pension Payment"),
    ("wpr_pension",           "WPR Pension"),
    ("ni_employee",           "Employee NI"),
    ("paye_tax",              "PAYE Tax"),
    ("total_deductions",      "Total Deductions"),
    ("take_home_pay",         "Take Home / Net Pay"),

    # Employer costs
    ("ni_employer",           "Employer NI"),
    ("pension_employer",      "Employer Pension"),

    # Year to date
    ("ytd_gross",             "YTD Gross Pay"),
    ("ytd_taxable",           "YTD Taxable Pay"),
    ("ytd_tax_paid",          "YTD Tax Paid"),
    ("ytd_ni_employee",       "YTD Employee NI"),
    ("ytd_pension_employee",  "YTD Employee Pension"),
    ("ytd_pension_employer",  "YTD Employer Pension"),
]
