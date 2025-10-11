from database import mongo_manager
import pandas as pd

class IncomeManager:
    def __init__(self, user_id: str, currency=None):
        self.user_id = user_id
        self.currency = currency

    def add_income(self, amount: float, source: str, date, currency_code: str):
        mongo_manager.add_income(user_id=self.user_id, amount=amount, source=source, date=date, currency=currency_code)
        return True

    def list_income_df(self) -> pd.DataFrame:
        rows = mongo_manager.list_income(self.user_id)
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        if 'amount' in df.columns and self.currency:
            df['amount_in_base'] = df.apply(lambda r: self.currency.convert(r['amount'], r.get('currency', self.currency.base)), axis=1)
        return df
