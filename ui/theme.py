# ui/theme.py
import streamlit as st

def apply_theme():
    """Apply custom CSS theme for dark background and readable UI"""
    st.markdown("""
        <style>
        /* Main app background */
        .stApp {
            background-color: #000000; /* black background */
            color: #ffffff; /* default text white */
        }

        /* Tabs container */
        .css-1v3fvcr {
            background-color: #121212; /* dark gray tabs */
        }

        /* Selected tab */
        .css-1vq4p4l {
            background-color: #1f1f1f !important; /* darker selected tab */
            color: #ffffff !important; /* tab text white */
        }

        /* Input boxes */
        input, .stTextInput>div>input {
            background-color: #1f1f1f;
            color: #ffffff; /* input text white */
            border: 1px solid #333333;
        }

        /* Buttons */
        button, .stButton button {
            background-color: #007bff;
            color: #ffffff; /* button text white */
            border-radius: 5px;
        }

        button:hover, .stButton button:hover {
            background-color: #0056b3;
            color: #ffffff;
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff; /* headers white */
        }

        /* Textareas */
        textarea, .stTextArea>div>textarea {
            background-color: #1f1f1f;
            color: #ffffff;
            border: 1px solid #333333;
        }

        /* File uploader text */
        .css-1v0mbdj {
            color: #ffffff;
        }

        /* Checkbox label */
        .stCheckbox>label, .stCheckbox>div>label {
            color: #ffffff;
        }
    </style>
    """, unsafe_allow_html=True)
