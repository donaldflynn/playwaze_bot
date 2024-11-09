import subprocess
from datetime import datetime
from gmail import get_unread_email_thread, Thread, send_reply_to_thread
from selenium_scripts import fetch_session_start_time
import time
from datetime import datetime, timedelta

def main():
    thread = get_unread_email_thread()
    if thread is not None:
        handle_email(thread)
        

def handle_email(thread: Thread):

    try:
        start_time = fetch_session_start_time(thread.subject)
        booking_time = start_time - timedelta(days=3)
        if booking_time < datetime.now():
            raise ValueError("Booking time is in the past")
        send_reply_to_thread("Success", thread)

    except ValueError as e:
        print(f"Failed to handle email: {e}")
        send_reply_to_thread(f"Failure: {e}", thread)
        pass

if __name__ == "__main__":
    while True:
        main()
        time.sleep(5)
                
