from database import mongo_manager
from email_validator import validate_email, EmailNotValidError

class SharedAccounts:
    def invite(self, owner_id: str, member_email: str):
        try:
            validate_email(member_email)
        except EmailNotValidError as e:
            return False, str(e)
        
        # Check if user exists
        member_user = mongo_manager.get_user_by_email(member_email)
        if not member_user:
            return False, f"❌ No user found with email: {member_email}"
        
        # Check if already shared
        existing_shares = mongo_manager.list_shares(owner_id)
        for share in existing_shares:
            if share.get("member_email") == member_email:
                return False, f"❌ User {member_email} is already in your shared accounts"
        
        ok = mongo_manager.invite_share(owner_id, member_email)
        return True, f"✅ Successfully added {member_email} to shared accounts!" if ok else (False, "Failed to record invite")

    def list_shared(self, owner_id: str):
        rows = mongo_manager.list_shares(owner_id)
        import pandas as pd
        return pd.DataFrame(rows) if rows else None
    
    def get_shared_accounts_for_user(self, user_email: str):
        """Get all accounts that are shared with this user"""
        return mongo_manager.get_accounts_shared_with_user(user_email)
    
    def get_owner_accounts(self, owner_id: str):
        """Get shared account details for a user"""
        rows = mongo_manager.list_shares(owner_id)
        return rows
    
    def remove_shared_user(self, owner_id: str, member_email: str):
        """Remove a user from shared accounts"""
        return mongo_manager.remove_share(owner_id, member_email)
