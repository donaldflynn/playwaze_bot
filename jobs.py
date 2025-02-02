from selenium_scripts import book_session
from gmail import send_reply_to_thread, Thread
from variables import TINY_DB_PATH
from tinydb import TinyDB
from credentials_manager import CredentialsManager

def book_session_job(
    thread_dict: dict
):
    credentials_manager = CredentialsManager(TinyDB(TINY_DB_PATH).table('creds'))
    thread = Thread.from_dict(thread_dict)
    try:
        username, password = credentials_manager.get_credentials_from_email(thread.external_address)
        book_session(thread.subject, username, password)
        send_reply_to_thread("Success", thread)
    except Exception as e:
        send_reply_to_thread(f"Error: {repr(e)}", thread)