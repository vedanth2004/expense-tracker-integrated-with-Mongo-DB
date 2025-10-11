from database import mongo_manager
from email_validator import validate_email, EmailNotValidError

class SharedAccounts:
    def invite(self, owner_id: str, member_email: str):
        try:
            validate_email(member_email)
        except EmailNotValidError as e:
            return False, str(e)
        ok = mongo_manager.invite_share(owner_id, member_email)
        return True, "Invitation recorded" if ok else (False, "Failed to record invite")

    def list_shared(self, owner_id: str):
        rows = mongo_manager.list_shares(owner_id)
        import pandas as pd
        return pd.DataFrame(rows) if rows else None
