# gamifications.py
from database import mongo_manager
import pandas as pd
import datetime

class Achievements:
    def _evaluate(self, user_id: str):
        badges = []
        
        # Get expenses and income
        exps = mongo_manager.list_expenses(user_id, limit=1000)
        incs = mongo_manager.list_income(user_id, limit=1000)
        buds = mongo_manager.list_budgets(user_id)

        # --- Milestone Badges ---
        if exps and len(exps) >= 1:
            badges.append(("🎯 First Step", "Logged your first expense", "💼"))
        if exps and len(exps) >= 5:
            badges.append(("🌱 Getting Started", "Logged 5 expenses", "📝"))
        if exps and len(exps) >= 10:
            badges.append(("⭐ Active Tracker", "Logged 10 expenses", "📊"))
        if exps and len(exps) >= 25:
            badges.append(("🎖️ Dedicated User", "Logged 25 expenses", "📈"))
        if exps and len(exps) >= 50:
            badges.append(("🏆 Expense Master", "Logged 50+ expenses", "💯"))
        if exps and len(exps) >= 100:
            badges.append(("👑 Legendary Tracker", "Logged 100+ expenses", "🌟"))

        # --- Streak Badges ---
        if exps:
            dates = sorted({e.get('date')[:10] for e in exps if e.get('date')})
            if dates:
                streak = 1
                best_streak = 1
                parsed_dates = [datetime.date.fromisoformat(d) for d in dates if d]
                for i in range(1, len(parsed_dates)):
                    if (parsed_dates[i] - parsed_dates[i-1]).days == 1:
                        streak += 1
                        best_streak = max(best_streak, streak)
                    else:
                        streak = 1
                
                if best_streak >= 2:
                    badges.append(("🔥 Hot Start", "2-day expense streak", "💪"))
                if best_streak >= 3:
                    badges.append(("🔥🔥 On Fire", "3-day expense streak", "🔥"))
                if best_streak >= 7:
                    badges.append(("🔥🔥🔥 Streak King", "7-day expense streak", "⚡"))
                if best_streak >= 14:
                    badges.append(("🔥🔥🔥🔥 Unstoppable", "14-day expense streak", "💥"))
                if best_streak >= 30:
                    badges.append(("🔥🔥🔥🔥🔥 Perfectionist", "30-day expense streak", "✨"))

        # --- Spending Badges ---
        if exps:
            total_exp = sum(e.get("amount", 0) for e in exps)
            
            if total_exp >= 1000:
                badges.append(("💰 Thousand Club", f"Spent ₹{total_exp:,.0f}+", "💵"))
            if total_exp >= 5000:
                badges.append(("💸 Big Spender", f"Spent ₹{total_exp:,.0f}+", "💶"))
            if total_exp >= 10000:
                badges.append(("💎 High Roller", f"Spent ₹{total_exp:,.0f}+", "💷"))
            if total_exp >= 50000:
                badges.append(("👑 Premium Member", f"Spent ₹{total_exp:,.0f}+", "💴"))
            
            # Single big expense
            max_exp = max((e.get("amount", 0) for e in exps), default=0)
            if max_exp >= 1000:
                badges.append(("💳 Large Purchase", f"Single expense ₹{max_exp:,.0f}+", "💸"))
            if max_exp >= 5000:
                badges.append(("🎁 Splurge Time", f"Single expense ₹{max_exp:,.0f}+", "💎"))

        # --- Budget Badges ---
        if buds:
            total_budgets = len(buds)
            if total_budgets >= 1:
                badges.append(("📋 Budget Planner", f"Set {total_budgets} budget(s)", "📌"))
            if total_budgets >= 3:
                badges.append(("🎯 Goal Setter", f"Managing {total_budgets} categories", "🎯"))
            if total_budgets >= 5:
                badges.append(("🎨 Comprehensive Planner", f"Managing {total_budgets} categories", "📊"))
            
            # Check budget adherence
            under_budget_count = 0
            for budget in buds:
                spent = budget.get("spent", 0)
                limit = budget.get("monthly_limit", 0)
                if limit > 0 and spent < limit:
                    under_budget_count += 1
            
            if under_budget_count >= total_budgets and total_budgets >= 1:
                badges.append(("✅ Budget Hero", "All budgets under control", "🎯"))

        # --- Income Badges ---
        if incs:
            total_inc = sum(i.get("amount", 0) for i in incs)
            income_count = len(incs)
            
            if income_count >= 1:
                badges.append(("💵 Income Tracker", f"Logged {income_count} income(s)", "💰"))
            if total_inc >= 10000:
                badges.append(("📈 Earned Well", f"Total income ₹{total_inc:,.0f}+", "💵"))
            if total_inc >= 50000:
                badges.append(("🏅 Wealth Builder", f"Total income ₹{total_inc:,.0f}+", "💸"))
            
            max_inc = max((i.get("amount", 0) for i in incs), default=0)
            if max_inc >= 10000:
                badges.append(("🎯 Big Income", f"Single income ₹{max_inc:,.0f}+", "💰"))

        # --- Multi-Currency Badge ---
        currencies = set(e.get("currency", "") for e in exps if e.get("currency"))
        if len(currencies) > 1:
            badges.append(("🌍 World Traveler", f"Used {len(currencies)} currencies", "✈️"))

        # --- Category Diversity ---
        if exps:
            categories = set(e.get("category", "") for e in exps if e.get("category"))
            if len(categories) >= 3:
                badges.append(("🎪 Diversified Spender", f"{len(categories)} categories", "🎨"))
            if len(categories) >= 6:
                badges.append(("🌈 Complete Coverage", f"{len(categories)} categories", "🎯"))

        # --- Weekly Consistency ---
        if exps:
            weeks = set(e.get("date")[:7] for e in exps if e.get("date"))
            if len(weeks) >= 2:
                badges.append(("📅 Consistent Logger", f"{len(weeks)} weeks active", "📝"))
            if len(weeks) >= 4:
                badges.append(("📆 Regular Tracker", f"{len(weeks)} weeks active", "📊"))
            if len(weeks) >= 8:
                badges.append(("📅💯 Long-term User", f"{len(weeks)} weeks active", "🌟"))

        # --- Receipt Master (OCR feature) ---
        receipt_count = sum(1 for e in exps if e.get("receipt_text"))
        if receipt_count >= 1:
            badges.append(("📷 Photo Finish", f"{receipt_count} receipt(s) scanned", "📸"))
        if receipt_count >= 5:
            badges.append(("📷📷 Receipt Collector", f"{receipt_count} receipt(s) scanned", "📷"))
        if receipt_count >= 10:
            badges.append(("📷📷📷 Receipt Master", f"{receipt_count} receipt(s) scanned", "📷"))

        return badges

    def summary(self, db, user_id: str) -> str:
        b = self._evaluate(user_id)
        return f"Unlocked {len(b)} badges 🏆"

    def list_badges(self, db, user_id: str):
        badges_list = self._evaluate(user_id)
        data = []
        for item in badges_list:
            if len(item) == 3:  # Has emoji
                name, detail, emoji = item
                data.append({"badge": f"{emoji} {name}", "description": detail})
            else:  # Fallback for old format
                name, detail = item
                data.append({"badge": f"🏆 {name}", "description": detail})
        return pd.DataFrame(data)


# --------------------------
# OPTIONAL: Interactive UI (Streamlit)
# --------------------------
def render_badges_ui(user_id: str):
    """
    Interactive badges UI using Streamlit
    Run: `streamlit run gamifications.py`
    """
    import streamlit as st

    ach = Achievements()
    df = ach.list_badges(None, user_id)

    st.title("🏆 Achievements & Badges")
    st.write(f"You have unlocked **{len(df)} badges**!")

    for _, row in df.iterrows():
        st.markdown(f"**{row['name']}** 🎖️")
        st.write(row['detail'])
        st.markdown("---")
