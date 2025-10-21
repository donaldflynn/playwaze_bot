from selenium_scripts import book_session
from gmail import send_reply_to_thread, Thread
from variables import TINY_DB_PATH
from tinydb import TinyDB

def book_session_job(
    booking_time, session_id, **kwargs
):
    thread = Thread.from_dict(kwargs)
    try:
        book_session(thread.subject, booking_time)
        send_reply_to_thread("Success", thread)
    except Exception as e:
        send_reply_to_thread(f"Error: {repr(e)}", thread)