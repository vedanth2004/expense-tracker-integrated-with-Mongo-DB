# 💸 AI-Powered Expense Tracker

An advanced **personal finance web application** built with **Streamlit** that helps users track expenses, manage budgets, generate AI-driven financial insights, and even receive automated email reports — all in one interactive dashboard.

---

## 🚀 Features

### 🧾 Expense & Income Management
- Add, view, and delete your daily **expenses and income**.
- Upload receipts — **OCR automatically extracts text** from them.
- Multi-currency support with automatic **currency conversion**.

### 💰 Budget Planning
- Create and manage category-wise **monthly budgets**.
- Track **remaining balance**, **spent amount**, and receive alerts when limits are exceeded.

### 📊 Dashboard & Analytics
- Visualize income and expenses using dynamic charts.
- Generate **PDF/CSV financial reports** by custom date range.
- Access **AI-powered insights** using Gemini API (Google Generative AI).

### 📈 Stock Trends
- Get real-time stock market trends, analytics, and historical performance visualization.

### 🤖 AI Financial Insights
- Ask questions like “Where did I overspend last month?” or “How can I save more?”.
- Backed by **Gemini API** to provide intelligent insights from your personal financial data.

### 🧠 OCR Receipt Processing
- Upload receipt images, and the app automatically extracts and logs expense details.

### 🔐 Secure Authentication
- JWT token-based user authentication.
- Passwords stored securely in the database.

### 📬 Automated Email Reports
- Receive **daily, weekly, or custom reports** via email.
- Choose between **CSV or PDF** attachments.

### 👥 Collaboration
- Share financial data or budgets with friends, family, or colleagues.

### 🏆 Gamification
- Earn badges and achievements for reaching milestones like “Saved ₹10,000” or “30 Days of Budget Tracking”.

### 💬 Floating AI Chatbot
- Embedded **AI Chatbot** for finance-related Q&A and quick help.

---
## 🗂️ Project Structure

expense_tracker/
│
├── app.py # Main Streamlit application (entry point)
│
├── config/
│ └── settings.py # Configuration (MongoDB URI, API Keys, Secrets)
│
├── auth/
│ └── authenticator.py # User authentication and JWT management
│
├── database/
│ ├── mongo_manager.py # MongoDB connection and queries
│ └── init.py
│
├── features/
│ ├── expense_manager.py # Expense CRUD operations
│ ├── income_manager.py # Income CRUD operations
│ ├── budget_manager.py # Budget tracking logic
│ ├── ocr_processor.py # OCR text extraction from receipts
│ ├── currency_converter.py # Currency exchange conversion
│ ├── chatbot.py # Floating financial assistant chatbot
│ └── init.py
│
├── analytics/
│ ├── dashboard.py # Visualization dashboard
│ ├── reports.py # PDF/CSV report generation
│ ├── stock_trends.py # Stock trend visualization
│ ├── ai_insights.py # Gemini AI financial insights
│ └── init.py
│
├── collaboration/
│ └── shared_accounts.py # Multi-user collaboration feature
│
├── gamification/
│ └── achievements.py # Achievement and reward system
│
├── notifications/
│ ├── email_handler.py # Email service for sending reports
│ └── init.py
│
├── ui/
│ ├── theme.py # App theme and styles
│ ├── components.py # Navigation bar and animations
│ └── init.py
│
└── requirements.txt # Python dependencies

yaml
Copy code

---

## ⚙️ Installation Guide

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/expense-tracker.git
cd expense-tracker
2️⃣ Create a Virtual Environment
bash
Copy code
python -m venv venv
# Activate it:
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
3️⃣ Install Dependencies
bash
Copy code
pip install -r requirements.txt
🛢️ 4️⃣ MongoDB Setup
Go to MongoDB Atlas.

Create a free cluster.

Copy your connection string (URI).

Update your config/settings.py file with:

python
Copy code
MONGO_URI = "mongodb+srv://<username>:<password>@cluster.mongodb.net/expense_db"
SECRET_KEY = "your-secret-key"
CURRENCY_BASE = "INR"

# Email credentials
EMAIL_USER = "your_email@gmail.com"
EMAIL_PASS = "your_app_password"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
🧠 5️⃣ Gemini API Setup (AI Insights)
Visit Google AI Studio.

Generate your Gemini API key.

Launch the app, go to:

pgsql
Copy code
⚙️ Settings → 🔑 Gemini API Configuration
Paste your API key and click Save.

▶️ 6️⃣ Run the App
bash
Copy code
streamlit run app.py
Once the server starts, open the app in your browser:

arduino
Copy code
http://localhost:8501
🧩 Dependencies
These are the key libraries used (in requirements.txt):

nginx
Copy code
streamlit
pymongo
pandas
numpy
opencv-python
Pillow
requests
python-dotenv
reportlab
google-generativeai
email-validator
matplotlib
plotly
📧 Email Report Setup (Optional)
To enable email delivery of daily reports:

Turn on 2-Step Verification in your Gmail account.

Go to:

nginx
Copy code
Google Account → Security → App Passwords
Generate a new app password.

Use this password in your config/settings.py:

python
Copy code
EMAIL_PASS = "your_generated_app_password"
Now you can send reports via email directly from:

rust
Copy code
⚙️ Settings → 📧 Send Daily Report
🏅 Future Enhancements
✅ Push notifications for budget overspending
✅ Integration with UPI or banking APIs for real-time transactions
✅ Mobile responsive layout
✅ Multi-language support
✅ Receipt AI auto-categorization
✅ Expense forecasting with LSTM model

👨‍💻 Contributors
Your Name — Developer & Researcher
AI and Data Modules — Gemini & OpenAI Integrations

🛡️ License
This project is licensed under the MIT License — you are free to use and modify it with credit.

📸 Screenshots (Optional)
Add the following screenshots for documentation:

📊 Dashboard Overview

💡 AI Financial Insights

🧾 OCR Receipt Upload

📈 Stock Trends Visualization

🎯 Gamification & Achievements


