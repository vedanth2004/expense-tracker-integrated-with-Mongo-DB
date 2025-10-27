import streamlit as st
from analytics.ai_insights import AIInsights

class ChatBot:
    def __init__(self, user_id):
        self.user_id = user_id
        self.chat_history_key = f"chat_history_{user_id}"
        self.chat_open_key = f"chat_open_{user_id}"
        self.input_key = f"chat_input_{user_id}"
        self.clear_input_key = f"clear_input_{user_id}"
        self.ai = AIInsights()

        if self.chat_history_key not in st.session_state:
            st.session_state[self.chat_history_key] = []
        if self.chat_open_key not in st.session_state:
            st.session_state[self.chat_open_key] = False
        if self.input_key not in st.session_state:
            st.session_state[self.input_key] = ""
        if self.clear_input_key not in st.session_state:
            st.session_state[self.clear_input_key] = False

    def toggle_chat(self):
        st.session_state[self.chat_open_key] = not st.session_state[self.chat_open_key]
        st.rerun()

    def render(self):
        # CSS for wide blue floating button, centered, large text
        st.markdown(
            """
            <style>
            div[data-testid="stButton"][key="float_chat_btn"] > button {
                font-size: 22px !important;
                font-weight: 600 !important;
                min-width: 150px !important;
                height: 54px !important;
                background-color: #1976d2 !important;
                color: #fff !important;
                border-radius: 14px !important;
                border: none !important;
                margin-bottom: 12px !important;
                box-shadow: 0 2px 10px #0001;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Floating chat icon to open
        chat_col = st.columns([10, 1])[1]
        with chat_col:
            if not st.session_state[self.chat_open_key]:
                if st.button("💬 Ask bot", help="Open Chat", key="float_chat_btn"):
                    self.toggle_chat()
        if not st.session_state[self.chat_open_key]:
            return

        st.subheader("💬 Chat with Finance Bot")
        if st.button("❌ Close Chat"):
            self.toggle_chat()
            return

        input_value = st.session_state.get(self.input_key, "")
        if st.session_state[self.clear_input_key]:
            input_value = ""
            st.session_state[self.input_key] = ""
            st.session_state[self.clear_input_key] = False

        user_input = st.text_input("Type your question here:", key=self.input_key, value=input_value)

        if st.button("Ask", key="ask_btn"):
            question = st.session_state[self.input_key].strip()
            if not question:
                st.warning("Please ask a question.")
            else:
                history = st.session_state[self.chat_history_key]
                last_user_msg = next((msg for msg in history if msg[0] == "User"), None)
                if last_user_msg is None or last_user_msg[1] != question:
                    with st.spinner("Thinking..."):
                        answer, error = self.ai.analyze(self.user_id, question)
                        if error:
                            answer = f"Error: {error}"
                    # Insert at beginning for latest at top
                    history.insert(0, ("Bot", answer))
                    history.insert(0, ("User", question))
                    st.session_state[self.clear_input_key] = True
                    st.rerun()

        st.divider()

        # Render chat: user row, bot row, separator, newest at top
        history = st.session_state[self.chat_history_key]

        if not history:
            st.info("No conversation yet. Ask something!")
            return

        for i in range(0, len(history) - 1, 2):
            if history[i][0] == "User" and history[i + 1][0] == "Bot":
                user_text = history[i][1].replace('\n', '  \n')
                bot_text = history[i + 1][1].replace('\n', '  \n')
                st.markdown(f"**User:**  \n{user_text}")
                st.markdown(f"**Bot:**  \n{bot_text}")
                st.markdown("---")  # separator
