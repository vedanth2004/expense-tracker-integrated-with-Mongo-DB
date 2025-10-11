import streamlit as st
from config import settings
from auth.authenticator import Authenticator
from database import mongo_manager
from database.mongo_manager import init_db
from features.expense_manager import ExpenseManager
from features.income_manager import IncomeManager
from features.budget_manager import BudgetManager
from features.ocr_processor import OCRProcessor
from features.currency_converter import CurrencyConverter
from analytics.dashboard import render_dashboard
from analytics import stock_trends
from analytics.reports import Reports
from analytics.ai_insights import AIInsights
from collaboration.shared_accounts import SharedAccounts
from gamification.achievements import Achievements
from notifications.email_handler import EmailHandler
from ui.theme import apply_theme
from ui.components import nav_bar, animated_header
from datetime import datetime
from features.chatbot import ChatBot
from notifications import email_handler
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import uuid
import traceback
import traceback
import smtplib


# ---------- Page Config ----------
st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="wide")
apply_theme()

# ---------- Initialize DB ----------
db = init_db()

# ---------- Initialize Services ----------
auth = Authenticator(settings.SECRET_KEY)
email_service = EmailHandler(settings)
currency = CurrencyConverter(settings.CURRENCY_BASE)
ai = AIInsights()
ocr = OCRProcessor()
reports = Reports()
shared = SharedAccounts()
achievements = Achievements()

# ---------- Session Setup ----------
st.session_state.setdefault("token", None)
st.session_state.setdefault("user", None)
st.session_state.setdefault("logged_in", False)  # Flag for rendering authenticated flow

# ---------- Header ----------
animated_header()

# ---------- Authentication Flow ----------
if not st.session_state.logged_in:
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    # ---------------- Login Tab ----------------
    with tab_login:
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted_login = st.form_submit_button("Login")

            if submitted_login:
                if not email or not password:
                    st.warning("Please fill all fields")
                else:
                    ok, user, token, msg = auth.login(email, password)
                    if ok:
                        st.session_state.token = token
                        st.session_state.user = user
                        st.session_state.logged_in = True
                        st.success("✅ Logged in successfully!")
                        st.rerun()  # Reload app immediately after login
                    else:
                        st.error(msg)

    # ---------------- Signup Tab ----------------
    with tab_signup:
        st.subheader("Create New Account")
        with st.form("signup_form"):
            name = st.text_input("Name", key="signup_name")
            email2 = st.text_input("Email", key="signup_email")
            pass1 = st.text_input("Password", type="password", key="signup_password")
            submitted_signup = st.form_submit_button("Sign Up")

            if submitted_signup:
                if not name or not email2 or not pass1:
                    st.warning("Please fill all fields")
                else:
                    ok, msg = auth.signup(name, email2, pass1)
                    if ok:
                        st.success("🎉 Account created! Please log in.")
                    else:
                        st.error(msg)

    st.stop()  # Stop rendering the rest until login

# ---------- Authenticated Flow ----------
user = st.session_state.user
page = nav_bar([
    "Dashboard", "Expenses", "Income", "Budgets",
    "Reports", "AI Insights", "Stock Trends",  # <-- new page added
    "Collaboration", "Gamification", "Settings"
])
# ---------- Instantiate Floating ChatBot ----------
chatbot = ChatBot(user["id"])
chatbot.render()

# ---------- Instantiate Managers ----------
exp_mgr = ExpenseManager(user_id=user["id"], currency=currency)
inc_mgr = IncomeManager(user_id=user["id"], currency=currency)
bud_mgr = BudgetManager(user_id=user["id"], currency=currency)

# ---------- Pages ----------
if page == "Dashboard":
    from analytics.dashboard import render_dashboard
    render_dashboard(db, user["id"], currency, user_name=user["name"])


