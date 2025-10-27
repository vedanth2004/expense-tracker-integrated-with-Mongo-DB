# components.py
import streamlit as st
import plotly.express as px
import pandas as pd
from streamlit_lottie import st_lottie
import requests

def load_lottie_url(url: str):
    """Fetch Lottie animation JSON from URL"""
    try:
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None

def nav_bar(items):
    """Sidebar navigation - returns selected item"""
    # Icon mapping for items
    icons = {
        "Dashboard": "📊",
        "Expenses": "💸",
        "Income": "💰",
        "Budgets": "📋",
        "Bills": "📅",
        "Split Bills": "👥",
        "Goals": "🎯",
        "Debts": "💳",
        "Reports": "📄",
        "AI Insights": "🤖",
        "Stock Trends": "📈",
        "Collaboration": "🤝",
        "Badges": "🏆",
        "Settings": "⚙️"
    }
    
    # Add icons to navigation items
    items_with_icons = [f"{icons.get(item, '📌')} {item}" for item in items]
    
    st.sidebar.markdown("## 💸 Expense Tracker")
    st.sidebar.divider()
    
    selected = st.sidebar.radio("Navigate", items_with_icons, index=0)
    
    st.sidebar.divider()
    
    
    # Remove icon from selected item to get clean name
    selected_clean = selected.split(" ", 1)[1] if " " in selected else selected
    
    return selected_clean

# -------------------- DASHBOARD METRICS --------------------
def render_metrics(income: float, expense: float, balance: float):
    """Display Total Income, Expense, and Balance in stylish glass cards"""
    col1, col2, col3 = st.columns(3, gap="medium")
    def glass_card_metric(title, amount, color="#06D6A0"):
        st.markdown(f"""
            <div style="
                background: rgba(255,255,255,0.85);
                backdrop-filter: blur(10px);
                border-radius: 14px;
                padding: 20px;
                text-align:center;
                box-shadow: 0 10px 30px rgba(2,6,23,0.06);
                font-family: 'Arial', sans-serif;
                margin-bottom: 12px;
            ">
                <div style="color:#666;font-weight:600">{title}</div>
                <div style="font-size:22px;font-weight:700;color:{color}">₹{amount:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)

    with col1:
        glass_card_metric("Total Income", income, color="#06D6A0")
    with col2:
        glass_card_metric("Total Expense", expense, color="#EF476F")
    with col3:
        balance_color = "#9B5DE5" if balance >= 0 else "#EF476F"  # Changed from yellow to purple
        glass_card_metric("Balance", balance, color=balance_color)


# -------------------- EXPENSE CHARTS --------------------
def render_expense_chart(expenses):
    st.markdown("### 📊 Expense Trend")
    if not expenses:
        st.info("No expenses to visualize yet.")
        return
    df = pd.DataFrame(expenses)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    fig = px.bar(df, x='date', y='amount', color='category',
                 title="Expenses Over Time",
                 hover_data=['note', 'currency'])
    fig.update_layout(
        height=450,
        margin=dict(t=50, l=10, r=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

# -------------------- GLASS CARD WRAPPER --------------------
def glass_card(html_content: str):
    """Wrap content inside a stylish glass card"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(180deg, rgba(255,255,255,0.85), rgba(245,245,255,0.72));
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(2,6,23,0.06);
        margin-bottom: 16px;
        font-family: 'Arial', sans-serif;
    ">
        {html_content}
    </div>
    """, unsafe_allow_html=True)

# -------------------- ANIMATED TABLE --------------------
def animated_table(df, height=300):
    st.markdown("""
    <style>
    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .fade-table { animation: fadeInUp 0.6s ease both; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="fade-table">', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, height=height)
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- ANIMATED HEADER --------------------
def animated_header(title="💸 Expense Tracker"):
    lottie = load_lottie_url("https://assets10.lottiefiles.com/packages/lf20_2glqweqs.json")
    if lottie:
        st_lottie(lottie, height=130)
        st.markdown(f"<h2 style='text-align:center;font-family:sans-serif;'>{title}</h2>", unsafe_allow_html=True)
    else:
        st.title(title)

# -------------------- BADGES UI --------------------
def render_badges(df_badges):
    st.markdown("### 🏆 Achievements & Badges")
    if df_badges.empty:
        st.info("No badges unlocked yet. Start logging your expenses!")
        return
    for _, row in df_badges.iterrows():
        glass_card(f"<b>{row['name']}</b><br><small>{row['detail']}</small>")

# -------------------- PIE CHART --------------------
def render_category_pie(expenses):
    st.markdown("### 📌 Expense by Category")
    if not expenses:
        st.info("No expenses to display.")
        return
    df = pd.DataFrame(expenses)
    by_cat = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    fig = px.pie(names=by_cat.index, values=by_cat.values, hole=0.4, title="Expense Distribution")
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400, margin=dict(t=40, l=10, r=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
