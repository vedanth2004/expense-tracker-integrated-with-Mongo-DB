from pydantic_settings import BaseSettings
from typing import Optional
import streamlit as st

class Settings(BaseSettings):
    SECRET_KEY: str = st.secrets.get("SECRET_KEY", "dev_secret_key")
    MONGO_URI: str = st.secrets.get("MONGO_URI", "mongodb+srv://shapuramvedanthreddy_db_user:kyNIkrEaOzK5Ovuc@cluster0.7e1g9hm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    SMTP_HOST: str = st.secrets.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = st.secrets.get("SMTP_PORT", 587)
    SMTP_USER: str = st.secrets.get("SMTP_USER", "")
    SMTP_PASS: str = st.secrets.get("SMTP_PASS", "")
    CURRENCY_BASE: str = st.secrets.get("CURRENCY_BASE", "USD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
