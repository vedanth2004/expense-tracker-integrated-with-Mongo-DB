# analytics/ai_insights.py
import json
import streamlit as st
from database import mongo_manager

try:
    import google.generativeai as genai
except ImportError:
    genai = None
    st.warning("Google GenAI SDK not installed. AI Insights will not work.")

class AIInsights:
    def __init__(self):
        self.finance_model = "gemini-2.5-flash"
        self.general_model = "gemini-2.5-flash"

    def set_api_key(self, user_id: str, api_key: str):
        """Store API key in DB and session"""
        if genai:
            # Store in DB
            mongo_manager.set_gemini_api_key(user_id, api_key)
            # Store in session
            st.session_state["gemini_api_key"] = api_key
            return True
        return False

    def _get_api_key(self, user_id: str):
        # Check session first
        api_key = st.session_state.get("gemini_api_key")
        if api_key:
            return api_key
        # Fallback to DB
        return mongo_manager.get_gemini_api_key(user_id)

    def analyze_finance(self, user_id: str, prompt: str):
        """Analyze user finances using Gemini"""
        if genai is None:
            return None, "GenAI SDK not installed."

        api_key = self._get_api_key(user_id)
        if not api_key:
            return None, "⚠️ No Gemini API key found. Please add it in Settings."

        # Configure Gemini
        try:
            genai.configure(api_key=api_key)
        except Exception as e:
            return None, f"Error configuring Gemini API: {e}"

        # Gather user financial data
        expenses = mongo_manager.list_expenses(user_id)
        income = mongo_manager.list_income(user_id)
        budgets = mongo_manager.list_budgets(user_id)

        # Build structured user data
        user_data = {
            "expenses": expenses,
            "income": income,
            "budgets": budgets
        }

        # Finance-specific prompt
        full_prompt = f"""
You are a financial assistant. Analyze the user's financial data and provide concise,
friendly, actionable insights. Highlight categories over budget and suggest actions.

User data:
{json.dumps(user_data, default=str)}

User question/prompt: {prompt}

Return your answer in clear bullet points or numbered list.
"""

        try:
            model = genai.GenerativeModel(self.finance_model)
            response = model.generate_content(full_prompt)
            return response.text, None
        except Exception as e:
            return None, f"Error generating insights: {e}"

    def analyze_general(self, user_id: str, question: str):
        """Answer any general question using Gemini"""
        if genai is None:
            return None, "GenAI SDK not installed."

        api_key = self._get_api_key(user_id)
        if not api_key:
            return None, "⚠️ No Gemini API key found. Please add it in Settings."

        # Configure Gemini
        try:
            genai.configure(api_key=api_key)
        except Exception as e:
            return None, f"Error configuring Gemini API: {e}"

        full_prompt = f"""
Answer the following question clearly and concisely. Provide useful information in readable text.

Question: {question}
"""

        try:
            model = genai.GenerativeModel(self.general_model)
            response = model.generate_content(full_prompt)
            return response.text, None
        except Exception as e:
            return None, f"Error generating response: {e}"

    # --- ADDED FOR BACKWARD COMPATIBILITY ---
    def analyze(self, user_id: str, prompt: str):
        """
        Wrapper method to keep old code working.
        Defaults to finance analysis.
        """
        return self.analyze_finance(user_id, prompt)
