from selenium_scripts import book_session, get_sessions_list
from gmail import send_reply_to_thread, Thread
from variables import TINY_DB_PATH
from tinydb import TinyDB

def book_session_job(
    thread_dict: dict
):
    thread = Thread.from_dict(thread_dict)
    try:
        book_session(thread.subject)
        send_reply_to_thread("Success", thread)
    except Exception as e:
        send_reply_to_thread(f"Error: {repr(e)}", thread)

def check_for_new_sessions_job():
    db = TinyDB(TINY_DB_PATH)
    sessions_table = db.table('sessions')
    sessions_db_list = sessions_table.all()[0]['recent'] if len(sessions_table.all()) > 0 else []
    try:
        sessions = get_sessions_list()
        if len(sessions) != 0:
            if any(item not in sessions_db_list for item in sessions):
                print(f"New session Found: {sessions}")
                sessions_table.truncate()
                sessions_table.insert({'recent': sessions})
            else:
                print("No new sessions found")
    except:
        pass