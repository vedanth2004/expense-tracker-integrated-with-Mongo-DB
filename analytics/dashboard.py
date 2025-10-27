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
    
    # --- COMPREHENSIVE OVERVIEW METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    
    # Fetch bills
    all_bills = mongo_manager.list_bill_reminders(user_id)
    due_bills = [b for b in all_bills if not b.get("is_paid", False)]
    total_due = sum(b.get("amount", 0) for b in due_bills)
    
    # Fetch debts
    debts = mongo_manager.list_debts(user_id)
    total_debt = sum(d.get("remaining_amount", 0) for d in debts)
    
    # Fetch goals
    goals = mongo_manager.list_financial_goals(user_id)
    total_goal_progress = sum(g.get("current_amount", 0) for g in goals)
    total_goal_target = sum(g.get("target_amount", 0) for g in goals)
    
    with col1:
        st.metric("💰 Bills Due", f"₹{total_due:,.2f}", f"{len(due_bills)} bills")
    with col2:
        st.metric("💳 Total Debt", f"₹{total_debt:,.2f}", f"{len(debts)} debts")
    with col3:
        goal_progress = (total_goal_progress / total_goal_target * 100) if total_goal_target > 0 else 0
        st.metric("🎯 Goals Progress", f"{goal_progress:.1f}%", f"₹{total_goal_progress:,.2f} saved")
    with col4:
        # Get this month's data
        expenses = mongo_manager.list_expenses(user_id, limit=1000)
        incs = mongo_manager.list_income(user_id, limit=1000)
        
        exp_df = pd.DataFrame(expenses) if expenses else pd.DataFrame()
        inc_df = pd.DataFrame(incs) if incs else pd.DataFrame()
        
        if not exp_df.empty and not inc_df.empty:
            exp_df["date"] = pd.to_datetime(exp_df["date"], errors="coerce")
            inc_df["date"] = pd.to_datetime(inc_df["date"], errors="coerce")
            month_start = datetime.today().replace(day=1)
            month_exp = exp_df[exp_df["date"] >= month_start]["amount"].sum()
            month_inc = inc_df[inc_df["date"] >= month_start]["amount"].sum()
            savings = month_inc - month_exp
            st.metric("📊 This Month", f"₹{savings:,.2f}", f"Balance")
        else:
            st.metric("📊 This Month", f"₹0.00", "No data yet")
    
    st.divider()
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
        render_section(month_exp, month_inc, "Month", user_id)

    elif selected_dashboard == "Today Dashboard":
        today = datetime.today().date()
        today_exp = exp_df[exp_df["date"].dt.date == today] if not exp_df.empty else pd.DataFrame()
        today_inc = inc_df[inc_df["date"].dt.date == today] if not inc_df.empty else pd.DataFrame()
        render_section(today_exp, today_inc, "Today", user_id)

    elif selected_dashboard == "Year Dashboard":
        year_start = datetime.today().replace(month=1, day=1)
        year_exp = exp_df[exp_df["date"] >= year_start] if not exp_df.empty else pd.DataFrame()
        year_inc = inc_df[inc_df["date"] >= year_start] if not inc_df.empty else pd.DataFrame()
        render_section(year_exp, year_inc, "Year", user_id)

    elif selected_dashboard == "Life Dashboard (All-time)":
        render_section(exp_df, inc_df, "Life", user_id)


