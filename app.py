import streamlit as st
import pandas as pd
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
    "Bills", "Split Bills", "Goals", "Debts",
    "Reports", "AI Insights", "Stock Trends",
    "Collaboration", "Badges", "Settings"
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
    if "auto_filled_data" not in st.session_state:
        st.session_state.auto_filled_data = None

    # --- Initialize receipt processing flag ---
    if "receipt_processed" not in st.session_state:
        st.session_state.receipt_processed = {}
    
    # --- Receipt upload section ---
    receipt = st.file_uploader(
        "Receipt image (optional)", type=["png", "jpg", "jpeg"], key="receipt_input"
    )

    # --- Auto-add expense from receipt using Gemini ---
    if receipt is not None:
        # Get receipt identifier
        receipt_name = getattr(receipt, 'name', None) or str(id(receipt))
        
        # Check if we've already processed this receipt
        if receipt_name not in st.session_state.receipt_processed:
            # Get Gemini API key
            api_key = st.session_state.get("gemini_api_key") or mongo_manager.get_gemini_api_key(user["id"])
            
            if api_key:
                with st.spinner("🤖 Analyzing receipt with AI..."):
                    try:
                        parsed_data = ocr.parse_receipt_with_gemini(receipt, api_key)
                    except Exception as e:
                        st.error(f"❌ Error analyzing receipt: {str(e)}")
                        parsed_data = None
                    
                    if parsed_data and "amount" in parsed_data and parsed_data["amount"]:
                        # Validate the parsed data
                        try:
                            amount = float(parsed_data.get("amount", 0))
                            
                            if amount > 0:
                                # Parse other fields
                                category = parsed_data.get("category", "Other")
                                if category not in ["Food", "Transport", "Rent", "Utilities", "Entertainment", "Other"]:
                                    category = "Other"
                                
                                note = parsed_data.get("note", "Receipt")
                                currency_code = parsed_data.get("currency", currency.base).upper()
                                
                                # Parse date
                                import datetime as dt_module
                                try:
                                    date_str = parsed_data.get("date", "")
                                    if date_str:
                                        parsed_date = dt_module.datetime.strptime(date_str, "%Y-%m-%d").date()
                                    else:
                                        parsed_date = dt_module.date.today()
                                except:
                                    parsed_date = dt_module.date.today()
                                
                                # Convert date to datetime
                                date_val = dt_module.datetime.combine(parsed_date, dt_module.datetime.min.time())
                                
                                # Extract OCR text
                                try:
                                    ocr_text = ocr.extract_text(receipt)
                                except:
                                    ocr_text = "Receipt analyzed by AI"
                                
                                # Add expense directly to database
                                exp_mgr.add_expense(
                                    amount=amount,
                                    category=category,
                                    note=note,
                                    date=date_val,
                                    currency_code=currency_code,
                                    receipt_text=ocr_text
                                )
                                
                                st.success(f"✅ Expense added successfully! Amount: {currency_code} {amount:,.2f}")
                                st.session_state.expense_added = True
                                
                                # Mark this receipt as processed
                                st.session_state.receipt_processed[receipt_name] = True
                                
                                # Refresh to show new expense
                                st.rerun()
                            else:
                                st.warning("⚠️ Invalid amount extracted from receipt. Please add manually.")
                        except (ValueError, Exception) as e:
                            st.warning(f"⚠️ Could not extract valid amount from receipt: {str(e)}. Please add manually.")
                    else:
                        st.info("⚠️ Could not parse receipt automatically. Please add expense manually.")
            else:
                st.info("💡 Add Gemini API key in Settings to enable automatic receipt parsing.")

    # --- Initialize session state for form fields ---
    if "amount_value" not in st.session_state:
        st.session_state.amount_value = ""
    if "note_value" not in st.session_state:
        st.session_state.note_value = ""
    if "currency_value" not in st.session_state:
        st.session_state.currency_value = currency.base
    if "category_index" not in st.session_state:
        st.session_state.category_index = 0
    if "date_value" not in st.session_state:
        import datetime as dt_module
        st.session_state.date_value = dt_module.date.today()
    
    # --- Auto-fill form fields if data is available ---
    if st.session_state.auto_filled_data:
        import datetime as dt_module
        
        # Only update if amount is present
        if "amount" in st.session_state.auto_filled_data and st.session_state.auto_filled_data["amount"]:
            st.session_state.amount_value = str(st.session_state.auto_filled_data.get("amount", ""))
        
        if "note" in st.session_state.auto_filled_data:
            st.session_state.note_value = st.session_state.auto_filled_data.get("note", "")
        
        if "currency" in st.session_state.auto_filled_data:
            st.session_state.currency_value = st.session_state.auto_filled_data.get("currency", currency.base)
        
        # Handle category
        if "category" in st.session_state.auto_filled_data:
            categories = ["Food", "Transport", "Rent", "Utilities", "Entertainment", "Other"]
            parsed_cat = st.session_state.auto_filled_data.get("category", "")
            if parsed_cat in categories:
                st.session_state.category_index = categories.index(parsed_cat)
        
        # Handle date
        if "date" in st.session_state.auto_filled_data:
            try:
                date_str = st.session_state.auto_filled_data.get("date", "")
                if date_str:
                    st.session_state.date_value = dt_module.datetime.strptime(date_str, "%Y-%m-%d").date()
            except:
                pass
    
    # --- Expense input form ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        amount = st.text_input("Amount", value=st.session_state.amount_value, key="amount_input")
    
    with col2:
        categories = ["Food", "Transport", "Rent", "Utilities", "Entertainment", "Other"]
        category = st.selectbox(
            "Category",
            categories,
            index=st.session_state.category_index,
            key="category_input"
        )
    
    with col3:
        currency_code = st.text_input("Currency", value=st.session_state.currency_value, key="currency_input")

    note = st.text_input("Note", value=st.session_state.note_value, key="note_input")
    
    import datetime as dt_module
    date = st.date_input("Date", value=st.session_state.date_value, key="date_input")

    # --- Reset auto-fill data after showing ---
    if receipt is None:
        st.session_state.auto_filled_data = None

    # --- Add Expense button ---
    if st.button("Add Expense", key="add_expense_btn"):
        # Validate and clean amount
        if not amount:
            st.error("❌ Please enter an amount")
        else:
            try:
                # Clean and convert amount
                amt_str = str(amount).replace(",", "").strip()
                if not amt_str:
                    st.error("❌ Please enter a valid amount")
                else:
                    amt = float(amt_str)
                    
                    # Validate amount is positive
                    if amt <= 0:
                        st.error("❌ Amount must be greater than 0")
                    else:
                        # All validations passed, add the expense
                        from datetime import datetime, date as dt_date
                        date_val = datetime.combine(date, datetime.min.time()) if isinstance(date, dt_date) else date
                        
                        # Extract OCR text from receipt if available
                        ocr_text = None
                        if receipt:
                            try:
                                ocr_text = ocr.extract_text(receipt)
                            except:
                                ocr_text = ""

                        exp_mgr.add_expense(
                            amount=amt,
                            category=category,
                            note=note,
                            date=date_val,
                            currency_code=currency_code.upper(),
                            receipt_text=ocr_text
                        )

                        # Clear form fields and widget state
                        st.session_state.amount_value = ""
                        st.session_state.note_value = ""
                        st.session_state.currency_value = currency.base
                        st.session_state.category_index = 0
                        import datetime as dt_module
                        st.session_state.date_value = dt_module.date.today()
                        st.session_state.auto_filled_data = None
                        
                        # Clear widget states
                        if "amount_input" in st.session_state:
                            del st.session_state.amount_input
                        if "note_input" in st.session_state:
                            del st.session_state.note_input
                        if "currency_input" in st.session_state:
                            del st.session_state.currency_input
                        if "category_input" in st.session_state:
                            del st.session_state.category_input
                        if "date_input" in st.session_state:
                            del st.session_state.date_input
                        
                        st.session_state.expense_added = True
                        st.rerun()  # ✅ Refresh immediately after adding
                        
            except ValueError:
                st.error(f"❌ Invalid amount: '{amount}'. Please enter a valid number.")
            except Exception as e:
                st.error(f"❌ Error adding expense: {str(e)}")

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
    tab1, tab2 = st.tabs(["👥 My Shared Accounts", "🌐 Accounts Shared With Me"])
    
    with tab1:
        st.subheader("👥 Share Your Account")
        st.write("Invite users to view your expenses and budgets.")
        
        email_other = st.text_input("Enter user's email to invite", placeholder="user@example.com")
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("➕ Invite"):
                if email_other:
                    ok, msg = shared.invite(user["id"], email_other)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter an email")
        
        st.divider()
        st.subheader("📋 People You've Shared With")
        df_shared = shared.list_shared(user["id"])
        if df_shared is not None and not df_shared.empty:
            for idx, row in df_shared.iterrows():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"📧 **{row['member_email']}**")
                with col2:
                    st.write(f"Added: {row['created_at'][:10] if row.get('created_at') else 'Unknown'}")
                with col3:
                    if st.button("🗑️", key=f"remove_{idx}"):
                        if shared.remove_shared_user(user["id"], row['member_email']):
                            st.success(f"Removed {row['member_email']}")
                            st.rerun()
            st.info("💡 These users can now view your expenses, budgets, and financial data.")
        else:
            st.info("👤 No shared accounts yet. Invite users above to get started!")
    
    with tab2:
        st.subheader("🌐 Accounts Shared With Me")
        st.write("Accounts that others have shared with you.")
        
        # Get accounts shared with this user
        shared_accounts = shared.get_shared_accounts_for_user(user.get("email", ""))
        
        if shared_accounts:
            for account in shared_accounts:
                with st.expander(f"📂 {account.get('owner_name', 'Unknown')} - {account.get('owner_email', '')}"):
                    owner_id = account.get('owner_id')
                    
                    # Get expenses
                    owner_exps = mongo_manager.list_expenses(owner_id, limit=50)
                    if owner_exps:
                        st.subheader("📊 Recent Expenses")
                        st.dataframe(pd.DataFrame(owner_exps), use_container_width=True)
                    else:
                        st.info("No expenses to show")
                    
                    # Get budgets
                    owner_budgets = mongo_manager.list_budgets(owner_id)
                    if owner_budgets:
                        st.subheader("💰 Budgets")
                        budget_df = pd.DataFrame(owner_budgets)
                        st.dataframe(budget_df, use_container_width=True)
                    else:
                        st.info("No budgets to show")
        else:
            st.info("🔒 No accounts are currently shared with you.")
            st.write("Ask account owners to share their data with you!")

