def safe_float(x: str):
    try:
        if x is None:
            return None
        s = str(x).strip().replace(",","")
        return float(s)
    except Exception:
        return None
