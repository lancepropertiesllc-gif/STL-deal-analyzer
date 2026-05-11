import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="St. Louis Multifamily Deal Analyzer", layout="wide")

st.title("🏙️ St. Louis Multifamily Deal Analyzer")
st.markdown("**2026 Edition** — Realistic Deal Analysis")

st.info("**All-In Cost = Purchase Price + Rehab Cost**")

# ===================== INPUTS =====================
st.sidebar.header("Deal Basics")

purchase_price = st.sidebar.number_input("Purchase Price ($)", value=350_000, step=10_000)
arv = st.sidebar.number_input("After Repair Value (ARV) ($)", value=475_000, step=10_000)
units = st.sidebar.number_input("Number of Units", value=12, min_value=4)
avg_rent = st.sidebar.number_input("Avg Monthly Rent per Unit ($)", value=1_250, step=25)

analysis_mode = st.sidebar.radio("Analysis Mode", ["Hold (Rental)", "Flip"])

rehab_cost = st.sidebar.number_input("Total Rehab Budget ($)", value=40_000, step=5_000)

vacancy_rate = st.sidebar.slider("Vacancy Rate (%)", 0, 20, 7) / 100
annual_expenses = st.sidebar.number_input("Annual Operating Expenses ($)", value=48_000, step=2_000)  # More realistic default
property_tax_rate = st.sidebar.slider("Annual Property Tax Rate (%)", 1.0, 3.5, 2.1) / 100

loan_to_value = st.sidebar.slider("Loan-to-Value (%)", 60, 85, 75)
interest_rate = st.sidebar.slider("Interest Rate (%)", 4.0, 9.0, 6.8) / 100
loan_term = st.sidebar.slider("Loan Term (years)", 15, 30, 25)

if analysis_mode == "Hold (Rental)":
    rent_growth = st.sidebar.slider("Annual Rent Growth (%)", 1, 8, 4) / 100
    expense_growth = st.sidebar.slider("Annual Expense Growth (%)", 1, 6, 3) / 100

# ===================== CALCULATIONS =====================
total_all_in_cost = purchase_price + rehab_cost
loan_amount = purchase_price * (loan_to_value / 100)
down_payment = purchase_price - loan_amount

annual_gross_rent = avg_rent * 12 * units
vacancy_loss = annual_gross_rent * vacancy_rate
effective_gross_income = annual_gross_rent - vacancy_loss

noi = effective_gross_income - annual_expenses - (purchase_price * property_tax_rate)

cap_rate = (noi / purchase_price) * 100 if purchase_price > 0 else 0

# Debt Service
monthly_rate = interest_rate / 12
num_payments = loan_term * 12
if monthly_rate > 0:
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
else:
    monthly_payment = loan_amount / num_payments
annual_debt_service = monthly_payment * 12

cash_flow = noi - annual_debt_service
cash_on_cash = (cash_flow / down_payment) * 100 if down_payment > 0 else 0

total_equity_upside = (arv - loan_amount) - down_payment - rehab_cost

# ===================== DISPLAY =====================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Going-in Cap Rate", f"{cap_rate:.2f}%")
col2.metric("Cash-on-Cash Return", f"{cash_on_cash:.1f}%")
col3.metric("**Total All-In Cost**", f"${total_all_in_cost:,.0f}")
col4.metric("All-In vs ARV Spread", f"${total_equity_upside:,.0f}")

if total_equity_upside < 0:
    st.error("⚠️ NEGATIVE EQUITY WARNING: Total All-In Cost is higher than ARV. This is likely a bad deal.")

if analysis_mode == "Hold (Rental)":
    st.subheader("5-Year Hold Projection")
    # Projection code (same as before)
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

else:
    st.subheader("Flip Analysis")
    est_holding_cost = annual_debt_service * 0.5
    flip_profit = arv - total_all_in_cost - est_holding_cost
    st.metric("Estimated Flip Profit (before selling costs)", f"${flip_profit:,.0f}")

st.caption("Portfolio Tool by Tyler — Real Estate Ops & AI Consultant")