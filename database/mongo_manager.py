# database/mongo_manager.py
import datetime
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
import streamlit as st
from config.settings import settings
from bson.objectid import ObjectId

# -----------------------------
# Cached MongoDB client
# -----------------------------
@st.cache_resource
def get_client():
    mongo_uri = settings.MONGO_URI
    if not mongo_uri:
        raise RuntimeError(
            "MongoDB URI not set. Put it in .streamlit/secrets.toml as 'MONGO_URI' or set MONGO_URI env var."
        )
    return MongoClient(mongo_uri, tls=True, serverSelectionTimeoutMS=10000)

# Use a single client and db for all operations
client = get_client()
db = client["expense_tracker"]

# -----------------------------
# Create indexes once at startup
# -----------------------------
def init_indexes():
    try:
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.expenses.create_index([("user_id", ASCENDING), ("date", DESCENDING)])
        db.income.create_index([("user_id", ASCENDING), ("date", DESCENDING)])
        db.budgets.create_index([("user_id", ASCENDING), ("category", ASCENDING)], unique=True)
        db.shares.create_index([("owner_id", ASCENDING), ("member_email", ASCENDING)], unique=True)
    except Exception as e:
        logging.warning(f"Index creation error: {e}")

init_indexes()

# -----------------------------
# Users
# -----------------------------
def create_user(name: str, email: str, password_hash: bytes):
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
    return db.users.find_one({"email": email})

def get_user_by_id(user_id: str):
    return db.users.find_one({"_id": ObjectId(user_id)})

def get_user(user_id: str):
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return None
    user["_id"] = str(user["_id"])
    return user

# -----------------------------
# Expenses
# -----------------------------
def add_expense(user_id: str, amount: float, category: str, note: str="", date=None, currency: str="USD", receipt_text: str=""):
    uid = str(user_id)
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
        "created_at": datetime.datetime.utcnow()
    }
    try:
        db.expenses.insert_one(doc)
        return True
    except Exception as e:
        logging.error(f"add_expense error: {e}")
        return False

def list_expenses(user_id: str, limit: int=200):
    uid = str(user_id)
    cursor = db.expenses.find({"user_id": uid}).sort("date", DESCENDING).limit(limit)
    rows = []
    for r in cursor:
        r["id"] = str(r["_id"])
        r["date"] = r.get("date").isoformat() if r.get("date") else ""
        rows.append(r)
    return rows

def delete_expense(expense_id: str, user_id: str) -> bool:
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
    uid = str(user_id)
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
    uid = str(user_id)
    db.budgets.update_one(
        {"user_id": uid, "category": category},
        {"$set": {"monthly_limit": float(monthly_limit), "updated_at": datetime.datetime.utcnow()}},
        upsert=True
    )
    return True

def list_budgets(user_id: str):
    uid = str(user_id)
    return list(db.budgets.find({"user_id": uid}))

# -----------------------------
# Shared Accounts
# -----------------------------
def invite_share(owner_id: str, member_email: str):
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
    uid = str(owner_id)
    cursor = db.shares.find({"owner_id": uid})
    out = []
    for r in cursor:
        out.append({
            "member_email": r.get("member_email"),
            "created_at": r.get("created_at").isoformat() if r.get("created_at") else ""
        })
    return out

# -----------------------------
# Gemini API
# -----------------------------
def save_gemini_api_key(user_id, api_key):
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"gemini_api_key": api_key}})

def get_gemini_api_key(user_id):
    user = db.users.find_one({"_id": ObjectId(user_id)}, {"gemini_api_key": 1})
    return user.get("gemini_api_key") if user else None

# -----------------------------
# Expense summary
# -----------------------------
def get_expense_summary(user_id: str):
    uid = str(user_id)
    pipeline = [
        {"$match": {"user_id": uid}},
        {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}},
        {"$sort": {"total": -1}}
    ]
    return list(db.expenses.aggregate(pipeline))
