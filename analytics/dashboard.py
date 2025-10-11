import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database import mongo_manager
from ui.components import render_metrics
from features.currency_converter import CurrencyConverter


def render_dashboard(db, user_id: str, currency: CurrencyConverter, user_name: str = None):
    # --- USER DETAILS ---
    user = mongo_manager.get_user(user_id)
    user_name = user_name or (user.get("name") if user else "User")

    st.header(f"📊 Welcome, {user_name}!")
    st.markdown("#### Select the dashboard view 👇")

    # --- FETCH DATA ---
    expenses = mongo_manager.list_expenses(user_id, limit=1000)
    incomes = mongo_manager.list_income(user_id, limit=1000)

    if not expenses and not incomes:
        st.info("No data found yet. Add some income and expenses to get started!")
        return

    # --- Convert to DataFrames ---
    exp_df = pd.DataFrame(expenses) if expenses else pd.DataFrame(columns=["category", "amount", "date"])
    inc_df = pd.DataFrame(incomes) if incomes else pd.DataFrame(columns=["source", "amount", "date"])

    if not exp_df.empty:
        exp_df["amount"] = exp_df["amount"].astype(float)
        exp_df["date"] = pd.to_datetime(exp_df["date"], errors="coerce")
    if not inc_df.empty:
        inc_df["amount"] = inc_df["amount"].astype(float)
        inc_df["date"] = pd.to_datetime(inc_df["date"], errors="coerce")

    # --- DASHBOARD SELECTION ---
    dashboard_options = ["Monthly Dashboard", "Today Dashboard", "Year Dashboard", "Life Dashboard (All-time)"]
    selected_dashboard = st.selectbox("Choose Dashboard", dashboard_options, index=0)  # Monthly as default

    if selected_dashboard == "Monthly Dashboard":
        month_start = datetime.today().replace(day=1)
        month_exp = exp_df[exp_df["date"] >= month_start] if not exp_df.empty else pd.DataFrame()
        month_inc = inc_df[inc_df["date"] >= month_start] if not inc_df.empty else pd.DataFrame()
        render_section(month_exp, month_inc, "Month")

    elif selected_dashboard == "Today Dashboard":
        today = datetime.today().date()
        today_exp = exp_df[exp_df["date"].dt.date == today] if not exp_df.empty else pd.DataFrame()
        today_inc = inc_df[inc_df["date"].dt.date == today] if not inc_df.empty else pd.DataFrame()
        render_section(today_exp, today_inc, "Today")

    elif selected_dashboard == "Year Dashboard":
        year_start = datetime.today().replace(month=1, day=1)
        year_exp = exp_df[exp_df["date"] >= year_start] if not exp_df.empty else pd.DataFrame()
        year_inc = inc_df[inc_df["date"] >= year_start] if not inc_df.empty else pd.DataFrame()
        render_section(year_exp, year_inc, "Year")

    elif selected_dashboard == "Life Dashboard (All-time)":
        render_section(exp_df, inc_df, "Life")


def render_section(exp_df: pd.DataFrame, inc_df: pd.DataFrame, label: str):
    total_exp = exp_df["amount"].sum() if not exp_df.empty else 0.0
    total_inc = inc_df["amount"].sum() if not inc_df.empty else 0.0
    balance = total_inc - total_exp

    st.subheader(f"🌟 {label} Summary")
    render_metrics(total_inc, total_exp, balance)

    # Expense by Category
    if not exp_df.empty:
        st.markdown(f"### 🍕 {label} Expense Distribution by Category")
        cat_chart = px.pie(
            exp_df,
            names="category",
            values="amount",
            title=f"{label} Spending Breakdown by Category",
            color_discrete_sequence=px.colors.sequential.RdPu
        )
        st.plotly_chart(cat_chart, use_container_width=True)
    else:
        st.write(f"No {label.lower()} expenses to show.")

    # Trend chart (Monthly/Yearly for Life/Month/Year, skip for Today)
    if not exp_df.empty and label != "Today":
        st.markdown(f"### 📈 {label} Expense Trend")
        period = "M" if label in ["Month"] else "Y"
        trend = exp_df.groupby(exp_df["date"].dt.to_period(period))["amount"].sum().reset_index()
        trend["date"] = trend["date"].astype(str)
        line_chart = px.line(
            trend,
            x="date",
            y="amount",
            title=f"{label} Expense Trend",
            markers=True,
            line_shape="spline"
        )
        st.plotly_chart(line_chart, use_container_width=True)

    # Income vs Expense
    st.markdown(f"### 💰 {label} Income vs Expenses")
    combined_data = pd.DataFrame({
        "Category": [f"{label} Income", f"{label} Expenses"],
        "Amount": [total_inc, total_exp]
    })
    bar_chart = px.bar(
        combined_data,
        x="Category",
        y="Amount",
        color="Category",
        text="Amount",
        color_discrete_sequence=["#00cc96", "#EF553B"]
    )
    bar_chart.update_traces(texttemplate="₹%{text:.2s}", textposition="outside")
    st.plotly_chart(bar_chart, use_container_width=True)

    # Savings Rate
    if total_inc > 0:
        savings_rate = (balance / total_inc) * 100
        st.metric(f"💸 {label} Savings Rate", f"{savings_rate:.2f}%")
        if savings_rate < 20:
            st.warning(f"{label} savings rate is below 20%. Consider reducing expenses.")
        else:
            st.success(f"Great! {label} savings rate is healthy. 👍")
