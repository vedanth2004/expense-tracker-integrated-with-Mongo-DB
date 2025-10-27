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

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: rgba(15, 23, 42, 0.95);
            border-right: 1px solid rgba(6, 182, 212, 0.2);
        }
        
        /* Sidebar header */
        [data-testid="stSidebar"] h2 {
            color: #06b6d4 !important;
            font-weight: 800 !important;
            text-align: center;
        }

        /* Sidebar radio buttons */
        [data-testid="stSidebar"] .stRadio > div > label {
            background-color: rgba(30, 41, 59, 0.8) !important;
            border: 2px solid rgba(100, 116, 139, 0.3) !important;
            color: #e2e8f0 !important;
            border-radius: 10px !important;
            padding: 0.75rem 1rem !important;
            margin: 0.25rem 0 !important;
            transition: all 0.3s ease !important;
        }
        
        [data-testid="stSidebar"] .stRadio > div > label:hover {
            background-color: rgba(6, 182, 212, 0.2) !important;
            border-color: rgba(6, 182, 212, 0.5) !important;
            transform: translateX(5px);
        }
        
        [data-testid="stSidebar"] .stRadio input[type="radio"]:checked + label {
            background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%) !important;
            border-color: transparent !important;
            color: white !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4) !important;
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
