from database import mongo_manager
import pandas as pd
import datetime
import calendar

class BudgetManager:
    def __init__(self, user_id: str, currency=None):
        self.user_id = user_id
        self.currency = currency

    def set_budget(self, category: str, monthly_limit: float):
        mongo_manager.set_budget(self.user_id, category, monthly_limit)

    def list_budgets_df(self) -> pd.DataFrame:
        rows = mongo_manager.list_budgets(self.user_id)
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        return df

    def budget_status_summary(self) -> str:
        today = datetime.date.today()
        start = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end = today.replace(day=last_day)
        # sum expenses between start and end
        expenses = mongo_manager.list_expenses(self.user_id, limit=1000)
        spent = {}
        for e in expenses:
            # e['date'] might be iso string
            d = e.get('date')
            try:
                ddate = datetime.datetime.fromisoformat(d) if isinstance(d, str) else d
            except Exception:
                ddate = None
            if ddate and start <= ddate.date() <= end:
                amt = float(e.get('amount', 0.0))
                spent[e.get('category', 'Other')] = spent.get(e.get('category', 'Other'), 0.0) + amt
        budgets = mongo_manager.list_budgets(self.user_id)
        lines = []
        for b in budgets:
            cat = b.get('category')
            limit = float(b.get('monthly_limit', 0.0))
            s = spent.get(cat, 0.0)
            pct = 0 if limit == 0 else (s / limit) * 100
            lines.append(f"{cat}: {s:.2f}/{limit:.2f} ({pct:.0f}%)")
        return "\n".join(lines) if lines else "No budgets set"