elif page == "Badges":
    st.header("🏆 Your Badges")
    badge_summary = achievements.summary(db, user["id"])
    st.markdown(f"### {badge_summary}")
    st.divider()
    
    df_badges = achievements.list_badges(db, user["id"])
    
    if df_badges.empty:
        st.info("🎯 No badges yet! Start tracking expenses to earn your first badge.")
    else:
        # Display badges in a nice format
        st.subheader("🎖️ Unlocked Badges")
        for idx, row in df_badges.iterrows():
            with st.container():
                col1, col2 = st.columns([2, 4])
                with col1:
                    st.markdown(f"### {row['badge']}")
                with col2:
                    st.markdown(f"*{row['description']}*")
                st.divider()

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

elif page == "Bills":
    st.header("📅 Bill Reminders")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Bill", "📋 Due Bills", "✅ Paid Bills"])
    
    with tab1:
        st.subheader("Add Bill Reminder")
        col1, col2 = st.columns(2)
        with col1:
            bill_title = st.text_input("Bill Name", placeholder="Electricity, Rent, etc.")
            bill_amount = st.text_input("Amount")
            due_date = st.date_input("Due Date")
        with col2:
            bill_category = st.selectbox("Category", ["Utilities", "Rent", "Insurance", "Other"])
            bill_notes = st.text_area("Notes (optional)")
        
        if st.button("➕ Add Bill"):
            if bill_title and bill_amount:
                try:
                    amount = float(bill_amount)
                    ok = mongo_manager.add_bill_reminder(user["id"], bill_title, amount, due_date, bill_category, bill_notes)
                    if ok:
                        st.success(f"✅ Added {bill_title} bill reminder")
                        st.rerun()
                except:
                    st.error("Invalid amount")
    
    with tab2:
        all_bills = mongo_manager.list_bill_reminders(user["id"])
        due_bills = [b for b in all_bills if not b.get("is_paid", False)]
        
        if due_bills:
            for bill in due_bills:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    st.write(f"📋 **{bill.get('title')}**")
                with col2:
                    due = bill.get("due_date")
                    if isinstance(due, str):
                        due = due[:10]
                    st.write(f"Due: {due}")
                with col3:
                    st.write(f"₹{bill.get('amount', 0):,.2f}")
                with col4:
                    if st.button("✅", key=f"pay_{bill.get('_id')}"):
                        mongo_manager.mark_bill_paid(str(bill.get('_id')), user["id"])
                        st.rerun()
                st.divider()
        else:
            st.success("🎉 All bills are paid!")
    
    with tab3:
        all_bills = mongo_manager.list_bill_reminders(user["id"])
        paid_bills = [b for b in all_bills if b.get("is_paid", False)]
        if paid_bills:
            st.dataframe(pd.DataFrame(paid_bills), use_container_width=True)
        else:
            st.info("No paid bills yet")

