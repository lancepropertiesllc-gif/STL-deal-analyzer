import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="St. Louis Multifamily Deal Analyzer", layout="wide")

st.title("🏙️ St. Louis Multifamily Deal Analyzer")
st.markdown("**2026 Edition** — Purchase vs ARV + Hold vs Flip Analysis")

st.info("""
**How to use:** Adjust the inputs on the left. The tool now properly accounts for **Total All-In Cost** (Purchase + Rehab).
""")

# ===================== INPUTS =====================
st.sidebar.header("Deal Basics")

purchase_price = st.sidebar.number_input("Purchase Price ($)", value=1_250_000, step=25_000)
arv = st.sidebar.number_input("After Repair Value (ARV) ($)", value=1_650_000, step=25_000)
units = st.sidebar.number_input("Number of Units", value=24, min_value=4)
avg_rent = st.sidebar.number_input("Avg Monthly Rent per Unit ($)", value=1_375, step=25)

analysis_mode = st.sidebar.radio("Analysis Mode", ["Hold (Rental)", "Flip"])

rehab_cost = st.sidebar.number_input("Total Rehab Budget ($)", value=150_000, step=10_000)

vacancy_rate = st.sidebar.slider("Vacancy Rate (%)", 0, 20, 6) / 100
annual_expenses = st.sidebar.number_input("Annual Operating Expenses ($)", value=92_000, step=5_000)
property_tax_rate = st.sidebar.slider("Annual Property Tax Rate (%)", 1.0, 3.5, 2.1) / 100

loan_to_value = st.sidebar.slider("Loan-to-Value (%)", 60, 85, 75)
interest_rate = st.sidebar.slider("Interest Rate (%)", 4.0, 9.0, 6.5) / 100
loan_term = st.sidebar.slider("Loan Term (years)", 15, 30, 25)

if analysis_mode == "Hold (Rental)":
    rent_growth = st.sidebar.slider("Annual Rent Growth (%)", 1, 8, 4) / 100
    expense_growth = st.sidebar.slider("Annual Expense Growth (%)", 1, 6, 3) / 100

# ===================== CALCULATIONS =====================
total_all_in_cost = purchase_price + rehab_cost
loan_amount = purchase_price * (loan_to_value / 100)
down_payment = purchase_price - loan_amount

annual_gross_rent = avg_rent * 12 * units
effective_gross_income = annual_gross_rent * (1 - vacancy_rate)
noi = effective_gross_income - annual_expenses - (purchase_price * property_tax_rate)
cap_rate = (noi / purchase_price) * 100

# Debt Service
monthly_rate = interest_rate / 12
num_payments = loan_term * 12
monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
annual_debt_service = monthly_payment * 12

cash_flow = noi - annual_debt_service
cash_on_cash = (cash_flow / down_payment) * 100 if down_payment > 0 else 0

# Equity & Spread (now uses All-In Cost)
equity_at_arv = arv - loan_amount
total_equity_upside = equity_at_arv - down_payment - rehab_cost   # True economic upside

# ===================== DISPLAY =====================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Going-in Cap Rate", f"{cap_rate:.2f}%")
col2.metric("Cash-on-Cash Return", f"{cash_on_cash:.1f}%")
col3.metric("Total All-In Cost", f"${total_all_in_cost:,.0f}")
col4.metric("All-In vs ARV Spread", f"${total_equity_upside:,.0f}")

if total_equity_upside < 0:
    st.error("⚠️ **WARNING: Negative Equity Position** — You are all-in for more than the ARV. This is a high-risk or bad deal regardless of cash flow.")

if analysis_mode == "Hold (Rental)":
    st.subheader("5-Year Hold Projection")
    years = list(range(1, 6))
    projections = []
    current_rent = avg_rent
    current_exp = annual_expenses

    for year in years:
        gross = current_rent * 12 * units
        egi = gross * (1 - vacancy_rate)
        noi_y = egi - current_exp - (purchase_price * property_tax_rate)
        cf_y = noi_y - annual_debt_service
        projections.append({'Year': year, 'Avg Rent': round(current_rent, 2), 'NOI': round(noi_y, 0), 'Cash Flow': round(cf_y, 0)})
        current_rent *= (1 + rent_growth)
        current_exp *= (1 + expense_growth)

    proj_df = pd.DataFrame(projections)
    st.dataframe(proj_df, use_container_width=True, hide_index=True)
    st.metric("Total 5-Year Cash Flow", f"${proj_df['Cash Flow'].sum():,.0f}")

else:  # Flip Mode
    st.subheader("Flip Analysis")
    est_holding_cost = annual_debt_service * 0.5
    flip_profit = arv - total_all_in_cost - est_holding_cost
    st.metric("Estimated Flip Profit (before selling costs)", f"${flip_profit:,.0f}")

st.subheader("Key Insights")
st.info(f"""
**Deal Summary:**
- Total All-In Cost (Purchase + Rehab): **${total_all_in_cost:,.0f}**
- Equity Position after Rehab (at ARV): **${total_equity_upside:,.0f}**
- {'This deal has negative equity and is likely a bad buy.' if total_equity_upside < 0 else 'This deal has positive equity upside.'}
""")

st.caption("Portfolio Tool by Tyler — Real Estate Ops & AI Consultant")