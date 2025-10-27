# database/mongo_manager.py
import datetime
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
import streamlit as st
from config.settings import settings
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

# -----------------------------
# MongoDB Client
# -----------------------------
client = MongoClient(os.getenv("MONGO_URI"))
db = client["expense_tracker"]
@st.cache_resource
def get_client():
    mongo_uri = settings.MONGO_URI
    if not mongo_uri:
        raise RuntimeError(
            "MongoDB URI not set. Put it in .streamlit/secrets.toml as 'mongo_uri' or set MONGO_URI env var."
        )
    return MongoClient(mongo_uri)

def init_db():
    client = get_client()
    db = client["expense_tracker"]

    # create indexes if not exist
    try:
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.expenses.create_index([("user_id", ASCENDING), ("date", DESCENDING)])
        db.income.create_index([("user_id", ASCENDING), ("date", DESCENDING)])
        db.budgets.create_index([("user_id", ASCENDING), ("category", ASCENDING)], unique=True)
        db.shares.create_index([("owner_id", ASCENDING), ("member_email", ASCENDING)], unique=True)
    except Exception as e:
        logging.warning(f"Index creation error: {e}")
    return db

# -----------------------------
# Users
# -----------------------------
def create_user(name: str, email: str, password_hash: bytes):
    db = init_db()
    try:
        res = db.users.insert_one({
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.datetime.utcnow()
        })
        return str(res.inserted_id)
    except Exception as e:
        logging.error(f"create_user error: {e}")
        return None

def get_user_by_email(email: str):
    db = init_db()
    return db.users.find_one({"email": email})

def get_user_by_id(user_id: str):
    db = init_db()
    return db.users.find_one({"_id": str(user_id)})

# -----------------------------
# Expenses
# -----------------------------
# -----------------------------
# Expenses
# -----------------------------
def add_expense(user_id: str, amount: float, category: str, note: str="", date=None, currency: str="USD", receipt_text: str="", is_tax_deductible: bool=False, tax_category: str=""):
    db = init_db()
    uid = str(user_id)
    # Convert date to datetime
    if date and isinstance(date, datetime.date) and not isinstance(date, datetime.datetime):
        date = datetime.datetime.combine(date, datetime.datetime.min.time())
    elif not date:
        date = datetime.datetime.utcnow()
    doc = {
        "user_id": uid,
        "amount": float(amount),
        "category": category,
        "note": note,
        "date": date,
        "currency": currency,
        "receipt_text": receipt_text,
        "is_tax_deductible": is_tax_deductible,
        "tax_category": tax_category,
        "created_at": datetime.datetime.utcnow()
    }
    try:
        db.expenses.insert_one(doc)
        return True
    except Exception as e:
        logging.error(f"add_expense error: {e}")
        return False

def list_expenses(user_id: str, limit: int=200):
    db = init_db()
    uid = str(user_id)
    cursor = db.expenses.find({"user_id": uid}).sort("date", DESCENDING).limit(limit)
    rows = []
    for r in cursor:
        r["id"] = str(r["_id"])
        r["date"] = r.get("date").isoformat() if r.get("date") else ""
        rows.append(r)
    return rows

# -----------------------------
# DELETE EXPENSE (NEW)
# -----------------------------
def delete_expense(expense_id: str, user_id: str) -> bool:
    """
    Deletes a specific expense by its ID for a given user.
    Returns True if deleted, False otherwise.
    """
    db = init_db()
    try:
        res = db.expenses.delete_one({"_id": ObjectId(expense_id), "user_id": str(user_id)})
        return res.deleted_count > 0
    except Exception as e:
        logging.error(f"delete_expense error: {e}")
        return False


# -----------------------------
# Income
# -----------------------------
def add_income(user_id: str, amount: float, source: str, date=None, currency: str="USD"):
    db = init_db()
    uid = str(user_id)
    # Convert date
    if date and isinstance(date, datetime.date) and not isinstance(date, datetime.datetime):
        date = datetime.datetime.combine(date, datetime.datetime.min.time())
    elif not date:
        date = datetime.datetime.utcnow()
    doc = {
        "user_id": uid,
        "amount": float(amount),
        "source": source,
        "date": date,
        "currency": currency,
        "created_at": datetime.datetime.utcnow()
    }
    try:
        db.income.insert_one(doc)
        return True
    except Exception as e:
        logging.error(f"add_income error: {e}")
        return False

def list_income(user_id: str, limit: int=200):
    db = init_db()
    uid = str(user_id)
    cursor = db.income.find({"user_id": uid}).sort("date", DESCENDING).limit(limit)
    rows = []
    for r in cursor:
        rows.append({
            "id": str(r["_id"]),
            "amount": r.get("amount"),
            "source": r.get("source"),
            "date": r.get("date").isoformat() if r.get("date") else "",
            "currency": r.get("currency")
        })
    return rows