elif page == "Split Bills":
    st.header("👥 Split Bills")
    
    st.subheader("Create Group Expense")
    col1, col2 = st.columns(2)
    with col1:
        description = st.text_input("What is this expense for?")
        total_amount = st.text_input("Total Amount")
        split_type = st.selectbox("Split Type", ["Equal Split", "Custom Amounts"])
    with col2:
        member_emails = st.text_area("Enter member emails (comma-separated)", placeholder="email1@example.com, email2@example.com")
    
    if st.button("➕ Add Group Expense"):
        if description and total_amount and member_emails:
            try:
                amount = float(total_amount)
                emails = [e.strip() for e in member_emails.split(",")]
                members = [{"email": email, "amount": amount/len(emails), "paid": False} for email in emails]
                ok = mongo_manager.add_group_expense(user["id"], description, amount, split_type.lower().replace(" ", "_"), members)
                if ok:
                    st.success(f"✅ Created group expense: {description}")
                    st.rerun()
            except:
                st.error("Invalid amount")
    
    st.divider()
    st.subheader("My Group Expenses")
    group_exps = mongo_manager.list_group_expenses(user["id"])
    if group_exps:
        for exp in group_exps:
            with st.expander(f"💰 {exp.get('description')} - ₹{exp.get('amount'):,.2f}"):
                st.write("**Members:**")
                for member in exp.get('members', []):
                    status = "✅ Paid" if member.get('paid') else "⏳ Pending"
                    st.write(f"- {member.get('email')}: ₹{member.get('amount'):,.2f} {status}")
    else:
        st.info("No group expenses yet")