def render_section(exp_df: pd.DataFrame, inc_df: pd.DataFrame, label: str, user_id: str = None):
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
    
    # --- FINANCIAL HEALTH OVERVIEW (Show on Monthly Dashboard only) ---
    if label == "Month" and user_id:
        st.divider()
        st.markdown("### 🏥 Financial Health Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Bills Status
            all_bills = mongo_manager.list_bill_reminders(user_id)
            due_bills_count = len([b for b in all_bills if not b.get("is_paid", False)])
            paid_bills_count = len([b for b in all_bills if b.get("is_paid", False)])
            
            if due_bills_count > 0:
                st.warning(f"⚠️ {due_bills_count} bills pending payment")
            if paid_bills_count > 0:
                st.success(f"✅ {paid_bills_count} bills paid this month")
            if len(all_bills) == 0:
                st.info("📅 No bill reminders set")
        
        with col2:
            # Goals Progress
            goals = mongo_manager.list_financial_goals(user_id)
            if goals:
                active_goals = len([g for g in goals if not g.get("is_achieved", False)])
                achieved_goals = len([g for g in goals if g.get("is_achieved", False)])
                
                if active_goals > 0:
                    st.info(f"🎯 {active_goals} active financial goals")
                if achieved_goals > 0:
                    st.success(f"🎉 {achieved_goals} goals achieved!")
            else:
                st.info("🎯 No financial goals set yet")
        
        # Quick Action Cards
        col3, col4, col5 = st.columns(3)
        
        with col3:
            if due_bills_count > 0:
                st.markdown("### 📋 Action Needed")
                st.markdown(f"**Pay {due_bills_count} bills**")
                st.markdown("[➡️ Go to Bills page](?page=Bills)")
        
        with col4:
            debts = mongo_manager.list_debts(user_id)
            total_debt = sum(d.get("remaining_amount", 0) for d in debts)
            if total_debt > 0:
                st.markdown("### 💳 Debt Status")
                debt_progress = 100 - ((sum(d.get("remaining_amount", 0) for d in debts) / 
                                       sum(d.get("total_amount", 0) for d in debts)) * 100) if debts else 0
                st.progress(debt_progress / 100)
                st.write(f"{debt_progress:.1f}% paid off")
        
        with col5:
            # Check upcoming due dates
            if all_bills:
                upcoming_bills = [b for b in all_bills if not b.get("is_paid", False)]
                if upcoming_bills:
                    closest = min(upcoming_bills, key=lambda x: x.get("due_date", ""))
                    st.markdown("### ⏰ Next Payment")
                    st.write(f"**{closest.get('title')}**")
                    st.write(f"₹{closest.get('amount', 0):,.2f}")
    
    # --- UPCOMING FINANCIAL SUMMARY (All-time Dashboard) ---
    if label == "Life" and user_id:
        st.divider()
        st.markdown("### 📊 Overall Financial Summary")
        
        summary_col1, summary_col2 = st.columns(2)
        
        with summary_col1:
            # Net Worth Calculation
            all_incomes = mongo_manager.list_income(user_id, limit=10000)
            all_expenses = mongo_manager.list_expenses(user_id, limit=10000)
            total_income_all = sum(i.get("amount", 0) for i in all_incomes)
            total_expenses_all = sum(e.get("amount", 0) for e in all_expenses)
            
            # Assets (income - expenses)
            assets = total_income_all - total_expenses_all
            
            # Liabilities (debts)
            all_debts = mongo_manager.list_debts(user_id)
            liabilities = sum(d.get("remaining_amount", 0) for d in all_debts)
            
            net_worth = assets - liabilities
            
            st.markdown("#### 💰 Net Worth Analysis")
            st.metric("Total Assets", f"₹{assets:,.2f}")
            st.metric("Total Liabilities", f"₹{liabilities:,.2f}")
            st.metric("**Net Worth**", f"₹{net_worth:,.2f}", 
                     delta=f"{((assets-liabilities)/assets*100):.1f}%" if assets > 0 else "0%")
        
        with summary_col2:
            # Financial Goals Overview
            goals_list = mongo_manager.list_financial_goals(user_id)
            if goals_list:
                st.markdown("#### 🎯 Your Financial Goals")
                for goal in goals_list[:3]:  # Show top 3
                    current = goal.get("current_amount", 0)
                    target = goal.get("target_amount", 1)
                    progress = min(current / target * 100, 100)
                    
                    st.write(f"**{goal.get('title')}**")
                    st.progress(progress / 100)
                    st.caption(f"₹{current:,.2f} / ₹{target:,.2f} ({progress:.1f}%)")
                    st.write("---")
            else:
                st.info("Set your first financial goal to start tracking savings!")
