from pydantic_settings import BaseSettings
import os
import streamlit as st

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", None) or st.secrets.get("SECRET_KEY", "dev_secret_key")
    MONGO_URI: str = os.getenv("MONGO_URI", None) or st.secrets.get("MONGO_URI", None)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER", None) or st.secrets.get("SMTP_USER", "")
    SMTP_PASS: str = os.getenv("SMTP_PASS", None) or st.secrets.get("SMTP_PASS", "")
    CURRENCY_BASE: str = os.getenv("CURRENCY_BASE", None) or st.secrets.get("CURRENCY_BASE", "USD")

settings = Settings()
