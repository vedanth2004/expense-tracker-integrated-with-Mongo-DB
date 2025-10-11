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

## ⚙️ Installation Guide

### Clone the Repository
- Clone the repository and navigate into the folder:
```bash
git clone https://github.com/your-username/expense-tracker.git
cd expense-tracker
````

### Create a Virtual Environment

* Create a virtual environment:

```bash
python -m venv venv
```

* Activate the virtual environment:

On Windows:

```bash
venv\Scripts\activate
```

On macOS/Linux:

```bash
source venv/bin/activate
```

### Install Dependencies

* Install required Python packages:

```bash
pip install -r requirements.txt
```

### 🛢️ MongoDB Setup

* Go to [MongoDB Atlas](https://www.mongodb.com/atlas) and create a free cluster.
* Copy your connection string (URI).
* Update your `config/settings.py` with the following:

```python
MONGO_URI = "mongodb+srv://<username>:<password>@cluster.mongodb.net/expense_db"
SECRET_KEY = "your-secret-key"
CURRENCY_BASE = "INR"

# Email credentials
EMAIL_USER = "your_email@gmail.com"
EMAIL_PASS = "your_app_password"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
```

### 🧠 Gemini API Setup (AI Insights)

* Visit [Google AI Studio](https://aistudio.google.com/).
* Generate your Gemini API Key.
* Launch the app, navigate to:
  ⚙️ Settings → 🔑 Gemini API Configuration
* Paste your API key and click Save.

### ▶️ Run the App

* Start the Streamlit app:

```bash
streamlit run app.py
```

* Once the server starts, open the app in your browser:
  👉 [http://localhost:8501](http://localhost:8501)

### 🧩 Dependencies

* Key libraries used (included in `requirements.txt`):

```
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
```

### 📧 Email Report Setup (Optional)

* To enable email delivery of daily reports:

  * Turn on 2-Step Verification in your Gmail account.
  * Go to Google Account → Security → App Passwords.
  * Generate a new app password.
  * Use this password in `config/settings.py`:

```python
EMAIL_PASS = "your_generated_app_password"
```

* Now you can send reports via:
  ⚙️ Settings → 📧 Send Daily Report

### 🏅 Future Enhancements

* ✅ Push notifications for budget overspending
* ✅ Integration with UPI or banking APIs for real-time transactions
* ✅ Mobile responsive layout
* ✅ Multi-language support
* ✅ Receipt AI auto-categorization
* ✅ Expense forecasting with LSTM model

### 👨‍💻 Contributors

* Vedanth Reddy — Developer & Researcher
* AI and Data Modules — GPT-powered Integrations