elif page == "Goals":
    st.header("🎯 Financial Goals")
    
    tab1, tab2 = st.tabs(["➕ New Goal", "📊 My Goals"])
    
    with tab1:
        st.subheader("Create Financial Goal")
        col1, col2 = st.columns(2)
        with col1:
            goal_title = st.text_input("Goal Name", placeholder="Vacation, Emergency Fund, etc.")
            target_amount = st.text_input("Target Amount (₹)")
            target_date = st.date_input("Target Date")
        with col2:
            goal_category = st.selectbox("Category", ["Travel", "Emergency", "Investment", "Purchase", "Other"])
            current_amount = st.text_input("Current Amount (₹)", value="0")
        
        if st.button("➕ Add Goal"):
            if goal_title and target_amount:
                try:
                    target = float(target_amount)
                    current = float(current_amount)
                    
                    ok = mongo_manager.add_financial_goal(user["id"], goal_title, target, target_date, goal_category)
                    if ok and current > 0:
                        goals = mongo_manager.list_financial_goals(user["id"])
                        if goals:
                            mongo_manager.update_goal_progress(str(goals[-1].get("_id")), current)
                    st.success(f"✅ Created goal: {goal_title}")
                    st.rerun()
                except:
                    st.error("Invalid amount")
    
    with tab2:
        goals = mongo_manager.list_financial_goals(user["id"])
        if goals:
            for goal in goals:
                current = goal.get("current_amount", 0)
                target = goal.get("target_amount", 1)
                progress = min(current / target * 100, 100)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"🎯 {goal.get('title')}")
                    st.progress(progress / 100)
                    st.write(f"₹{current:,.2f} / ₹{target:,.2f} ({progress:.1f}%)")
                with col2:
                    add_amount = st.number_input("Add ₹", min_value=0, key=f"goal_{goal.get('_id')}")
                    if st.button("💵 Contribute", key=f"btn_{goal.get('_id')}"):
                        mongo_manager.update_goal_progress(str(goal.get('_id')), add_amount)
                        st.rerun()
        else:
            st.info("No goals set yet")

