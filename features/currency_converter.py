import time
import requests

class CurrencyConverter:
    def __init__(self, base: str = "USD"):
        self.base = base.upper()
        self._rates = {self.base: 1.0}
        self._last_fetch = 0

    def _fetch_rates(self):
        try:
            resp = requests.get(f"https://api.exchangerate.host/latest?base={self.base}", timeout=8)
            if resp.ok:
                data = resp.json()
                self._rates = data.get("rates", {})
                self._rates[self.base] = 1.0
                self._last_fetch = time.time()
        except Exception:
            pass

    def convert(self, amount: float, from_code: str):
        now = time.time()
        if now - self._last_fetch > 6 * 3600:
            self._fetch_rates()
        from_code = from_code.upper()
        if from_code == self.base:
            return float(amount)
        rate = self._rates.get(from_code)
        if rate:
            return float(amount) / float(rate)
        return float(amount)
