import bcrypt
from database import mongo_manager
from config import settings

class Authenticator:
    def __init__(self, secret_key=None):
        self.secret_key = secret_key or settings.SECRET_KEY

    def signup(self, name: str, email: str, password: str):
        existing = mongo_manager.get_user_by_email(email)
        if existing:
            return False, "Email already registered"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        user_id = mongo_manager.create_user(name, email, hashed)
        if user_id:
            return True, "Account created"
        return False, "Failed to create account"

    def login(self, email: str, password: str):
        user = mongo_manager.get_user_by_email(email)
        if not user:
            return False, None, None, "User not found"
        phash = user.get("password_hash")
        if isinstance(phash, str):
            phash = phash.encode()
        if bcrypt.checkpw(password.encode(), phash):
            # create a simple token (not JWT for simplicity)
            token = f"token-{user.get('_id')}"
            # return ok, user dict, token, message
            user_out = {
                "id": str(user.get("_id")),
                "name": user.get("name"),
                "email": user.get("email"),
                "_id": str(user.get("_id"))
            }
            return True, user_out, token, "Logged in"
        return False, None, None, "Invalid password"