elif page == "Expenses":
    st.subheader("Add Expense")

    # Initialize session state flags
    if "expense_added" not in st.session_state:
        st.session_state.expense_added = False

    # --- Expense input form ---
    col1, col2, col3 = st.columns(3)
    with col1:
        amount = st.text_input("Amount", key="amount_input")
    with col2:
        category = st.selectbox(
            "Category",
            ["Food", "Transport", "Rent", "Utilities", "Entertainment", "Other"],
            key="category_input"
        )
    with col3:
        currency_code = st.text_input("Currency", value=currency.base, key="currency_input")

    note = st.text_input("Note", key="note_input")
    date = st.date_input("Date", key="date_input")
    receipt = st.file_uploader(
        "Receipt image (optional)", type=["png", "jpg", "jpeg"], key="receipt_input"
    )

    # --- Add Expense button ---
    if st.button("Add Expense", key="add_expense_btn"):
        try:
            amt = float(str(amount).replace(",", ""))
            from datetime import datetime, date as dt_date
            date_val = datetime.combine(date, datetime.min.time()) if isinstance(date, dt_date) else date
            ocr_text = ocr.extract_text(receipt) if receipt else None

            exp_mgr.add_expense(
                amount=amt,
                category=category,
                note=note,
                date=date_val,
                currency_code=currency_code.upper(),
                receipt_text=ocr_text
            )

            st.session_state.expense_added = True
            st.rerun()  # ✅ Refresh immediately after adding
        except ValueError:
            st.error("Invalid amount")

    # --- Show success message ---
    if st.session_state.expense_added:
        st.success("Expense added ✅")
        st.session_state.expense_added = False

    st.divider()
    st.subheader("Your Expenses")

    # --- Fetch updated expenses ---
    df_expenses = exp_mgr.list_expenses_df().copy()

    if df_expenses.empty:
        st.info("No expenses logged yet.")
    else:
        headers = ["Category", "Amount", "Note", "Date", "Receipt", "Delete"]
        cols = st.columns([2, 2, 3, 2, 2, 1])
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")

        for idx, row in df_expenses.iterrows():
            cols = st.columns([2, 2, 3, 2, 2, 1])
            cols[0].markdown(row['category'])
            cols[1].markdown(f"₹{row['amount']:,.2f} ({row.get('currency', currency.base)})")
            cols[2].markdown(row.get('note', '—'))
            cols[3].markdown(str(row['date']))

            receipt_preview = row.get('receipt_text', '')[:30]
            if len(row.get('receipt_text', '')) > 30:
                receipt_preview += "..."
            cols[4].markdown(receipt_preview)

            # --- Delete button (single click refresh, same as Budgets) ---
            if cols[5].button("🗑️", key=f"del_exp_{row['id']}"):
                from database import mongo_manager
                ok = mongo_manager.delete_expense(row['id'], user["id"])
                if ok:
                    st.success(f"Deleted expense: {row['category']} - ₹{row['amount']:,.2f}")
                    st.rerun()  # ✅ Instantly refresh the expense list
                else:
                    st.error("Failed to delete expense")

    st.info("Click **🗑️** to remove an expense.")






elif page == "Income":
    st.subheader("Add Income")

    # Initialize session state flags
    if "income_added" not in st.session_state:
        st.session_state.income_added = False
    if "deleted_income_id" not in st.session_state:
        st.session_state.deleted_income_id = None
        st.session_state.deleted_msg = ""
    if "refresh_trigger_income" not in st.session_state:
        st.session_state.refresh_trigger_income = None

    # --- Income input form ---
    col1, col2 = st.columns(2)
    with col1:
        amount = st.text_input("Amount", key="income_amount_input")
    with col2:
        source = st.selectbox(
            "Source",
            ["Salary", "Business", "Investment", "Other"],
            key="income_source_input"
        )
    date = st.date_input("Date", key="income_date_input")
    currency_code = st.text_input("Currency", value=currency.base, key="income_currency_input")

    # --- Add Income button ---
    if st.button("Add Income", key="add_income_btn"):
        try:
            amt = float(str(amount).replace(",", ""))
            inc_mgr.add_income(
                amount=amt,
                source=source,
                date=date,
                currency_code=currency_code.upper()
            )
            st.session_state.income_added = True
            st.session_state.refresh_trigger_income = datetime.now()
        except Exception:
            st.error("Invalid amount")

    # --- Show success message ---
    if st.session_state.income_added:
        st.success("Income added ✅")
        st.session_state.income_added = False

    st.divider()
    st.subheader("Income List")

    # --- Fetch updated income ---
    _ = st.session_state.get("refresh_trigger_income")  # triggers rerun naturally
    df_income = inc_mgr.list_income_df()

    if df_income.empty:
        st.info("No income logged yet.")
    else:
        headers = ["Source", "Amount", "Date", "Currency", "Delete"]
        cols = st.columns([2, 2, 2, 2, 1])
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")

        for idx, row in df_income.iterrows():
            cols = st.columns([2, 2, 2, 2, 1])
            cols[0].markdown(row.get('source', '—'))
            cols[1].markdown(f"₹{row['amount']:,.2f}")
            cols[2].markdown(str(row['date']))
            cols[3].markdown(row.get('currency', currency.base))

            delete_key = f"del_income_{row['id']}"
            if cols[4].button("🗑️", key=delete_key):
                from database import mongo_manager
                ok = mongo_manager.db.income.delete_one({
                    "user_id": user["id"],
                    "_id": mongo_manager.ObjectId(row['id'])
                }).acknowledged

                if ok:
                    st.session_state.deleted_income_id = row['id']
                    st.session_state.deleted_msg = f"click delete again: {row.get('source', '')} - ₹{row['amount']:,.2f}"
                else:
                    st.error("Failed to delete income")

            # --- Show deletion message directly below the deleted row ---
            if st.session_state.deleted_income_id == row['id']:
                st.success(st.session_state.deleted_msg)
                st.session_state.deleted_income_id = None
                st.session_state.deleted_msg = ""
                st.session_state.refresh_trigger_income = datetime.now()
                st.rerun()

    st.info("Click **🗑️** to remove an income record.")



