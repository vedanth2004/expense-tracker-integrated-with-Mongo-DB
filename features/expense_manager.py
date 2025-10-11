from database import mongo_manager
import pandas as pd
from datetime import datetime, date as dt_date

class ExpenseManager:
    def __init__(self, user_id: str, currency=None):
        self.user_id = user_id
        self.currency = currency

    def add_expense(self, amount: float, category: str, note: str, date, currency_code: str, receipt_text: str | None = None):
        # Convert date to datetime.datetime
        if isinstance(date, dt_date) and not isinstance(date, datetime):
            date = datetime.combine(date, datetime.min.time())
        mongo_manager.add_expense(
            user_id=str(self.user_id),
            amount=amount,
            category=category,
            note=note,
            date=date,
            currency=currency_code,
            receipt_text=receipt_text or ""
        )
        return True

    def list_expenses_df(self) -> pd.DataFrame:
        rows = mongo_manager.list_expenses(self.user_id)
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        if 'amount' in df.columns and self.currency:
            df['amount_in_base'] = df.apply(lambda r: self.currency.convert(r['amount'], r.get('currency', self.currency.base)), axis=1)
        return df
    def delete_expense(self, expense_id: str) -> bool:
        """Delete an expense by ID"""
        from database import mongo_manager
        return mongo_manager.delete_expense(expense_id, self.user_id)