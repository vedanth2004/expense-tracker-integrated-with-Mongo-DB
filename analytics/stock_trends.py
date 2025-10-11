# analytics/stock_trends.py
import streamlit as st
import pandas as pd
from datetime import datetime
from database import mongo_manager

try:
    import google.generativeai as genai
except Exception:
    genai = None

# List of top NSE tickers to analyze
INDIAN_STOCKS = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","HINDUNILVR.NS",
    "KOTAKBANK.NS","SBIN.NS","BAJFINANCE.NS","ITC.NS","BHARTIARTL.NS","LT.NS",
    "ASIANPAINT.NS","AXISBANK.NS","HCLTECH.NS","MARUTI.NS","SUNPHARMA.NS","TITAN.NS",
    "ULTRACEMCO.NS","TECHM.NS"
]

def build_stock_prompt(tickers):
    prompt_lines = [
        "You are an experienced equity research analyst focused on Indian NSE stocks.",
        "Provide a concise, actionable report including:",
        "1) Top gainers and losers with approximate % change,",
        "2) Short explanation of drivers or patterns to watch,",
        "3) Short-term trade ideas (buy/watch/sell) with risk notes,",
        "4) 3 specific stock tickers to add to a watchlist and why.",
        "",
        "Focus only on the following tickers:",
        ", ".join(tickers),
        "",
        "Be concise. Use bullet points or numbered items. Include short risk warnings."
    ]
    return "\n".join(prompt_lines)

def render_stock_trends_page(user_id: str):
    st.header("📈 Indian Stock Trends & AI Suggestions")
    st.write("Get top trending NSE stocks and AI-powered suggestions (using Gemini).")

    # Fetch Gemini API key: first check session_state, then database
    api_key = st.session_state.get("gemini_api_key") or mongo_manager.get_gemini_api_key(user_id)

    if not api_key:
        st.info("No Gemini API key detected. Add it in Settings → Gemini API Configuration to enable AI analysis.")

    if st.button("Generate AI Stock Trends"):
        if genai and api_key:
            with st.spinner("Generating AI suggestions via Gemini..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    prompt = build_stock_prompt(INDIAN_STOCKS)
                    response = model.generate_content(prompt)
                    ai_text = getattr(response, "text", None) or str(response)

                    st.subheader("💡 AI Investment Suggestions (Gemini)")
                    st.write(ai_text)
                except Exception as e:
                    st.error(f"AI generation failed: {e}")
        else:
            st.warning("Gemini SDK or API key not available. Please add your key to run AI analysis.")