# -----------------------------
# Budgets
# -----------------------------
def set_budget(user_id: str, category: str, monthly_limit: float):
    db = init_db()
    uid = str(user_id)
    db.budgets.update_one(
        {"user_id": uid, "category": category},
        {"$set": {"monthly_limit": float(monthly_limit), "updated_at": datetime.datetime.utcnow()}},
        upsert=True
    )
    return True

def list_budgets(user_id: str):
    db = init_db()
    uid = str(user_id)
    return list(db.budgets.find({"user_id": uid}))

# -----------------------------
# Shared Accounts / Collaboration
# -----------------------------
def invite_share(owner_id: str, member_email: str):
    db = init_db()
    uid = str(owner_id)
    try:
        db.shares.insert_one({
            "owner_id": uid,
            "member_email": member_email,
            "created_at": datetime.datetime.utcnow()
        })
        return True
    except Exception as e:
        logging.error(f"invite_share error: {e}")
        return False

def list_shares(owner_id: str):
    db = init_db()
    uid = str(owner_id)
    cursor = db.shares.find({"owner_id": uid})
    out = []
    for r in cursor:
        out.append({
            "member_email": r.get("member_email"),
            "created_at": r.get("created_at").isoformat() if r.get("created_at") else ""
        })
    return out

def get_accounts_shared_with_user(user_email: str):
    """Get all accounts that share data with this user"""
    db = init_db()
    cursor = db.shares.find({"member_email": user_email})
    out = []
    for r in cursor:
        owner_id = r.get("owner_id")
        if owner_id:
            # Handle both string and ObjectId
            if isinstance(owner_id, str):
                owner = db.users.find_one({"_id": ObjectId(owner_id)})
            else:
                owner = db.users.find_one({"_id": owner_id})
            
            if owner:
                out.append({
                    "owner_id": str(owner.get("_id")),
                    "owner_name": owner.get("name"),
                    "owner_email": owner.get("email"),
                    "created_at": r.get("created_at").isoformat() if r.get("created_at") else ""
                })
    return out

def remove_share(owner_id: str, member_email: str):
    """Remove a user from shared accounts"""
    db = init_db()
    try:
        result = db.shares.delete_one({"owner_id": owner_id, "member_email": member_email})
        return result.deleted_count > 0
    except Exception as e:
        logging.error(f"remove_share error: {e}")
        return False

def save_gemini_api_key(user_id, api_key):
    """Save the user's Gemini API key in MongoDB"""
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"gemini_api_key": api_key}})

def get_gemini_api_key(user_id):
    """Retrieve the user's Gemini API key"""
    user = db.users.find_one({"_id": ObjectId(user_id)}, {"gemini_api_key": 1})
    return user.get("gemini_api_key") if user else None
def get_user(user_id: str):
    """Fetch user details by ID."""
    user = db.users.find_one({"_id": user_id})
    if not user:
        return None
    # Convert ObjectId to string if needed
    user["_id"] = str(user["_id"])
    return user
def get_expense_summary(user_id: str):
    db = init_db()
    uid = str(user_id)
    pipeline = [
        {"$match": {"user_id": uid}},
        {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}},
        {"$sort": {"total": -1}}
    ]
    return list(db.expenses.aggregate(pipeline))

# -----------------------------
# Subscriptions / Recurring Expenses
# -----------------------------
def add_subscription(user_id: str, name: str, amount: float, category: str, frequency: str, start_date, notes: str=""):
    """Add a recurring subscription"""
    db = init_db()
    doc = {
        "user_id": user_id,
        "name": name,
        "amount": float(amount),
        "category": category,
        "frequency": frequency,  # "monthly", "yearly", "weekly"
        "start_date": start_date,
        "notes": notes,
        "is_active": True,
        "created_at": datetime.datetime.utcnow()
    }
    try:
        db.subscriptions.insert_one(doc)
        return True
    except Exception as e:
        logging.error(f"add_subscription error: {e}")
        return False

def list_subscriptions(user_id: str):
    """Get all subscriptions for a user"""
    db = init_db()
    return list(db.subscriptions.find({"user_id": user_id, "is_active": True}))