elif page == "Debts":
    st.header("💳 Debt Management")
    
    tab1, tab2 = st.tabs(["➕ Add Debt", "📋 My Debts"])
    
    with tab1:
        st.subheader("Add Debt Record")
        col1, col2 = st.columns(2)
        with col1:
            creditor = st.text_input("Creditor Name", placeholder="Credit Card, Loan, etc.")
            total_amount = st.text_input("Total Debt Amount")
            interest_rate = st.text_input("Interest Rate (%)")
        with col2:
            min_payment = st.text_input("Minimum Payment")
            debt_notes = st.text_area("Notes (optional)")
        
        if st.button("➕ Add Debt"):
            if creditor and total_amount:
                try:
                    total = float(total_amount)
                    interest = float(interest_rate) if interest_rate else 0
                    minimum = float(min_payment) if min_payment else total * 0.02
                    ok = mongo_manager.add_debt(user["id"], creditor, total, interest, minimum, debt_notes)
                    if ok:
                        st.success(f"✅ Added debt: {creditor}")
                        st.rerun()
                except:
                    st.error("Invalid input")
    
    with tab2:
        debts = mongo_manager.list_debts(user["id"])
        if debts:
            total_debt = sum(d.get("remaining_amount", 0) for d in debts)
            st.metric("💳 Total Remaining Debt", f"₹{total_debt:,.2f}")
            
            for debt in debts:
                remaining = debt.get("remaining_amount", 0)
                total = debt.get("total_amount", 1)
                paid_percent = (total - remaining) / total * 100
                
                with st.expander(f"💳 {debt.get('creditor_name')} - ₹{remaining:,.2f} remaining"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Total: ₹{debt.get('total_amount'):,.2f}")
                        st.progress(paid_percent / 100)
                    with col2:
                        st.write(f"Interest: {debt.get('interest_rate', 0)}%")
                        st.write(f"Min Payment: ₹{debt.get('minimum_payment', 0):,.2f}")
                        
                        payment_amount = st.number_input("Payment", min_value=0.0, key=f"pay_{debt.get('_id')}")
                        if st.button("💵 Record Payment", key=f"btn_{debt.get('_id')}"):
                            mongo_manager.record_debt_payment(str(debt.get("_id")), payment_amount)
                            st.rerun()
        else:
            st.info("No debts recorded")

# ---------- Logout ----------
if st.sidebar.button("Logout"):
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.logged_in = False
    st.experimental_rerun = None  # Removed deprecated rerun
    st.stop()
