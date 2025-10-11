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



## ⚙️ Installation Guide

Clone the repository and navigate into the folder:
```bash
git clone https://github.com/your-username/expense-tracker.git
cd expense-tracker
Create a virtual environment:

bash
Copy code
python -m venv venv
Activate the virtual environment:

On Windows:

bash
Copy code
venv\Scripts\activate
On macOS/Linux:

bash
Copy code
source venv/bin/activate
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Set up MongoDB by creating a free cluster on MongoDB Atlas. Copy your connection string (URI) and update config/settings.py with:

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
Set up Gemini API (for AI Insights) by visiting Google AI Studio and generating your Gemini API Key. Launch the app, go to Settings → Gemini API Configuration, paste your key, and save.

Run the Streamlit app:

bash
Copy code
streamlit run app.py
Once the server starts, open your browser at http://localhost:8501.

Dependencies used (also in requirements.txt):

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
Optional: To enable sending daily email reports, turn on 2-Step Verification in Gmail, go to Google Account → Security → App Passwords, generate an app password, and use it as EMAIL_PASS in config/settings.py. You can now send reports via Settings → Send Daily Report.

Future enhancements planned: push notifications for budget overspending, integration with UPI/banking APIs for real-time transactions, mobile responsive layout, multi-language support, receipt AI auto-categorization, expense forecasting with LSTM models.

Contributors: Vedanth Reddy — Developer & Researcher. AI and Data modules powered by GPT.

pgsql
Copy code

This is **all in one continuous block**, no numbering, no splitting — ready to paste in your `README.md`.  

If you want, I can also make a **full README.md** including **project structure, features, screenshots, and license** in the same single-copy format. Do you want me to do that?