elif page == "Budgets":
    st.subheader("Budgets")

    if "refresh_budgets" not in st.session_state:
        st.session_state.refresh_budgets = 0

    # --- Add / Set Budget ---
    category = st.selectbox(
        "Category",
        ["Food", "Transport", "Rent", "Utilities", "Entertainment", "Other"]
    )
    monthly_limit = st.text_input("Monthly Limit")

    if st.button("Set Budget"):
        try:
            amt = float(str(monthly_limit).replace(",", ""))
            from database import mongo_manager

            # ✅ Update if exists, else insert new (avoids duplicate key error)
            mongo_manager.db.budgets.update_one(
                {"user_id": user["id"], "category": category},
                {
                    "$set": {
                        "monthly_limit": amt,
                        "remaining": amt,
                        "spent": 0,
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                },
                upsert=True
            )

            st.success("Budget set ✅")
            st.session_state.refresh_budgets += 1
            st.rerun()

        except ValueError:
            st.error("Invalid limit value.")
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()
    _ = st.session_state.refresh_budgets  # use counter to force refresh

    # --- Display budgets ---
    from database import mongo_manager
    df_budgets = bud_mgr.list_budgets_df()

    if df_budgets.empty:
        st.info("No budgets set yet.")
    else:
        headers = ["Category", "Monthly Limit", "Spent", "Remaining", "Delete"]
        cols = st.columns([2, 2, 2, 2, 1])
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")

        for idx, row in df_budgets.iterrows():
            cols = st.columns([2, 2, 2, 2, 1])
            cols[0].markdown(row['category'])
            cols[1].markdown(f"₹{row['monthly_limit']:,.2f}")
            cols[2].markdown(f"₹{row.get('spent', 0):,.2f}")
            cols[3].markdown(f"₹{row.get('remaining', row['monthly_limit']):,.2f}")

            # Delete budget button
            if cols[4].button("🗑️", key=f"del_budget_{row['category']}"):
                ok = mongo_manager.db.budgets.delete_one({
                    "user_id": user["id"],
                    "category": row['category']
                }).acknowledged
                if ok:
                    st.success(f"Deleted budget: {row['category']}")
                    st.session_state.refresh_budgets += 1
                    st.rerun()
                else:
                    st.error("Failed to delete budget")

    st.info(bud_mgr.budget_status_summary())



elif page == "Reports":
    st.subheader("Generate Report")
    start = st.date_input("Start Date")
    end = st.date_input("End Date")
    fmt = st.selectbox("Format", ["CSV", "PDF"])
    if st.button("Download"):
        if fmt == "CSV":
            data = reports.generate_csv(user["id"], start, end)
            st.download_button("Download CSV", data=data, file_name="report.csv", mime="text/csv")
        else:
            pdf_bytes = reports.generate_pdf(user["id"], start, end)
            st.download_button("Download PDF", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")

elif page == "AI Insights":
    st.header("💡 AI Financial Insights")

    prompt = st.text_area("Ask about your finances (e.g., 'Where did I overspend last month?')")

    if st.button("Analyze"):
        if not prompt.strip():
            st.warning("Please enter a question or prompt.")
        else:
            with st.spinner("Analyzing your data..."):
                result, error = ai.analyze(user["id"], prompt)

            if error:
                st.error(error)
                st.info("➡️ Go to **Settings → Gemini API Configuration** to add your key.")
            else:
                st.markdown("### ✨ AI Insights:")
                st.write(result)


elif page == "Collaboration":
    st.subheader("Shared Accounts")
    email_other = st.text_input("Invite user email")
    if st.button("Invite"):
        ok, msg = shared.invite(user["id"], email_other)
        st.success(msg) if ok else st.error(msg)
    df_shared = shared.list_shared(user["id"])
    if df_shared is not None:
        st.dataframe(df_shared, use_container_width=True)
    else:
        st.write("No shares yet.")

elif page == "Gamification":
    st.subheader("Achievements")
    st.write(achievements.summary(db, user["id"]))
    st.dataframe(achievements.list_badges(db, user["id"]), use_container_width=True)

elif page == "Settings":



    from analytics.reports import Reports  # ✅ Import the class directly
    reports = Reports()

    st.header("⚙️ Settings")

    # --- Gemini API Configuration ---
    with st.expander("🔑 Gemini API Configuration", expanded=True):
        st.write("Provide your Gemini API key to enable AI Insights.")
        existing_key = mongo_manager.get_gemini_api_key(user["id"])
        new_key = st.text_input(
            "Enter your Gemini API Key",
            type="password",
            value=existing_key if existing_key else ""
        )

        if st.button("Save API Key"):
            if new_key.strip():
                mongo_manager.save_gemini_api_key(user["id"], new_key.strip())
                st.success("✅ Gemini API key saved successfully! You can now use AI Insights.")
            else:
                st.warning("⚠️ Please enter a valid API key.")

    # --- Manual Report Email ---
    with st.expander("📧 Send Daily Report", expanded=True):
        st.write("You can send your financial report via email.")
        recipient_email = st.text_input("Recipient Email", value=user.get("email", ""))
        report_format = st.selectbox("Report Format", ["CSV", "PDF"])

        # Optional: select custom date range
        start_date = st.date_input("Start Date", value=date.today().replace(day=1))
        end_date = st.date_input("End Date", value=date.today())

        if st.button("Send Report via Email"):
            try:
                # --- Generate Report ---
                if report_format == "CSV":
                    data_bytes = reports.generate_csv(
                        user["id"], start=start_date, end=end_date
                    )
                    filename = "report.csv"
                    body = "Attached is your latest financial report (CSV)."
                else:  # PDF
                    data_bytes = reports.generate_pdf(
                        user["id"], start=start_date, end=end_date
                    )
                    filename = "report.pdf"
                    body = "Attached is your latest financial report (PDF)."

                # --- Compose Email ---
                msg = MIMEMultipart()
                msg["From"] = email_service.user
                msg["To"] = recipient_email
                msg["Subject"] = "Your Financial Report"
                msg.attach(MIMEText(body))

                # --- Attach File ---
                part = MIMEBase("application", "octet-stream")
                part.set_payload(data_bytes)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={filename}")
                msg.attach(part)

                # --- Send Email ---
                with smtplib.SMTP(email_service.host, email_service.port) as server:
                    server.starttls()
                    server.login(email_service.user, email_service.password)
                    server.sendmail(email_service.user, [recipient_email], msg.as_string())

                st.success(f"✅ Report sent successfully to {recipient_email}")

            except Exception as e:
                st.error(f"❌ Failed to send email. Details: {e}")
                st.code(traceback.format_exc())
elif page == "Stock Trends":
    from analytics.stock_trends import render_stock_trends_page
    render_stock_trends_page(user["id"])



# ---------- Logout ----------
if st.sidebar.button("Logout"):
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.logged_in = False
    st.experimental_rerun = None  # Removed deprecated rerun
    st.stop()
