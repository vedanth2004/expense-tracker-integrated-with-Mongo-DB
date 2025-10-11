# gamifications.py
from database import mongo_manager
import pandas as pd
import datetime

class Achievements:
    def _evaluate(self, user_id: str):
        badges = []

        exps = mongo_manager.list_expenses(user_id, limit=1000)
        if exps and len(exps) >= 1:
            badges.append(("First Expense", "Logged the first expense"))

        # --- Expense Streaks ---
        dates = sorted({e.get('date')[:10] for e in exps if e.get('date')})
        streak = 1
        best_streak = 1
        parsed_dates = [datetime.date.fromisoformat(d) for d in dates if d]
        for i in range(1, len(parsed_dates)):
            if (parsed_dates[i] - parsed_dates[i-1]).days == 1:
                streak += 1
                best_streak = max(best_streak, streak)
            else:
                streak = 1
        if best_streak >= 3:
            badges.append(("3-Day Streak", "Logged expenses 3 days in a row"))
        if best_streak >= 7:
            badges.append(("7-Day Streak", "Logged expenses 7 consecutive days"))

        # --- High Spender Badge ---
        total_exp = sum(e.get("amount", 0) for e in exps)
        if total_exp >= 10000:
            badges.append(("High Spender", f"Spent over ₹10,000"))

        # --- Big Single Expense ---
        max_exp = max((e.get("amount", 0) for e in exps), default=0)
        if max_exp >= 2000:
            badges.append(("Big Spender", f"Single expense over ₹2,000"))

        # --- Weekly Consistency ---
        weeks = set(e.get("date")[:7] for e in exps if e.get("date"))
        if len(weeks) >= 4:
            badges.append(("Consistent Week", "Logged expenses in 4 different weeks"))

        # --- Other fun badges (can expand later) ---
        if len(exps) >= 50:
            badges.append(("Expense Enthusiast", "Logged 50+ expenses"))

        return badges

    def summary(self, db, user_id: str) -> str:
        b = self._evaluate(user_id)
        return f"Unlocked {len(b)} badges"

    def list_badges(self, db, user_id: str):
        data = [{"name": n, "detail": d} for n, d in self._evaluate(user_id)]
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
