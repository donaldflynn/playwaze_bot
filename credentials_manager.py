import re
from data.credentials import accounts
from tinydb import Query

class CredentialsManager:
    def __init__(self, creds_table):
        self.creds_table = creds_table

    def perform_potential_password_update(self, email_address: str, body: str):
        if "password" in body.lower():
            match = re.search(r'["\'](.*?)["\']', body) # Extract text inside quotation marks (single or double)
            new_password = match.group(1) if match else None
        if new_password is not None:
            CredsData = Query()
            self.creds_table.remove(CredsData.email == email_address)
            self.creds_table.insert({"email": email_address, "password": new_password})
            return True
        return False
    
    def get_credentials_from_email(self, email) -> tuple[str, str]:
        # First check if account is hardcoded in:
        for account in accounts:
            if email in account['allowed_emails']:
                return account['username'], account['password']
        # Secondly check if account is stored in database:
        CredsData = Query()
        matches = self.jobs_table.search(CredsData.email == email)
        if len(matches >= 1):
            return email, matches[0]['password']
        else:
            raise ValueError('No Password for this account found. To register a password send an email with - password:"[my_password_here]" - in the body. Send the email from the address registered to your playwaze account.')
        
    def get_priority_from_email(email):
        for account in accounts:
            if email in account['allowed_emails']:
                return 10
        return 1
    