# -----------------------------
# Bill Reminders
# -----------------------------
def add_bill_reminder(user_id: str, title: str, amount: float, due_date, category: str, notes: str=""):
    """Add a bill reminder"""
    db = init_db()
    doc = {
        "user_id": user_id,
        "title": title,
        "amount": float(amount),
        "due_date": due_date,
        "category": category,
        "notes": notes,
        "is_paid": False,
        "created_at": datetime.datetime.utcnow()
    }
    try:
        db.bill_reminders.insert_one(doc)
        return True
    except Exception as e:
        logging.error(f"add_bill_reminder error: {e}")
        return False

def list_bill_reminders(user_id: str):
    """Get all bill reminders for a user"""
    db = init_db()
    return list(db.bill_reminders.find({"user_id": user_id}))

def mark_bill_paid(bill_id: str, user_id: str):
    """Mark a bill as paid"""
    db = init_db()
    try:
        result = db.bill_reminders.update_one(
            {"_id": ObjectId(bill_id), "user_id": user_id},
            {"$set": {"is_paid": True, "paid_at": datetime.datetime.utcnow()}}
        )
        return result.modified_count > 0
    except Exception as e:
        logging.error(f"mark_bill_paid error: {e}")
        return False

# -----------------------------
# Split Bills / Group Expenses
# -----------------------------
def add_group_expense(user_id: str, description: str, amount: float, split_type: str, members: list):
    """Add a group expense"""
    db = init_db()
    doc = {
        "user_id": user_id,
        "description": description,
        "amount": float(amount),
        "split_type": split_type,  # "equal" or "custom"
        "members": members,  # [{"email": "...", "amount": 100, "paid": False}]
        "created_at": datetime.datetime.utcnow()
    }
    try:
        db.group_expenses.insert_one(doc)
        return True
    except Exception as e:
        logging.error(f"add_group_expense error: {e}")
        return False

def list_group_expenses(user_id: str):
    """Get all group expenses for a user"""
    db = init_db()
    return list(db.group_expenses.find({"user_id": user_id}))

# -----------------------------
# Financial Goals
# -----------------------------
def add_financial_goal(user_id: str, title: str, target_amount: float, target_date, category: str):
    """Add a financial goal"""
    db = init_db()
    doc = {
        "user_id": user_id,
        "title": title,
        "target_amount": float(target_amount),
        "current_amount": 0.0,
        "target_date": target_date,
        "category": category,
        "is_achieved": False,
        "created_at": datetime.datetime.utcnow()
    }
    try:
        db.financial_goals.insert_one(doc)
        return True
    except Exception as e:
        logging.error(f"add_financial_goal error: {e}")
        return False

def list_financial_goals(user_id: str):
    """Get all financial goals for a user"""
    db = init_db()
    return list(db.financial_goals.find({"user_id": user_id}))

def update_goal_progress(goal_id: str, amount: float):
    """Update the progress of a financial goal"""
    db = init_db()
    try:
        db.financial_goals.update_one(
            {"_id": ObjectId(goal_id)},
            {"$inc": {"current_amount": float(amount)}}
        )
        return True
    except Exception as e:
        logging.error(f"update_goal_progress error: {e}")
        return False

# -----------------------------
# Debt Management
# -----------------------------
def add_debt(user_id: str, creditor_name: str, total_amount: float, interest_rate: float, minimum_payment: float, notes: str=""):
    """Add a debt record"""
    db = init_db()
    doc = {
        "user_id": user_id,
        "creditor_name": creditor_name,
        "total_amount": float(total_amount),
        "remaining_amount": float(total_amount),
        "interest_rate": float(interest_rate),
        "minimum_payment": float(minimum_payment),
        "notes": notes,
        "is_paid": False,
        "created_at": datetime.datetime.utcnow()
    }
    try:
        db.debts.insert_one(doc)
        return True
    except Exception as e:
        logging.error(f"add_debt error: {e}")
        return False

def list_debts(user_id: str):
    """Get all debts for a user"""
    db = init_db()
    return list(db.debts.find({"user_id": user_id, "is_paid": False}))

def record_debt_payment(debt_id: str, payment_amount: float):
    """Record a debt payment"""
    db = init_db()
    try:
        debt = db.debts.find_one({"_id": ObjectId(debt_id)})
        if debt:
            new_remaining = debt.get("remaining_amount", 0) - float(payment_amount)
            update_data = {
                "$inc": {"remaining_amount": -float(payment_amount)},
                "$set": {"last_payment_date": datetime.datetime.utcnow()}
            }
            
            if new_remaining <= 0:
                update_data["$set"]["is_paid"] = True
                update_data["$set"]["paid_at"] = datetime.datetime.utcnow()
            
            db.debts.update_one({"_id": ObjectId(debt_id)}, update_data)
            return True
        return False
    except Exception as e:
        logging.error(f"record_debt_payment error: {e}")
        return False
